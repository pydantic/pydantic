use pyo3::prelude::*;
use pyo3::types::{IntoPyDict, PyDict};

use super::{SchemaValidator, TypeValidator};
use crate::errors::{ErrorKind, LocItem, Location, ValLineError, ValResult, ValidationError};
use crate::utils::{dict_get, py_error};

#[derive(Debug, Clone)]
pub struct DictValidator {
    key_validator: Option<Box<SchemaValidator>>,
    value_validator: Option<Box<SchemaValidator>>,
    min_items: Option<usize>,
    max_items: Option<usize>,
}

impl TypeValidator for DictValidator {
    fn is_match(type_: &str, _dict: &PyDict) -> bool {
        type_ == "dict"
    }

    fn build(dict: &PyDict) -> PyResult<Self> {
        Ok(Self {
            key_validator: match dict_get!(dict, "keys", &PyDict) {
                Some(d) => Some(Box::new(SchemaValidator::build(d)?)),
                None => None,
            },
            value_validator: match dict_get!(dict, "values", &PyDict) {
                Some(d) => Some(Box::new(SchemaValidator::build(d)?)),
                None => None,
            },
            min_items: dict_get!(dict, "min_items", usize),
            max_items: dict_get!(dict, "max_items", usize),
        })
    }

    fn validate(&self, py: Python, obj: &PyAny, loc: &Location) -> PyResult<ValResult> {
        let dict: &PyDict = obj.cast_as()?;
        if let Some(min_length) = self.min_items {
            if dict.len() < min_length {
                return Ok(Err(ValidationError::single(ValLineError {
                    kind: ErrorKind::DictTooShort,
                    value: Some(dict.to_object(py)),
                    context: Some([("min_length", min_length)].into_py_dict(py).to_object(py)),
                    ..Default::default()
                })));
                return py_error!("dict must have at least {} items", min_length);
            }
        }
        if let Some(max_length) = self.max_items {
            if dict.len() > max_length {
                return py_error!("dict must have at most {} items", max_length);
            }
        }
        let output = PyDict::new(py);
        let mut errors = Vec::new();

        for (key, value) in dict.iter() {
            let get_key_loc = || -> PyResult<LocItem> {
                if let Ok(key_str) = key.extract::<String>() {
                    return Ok(LocItem::Key(key_str));
                }
                if let Ok(key_int) = key.extract::<usize>() {
                    return Ok(LocItem::Index(key_int));
                }
                // best effort is to use repr
                let repr: String = key.repr()?.extract()?;
                Ok(LocItem::Key(repr))
            };
            // just call this for now, should be lazy in future
            let key_loc = get_key_loc()?;

            let output_key: Option<PyObject> = match self.key_validator {
                Some(ref validator) => {
                    let mut field_loc = loc.clone();
                    field_loc.push(key_loc.clone());
                    field_loc.push(LocItem::Key("[key]".to_string()));

                    match validator.validate(py, key, &field_loc) {
                        Ok(key) => Some(key),
                        Err(err) => {
                            errors.push(err);
                            None
                        }
                    }
                }
                None => Some(key.to_object(py)),
            };
            let output_value: Option<PyObject> = match self.value_validator {
                Some(ref validator) => {
                    let mut field_loc = loc.clone();
                    field_loc.push(key_loc);
                    match validator.validate(py, value, &field_loc) {
                        Ok(value) => Some(value),
                        Err(err) => {
                            errors.push(err);
                            None
                        }
                    }
                }
                None => Some(value.to_object(py)),
            };
            if let (Some(key), Some(value)) = (output_key, output_value) {
                output.set_item(key, value)?;
            }
        }

        if errors.is_empty() {
            Ok(output.to_object(py))
        } else {
            py_error!("errors: {:?}", errors)
        }
    }

    fn clone_dyn(&self) -> Box<dyn TypeValidator> {
        Box::new(self.clone())
    }
}
