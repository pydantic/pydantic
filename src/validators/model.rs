use pyo3::prelude::*;
use pyo3::types::{PyDict, PySet};
use std::collections::HashSet;

use super::{build_validator, Extra, Validator};
use crate::errors::{as_internal, err_val_error, val_line_error, ErrorKind, ValError, ValLineError, ValResult};
use crate::input::{Input, ToLocItem};
use crate::utils::{dict_get, py_error};

#[derive(Debug, Clone)]
struct ModelField {
    name: String,
    // alias: Option<String>,
    default: Option<PyObject>,
    validator: Box<dyn Validator>,
}

#[derive(Debug, Clone)]
pub struct ModelValidator {
    fields: Vec<ModelField>,
    extra_behavior: ExtraBehavior,
    extra_validator: Option<Box<dyn Validator>>,
}

impl ModelValidator {
    pub const EXPECTED_TYPE: &'static str = "model";
}

impl Validator for ModelValidator {
    fn build(schema: &PyDict, _config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        // models ignore the parent config and always use the config from this model
        let config = dict_get!(schema, "config", &PyDict);

        let extra_behavior = ExtraBehavior::from_config(config)?;
        let extra_validator = match extra_behavior {
            ExtraBehavior::Allow => match dict_get!(schema, "extra_validator", &PyDict) {
                Some(v) => Some(build_validator(v, config)?),
                None => None,
            },
            _ => None,
        };

        let fields_dict: &PyDict = match dict_get!(schema, "fields", &PyDict) {
            Some(fields) => fields,
            None => {
                // allow an empty model, is this is a good idea?
                return Ok(Box::new(Self {
                    fields: vec![],
                    extra_behavior,
                    extra_validator,
                }));
            }
        };
        let mut fields: Vec<ModelField> = Vec::with_capacity(fields_dict.len());

        for (key, value) in fields_dict.iter() {
            let field_dict: &PyDict = value.cast_as()?;

            fields.push(ModelField {
                name: key.to_string(),
                // alias: dict_get!(field_dict, "alias", String),
                validator: build_validator(field_dict, config)?,
                default: dict_get!(field_dict, "default", PyAny),
            });
        }
        Ok(Box::new(Self {
            fields,
            extra_behavior,
            extra_validator,
        }))
    }

    fn validate(&self, py: Python, input: &dyn Input, extra: &Extra) -> ValResult<PyObject> {
        if let Some(field) = extra.field {
            // we're validating assignment, completely different logic
            return self.validate_assignment(py, field, input, extra);
        }

        let dict = input.validate_dict(py)?;
        let output_dict = PyDict::new(py);
        let mut errors: Vec<ValLineError> = Vec::new();
        let mut fields_set: HashSet<String> = HashSet::with_capacity(dict.input_len());

        let extra = Extra {
            data: Some(output_dict),
            field: None,
        };

        for field in &self.fields {
            if let Some(value) = dict.input_get(&field.name) {
                match field.validator.validate(py, value, &extra) {
                    Ok(value) => output_dict.set_item(&field.name, value).map_err(as_internal)?,
                    Err(ValError::LineErrors(line_errors)) => {
                        let loc = vec![field.name.to_loc()?];
                        for err in line_errors {
                            errors.push(err.prefix_location(&loc));
                        }
                    }
                    Err(err) => return Err(err),
                }
                fields_set.insert(field.name.clone());
            } else if let Some(ref default) = field.default {
                output_dict
                    .set_item(&field.name, default.clone())
                    .map_err(as_internal)?;
            } else {
                errors.push(val_line_error!(
                    py,
                    dict,
                    kind = ErrorKind::Missing,
                    location = vec![field.name.to_loc()?]
                ));
            }
        }

        let (check_extra, forbid) = match self.extra_behavior {
            ExtraBehavior::Ignore => (false, false),
            ExtraBehavior::Allow => (true, false),
            ExtraBehavior::Forbid => (true, true),
        };
        if check_extra {
            for (raw_key, value) in dict.input_iter() {
                let key: String = match raw_key.validate_str(py) {
                    Ok(k) => k,
                    Err(ValError::LineErrors(line_errors)) => {
                        let loc = vec![raw_key.to_loc()?];
                        for err in line_errors {
                            errors.push(err.prefix_location(&loc));
                        }
                        continue;
                    }
                    Err(err) => return Err(err),
                };
                if fields_set.contains(&key) {
                    continue;
                }
                fields_set.insert(key.clone());
                let loc = vec![key.to_loc()?];

                if forbid {
                    errors.push(val_line_error!(
                        py,
                        dict,
                        kind = ErrorKind::ExtraForbidden,
                        location = loc
                    ));
                } else if let Some(ref validator) = self.extra_validator {
                    match validator.validate(py, value, &extra) {
                        Ok(value) => output_dict.set_item(&key, value).map_err(as_internal)?,
                        Err(ValError::LineErrors(line_errors)) => {
                            for err in line_errors {
                                errors.push(err.prefix_location(&loc));
                            }
                        }
                        Err(err) => return Err(err),
                    }
                } else {
                    output_dict.set_item(&key, value.to_py(py)).map_err(as_internal)?;
                }
            }
        }

        if errors.is_empty() {
            Ok((output_dict, fields_set).to_object(py))
        } else {
            Err(ValError::LineErrors(errors))
        }
    }

    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}

