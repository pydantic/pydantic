use pyo3::prelude::*;
use pyo3::types::PyDict;

use super::{TypeValidator, Validator};
use crate::utils::{dict_get, py_error};

#[derive(Debug, Clone)]
pub struct DictValidator {
    key_validator: Option<Box<Validator>>,
    value_validator: Option<Box<Validator>>,
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
                Some(d) => Some(Box::new(Validator::build(d)?)),
                None => None,
            },
            value_validator: match dict_get!(dict, "values", &PyDict) {
                Some(d) => Some(Box::new(Validator::build(d)?)),
                None => None,
            },
            min_items: dict_get!(dict, "min_items", usize),
            max_items: dict_get!(dict, "max_items", usize),
        })
    }

    fn validate(&self, py: Python, obj: PyObject) -> PyResult<PyObject> {
        let dict: &PyDict = obj.extract(py)?;
        if let Some(min_length) = self.min_items {
            if dict.len() < min_length {
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
            let output_key: Option<PyObject> = match self.key_validator {
                Some(ref validator) => match validator.validate(py, key.to_object(py)) {
                    Ok(key) => Some(key),
                    Err(err) => {
                        errors.push(err);
                        None
                    },
                },
                None => Some(key.to_object(py)),
            };
            let output_value: Option<PyObject> = match self.value_validator {
                Some(ref validator) => match validator.validate(py, value.to_object(py)) {
                    Ok(value) => Some(value),
                    Err(err) => {
                        errors.push(err);
                        None
                    },
                },
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
