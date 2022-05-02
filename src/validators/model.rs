use pyo3::prelude::*;
use pyo3::types::{PyDict, PySet};

use crate::build_tools::{py_error, SchemaDict};
use crate::errors::{
    as_internal, err_val_error, val_line_error, ErrorKind, InputValue, ValError, ValLineError, ValResult,
};
use crate::input::{Input, ToLocItem};

use super::{build_validator, Extra, Validator, ValidatorArc};

#[derive(Debug, Clone)]
struct ModelField {
    name: String,
    // alias: Option<String>,
    default: Option<PyObject>,
    validator: Box<dyn Validator>,
}

#[derive(Debug, Clone)]
pub struct ModelValidator {
    name: String,
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
        let config: Option<&PyDict> = schema.get_as("config")?;

        let extra_behavior = ExtraBehavior::from_config(config)?;
        let extra_validator = match extra_behavior {
            ExtraBehavior::Allow => match schema.get_item("extra_validator") {
                Some(v) => Some(build_validator(v, config)?.0),
                None => None,
            },
            _ => None,
        };

        let name: String = schema.get_as("name")?.unwrap_or_else(|| "Model".to_string());
        let fields_dict: &PyDict = match schema.get_as("fields")? {
            Some(fields) => fields,
            None => {
                // allow an empty model, is this is a good idea?
                return Ok(Box::new(Self {
                    name,
                    fields: vec![],
                    extra_behavior,
                    extra_validator,
                }));
            }
        };
        let mut fields: Vec<ModelField> = Vec::with_capacity(fields_dict.len());

        for (key, value) in fields_dict.iter() {
            let (validator, field_dict) = match build_validator(value, config) {
                Ok(v) => v,
                Err(err) => return py_error!("Key \"{}\":\n  {}", key, err),
            };

            fields.push(ModelField {
                name: key.to_string(),
                // alias: field_dict.get_as("alias"),
                validator,
                default: field_dict.get_as("default")?,
            });
        }
        Ok(Box::new(Self {
            name,
            fields,
            extra_behavior,
            extra_validator,
        }))
    }

    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        if let Some(field) = extra.field {
            // we're validating assignment, completely different logic
            return self.validate_assignment(py, field, input, extra);
        }

        // TODO we shouldn't always use try_instance=true here
        let dict = input.lax_dict(true)?;
        let output_dict = PyDict::new(py);
        let mut errors: Vec<ValLineError> = Vec::new();
        let fields_set = PySet::empty(py).map_err(as_internal)?;

        let extra = Extra {
            data: Some(output_dict),
            field: None,
        };

        for field in &self.fields {
            if let Some(value) = dict.input_get(&field.name) {
                match field.validator.validate(py, value, &extra) {
                    Ok(value) => output_dict.set_item(&field.name, value).map_err(as_internal)?,
                    Err(ValError::LineErrors(line_errors)) => {
                        let loc = vec![field.name.to_loc()];
                        for err in line_errors {
                            errors.push(err.with_prefix_location(&loc));
                        }
                    }
                    Err(err) => return Err(err),
                }
                fields_set.add(field.name.clone()).map_err(as_internal)?;
            } else if let Some(ref default) = field.default {
                output_dict
                    .set_item(&field.name, default.clone())
                    .map_err(as_internal)?;
            } else {
                errors.push(val_line_error!(
                    input_value = InputValue::InputRef(input),
                    kind = ErrorKind::Missing,
                    location = vec![field.name.to_loc()]
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
                let key: String = match raw_key.lax_str() {
                    Ok(k) => k,
                    Err(ValError::LineErrors(line_errors)) => {
                        let loc = vec![raw_key.to_loc()];
                        for err in line_errors {
                            errors.push(err.with_prefix_location(&loc));
                        }
                        continue;
                    }
                    Err(err) => return Err(err),
                };
                if fields_set.contains(&key).map_err(as_internal)? {
                    continue;
                }
                fields_set.add(key.clone()).map_err(as_internal)?;
                let loc = vec![key.to_loc()];

                if forbid {
                    errors.push(val_line_error!(
                        input_value = InputValue::InputRef(input),
                        kind = ErrorKind::ExtraForbidden,
                        location = loc
                    ));
                } else if let Some(ref validator) = self.extra_validator {
                    match validator.validate(py, value, &extra) {
                        Ok(value) => output_dict.set_item(&key, value).map_err(as_internal)?,
                        Err(ValError::LineErrors(line_errors)) => {
                            for err in line_errors {
                                errors.push(err.with_prefix_location(&loc));
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

    fn set_ref(&mut self, name: &str, validator_arc: &ValidatorArc) -> PyResult<()> {
        if let Some(ref mut extra_validator) = self.extra_validator {
            extra_validator.set_ref(name, validator_arc)?;
        }
        for field in self.fields.iter_mut() {
            field.validator.set_ref(name, validator_arc)?;
        }
        Ok(())
    }

    fn get_name(&self, _py: Python) -> String {
        self.name.clone()
    }

    #[no_coverage]
    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}

impl ModelValidator {
    fn validate_assignment<'s, 'data>(
        &'s self,
        py: Python<'data>,
        field: &str,
        input: &'data dyn Input,
        extra: &Extra,
    ) -> ValResult<'data, PyObject>
    where
        'data: 's,
    {
        // TODO probably we should set location on errors here
        let data = match extra.data {
            Some(data) => data,
            None => panic!("data is required when validating assignment"),
        };

        let prepare_tuple = |output: PyObject| {
            data.set_item(field, output).map_err(as_internal)?;
            let fields_set = PySet::new(py, &[field]).map_err(as_internal)?;
            Ok((data, fields_set).to_object(py))
        };

        let prepare_result = |result: ValResult<'data, PyObject>| match result {
            Ok(output) => prepare_tuple(output),
            Err(ValError::LineErrors(line_errors)) => {
                let loc = vec![field.to_loc()];
                let errors = line_errors.into_iter().map(|e| e.with_prefix_location(&loc)).collect();
                Err(ValError::LineErrors(errors))
            }
            Err(err) => Err(err),
        };

        if let Some(field) = self.fields.iter().find(|f| f.name == field) {
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
                    let loc = vec![field.to_loc()];
                    err_val_error!(
                        input_value = InputValue::InputRef(input),
                        location = loc,
                        kind = ErrorKind::ExtraForbidden
                    )
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
                let b: Option<String> = dict.get_as("extra")?;
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