impl ModelValidator {
    fn validate_assignment(&self, py: Python, field: &str, input: &dyn Input, extra: &Extra) -> ValResult<PyObject> {
        // TODO probably we should set location on errors here
        let field_name = field.to_string();

        let data = match extra.data {
            Some(data) => data,
            None => panic!("data is required when validating assignment"),
        };

        let prepare_tuple = |output: PyObject| {
            data.set_item(field_name.clone(), output).map_err(as_internal)?;
            let fields_set = PySet::new(py, &vec![field_name.clone()][..]).map_err(as_internal)?;
            Ok((data, fields_set).to_object(py))
        };

        let prepare_result = |result: ValResult<PyObject>| match result {
            Ok(output) => prepare_tuple(output),
            Err(ValError::LineErrors(line_errors)) => {
                let loc = vec![field_name.to_loc()?];
                let errors = line_errors.iter().map(|e| e.prefix_location(&loc)).collect();
                Err(ValError::LineErrors(errors))
            }
            Err(err) => Err(err),
        };

        if let Some(field) = self.fields.iter().find(|f| f.name == field_name) {
            prepare_result(field.validator.validate(py, input, extra))
        } else {
            match self.extra_behavior {
                // with allow we either want to set the value
                ExtraBehavior::Allow => match self.extra_validator {
                    Some(ref validator) => prepare_result(validator.validate(py, input, extra)),
                    None => prepare_tuple(input.to_py(py)),
                },
                // otherwise we raise an error:
                // - with forbid this is obvious
                // - with ignore the model should never be overloaded, so an error is the clearest option
                _ => {
                    let loc = vec![field_name.to_loc()?];
                    err_val_error!(py, input, location = loc, kind = ErrorKind::ExtraForbidden)
                }
            }
        }
    }
}

#[derive(Debug, Clone)]
enum ExtraBehavior {
    Allow,
    Ignore,
    Forbid,
}

impl ExtraBehavior {
    pub fn from_config(config: Option<&PyDict>) -> PyResult<Self> {
        match config {
            Some(dict) => {
                let b = dict_get!(dict, "extra", String);
                match b {
                    Some(s) => match s.as_str() {
                        "allow" => Ok(ExtraBehavior::Allow),
                        "ignore" => Ok(ExtraBehavior::Ignore),
                        "forbid" => Ok(ExtraBehavior::Forbid),
                        _ => py_error!(r#"Invalid extra_behavior: "{}""#, s),
                    },
                    None => Ok(ExtraBehavior::Ignore),
                }
            }
            None => Ok(ExtraBehavior::Ignore),
        }
    }
}
