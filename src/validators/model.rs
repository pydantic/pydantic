use pyo3::prelude::*;
use pyo3::types::PyDict;

use super::{build_validator, Validator};
use crate::errors::{as_internal, val_error, ErrorKind, LocItem, ValError, ValLineError, ValResult};
use crate::standalone_validators::validate_dict;
use crate::utils::dict_get;

#[derive(Debug, Clone)]
struct ModelField {
    name: String,
    // alias: Option<String>,
    required: bool,
    validator: Box<dyn Validator>,
}

#[derive(Debug, Clone)]
pub struct ModelValidator {
    fields: Vec<ModelField>,
}

impl Validator for ModelValidator {
    fn is_match(type_: &str, _dict: &PyDict) -> bool {
        type_ == "model"
    }

    fn build(dict: &PyDict) -> PyResult<Self> {
        let fields_dict: &PyDict = match dict_get!(dict, "fields", &PyDict) {
            Some(fields) => fields,
            None => {
                // allow an empty model, is this is a good idea?
                return Ok(Self { fields: vec![] });
            }
        };
        let mut fields: Vec<ModelField> = Vec::with_capacity(fields_dict.len());

        for (key, value) in fields_dict.iter() {
            let field_dict: &PyDict = value.cast_as()?;

            fields.push(ModelField {
                name: key.to_string(),
                // alias: dict_get!(field_dict, "alias", String),
                required: dict_get!(field_dict, "required", bool).unwrap_or(false),
                validator: build_validator(field_dict)?,
            });
        }
        Ok(Self { fields })
    }

    fn validate(&self, py: Python, input: &PyAny) -> ValResult<PyObject> {
        let dict: &PyDict = validate_dict(py, input)?;
        let output = PyDict::new(py);
        let mut errors: Vec<ValLineError> = Vec::new();

        for field in &self.fields {
            if let Some(value) = dict.get_item(field.name.clone()) {
                match field.validator.validate(py, value) {
                    Ok(value) => output.set_item(field.name.clone(), value).map_err(as_internal)?,
                    Err(ValError::LineErrors(line_errors)) => {
                        let loc = vec![LocItem::S(field.name.clone())];
                        for err in line_errors {
                            errors.push(err.with_location(&loc));
                        }
                    }
                    Err(err) => return Err(err),
                }
            } else if field.required {
                errors.push(val_error!(
                    py,
                    dict,
                    kind = ErrorKind::Missing,
                    location = vec![LocItem::S(field.name.clone())]
                ));
            }
        }

        if errors.is_empty() {
            Ok(output.into())
        } else {
            println!("model got errors: {:?}", errors);
            Err(ValError::LineErrors(errors))
        }
    }

    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}
