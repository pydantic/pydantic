use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use super::{TypeValidator, Validator};
use crate::utils::{dict_get, py_error};

#[derive(Debug, Clone)]
pub struct ListValidator {
    min_items: Option<usize>,
    max_items: Option<usize>,
    item_validator: Option<Box<Validator>>,
}

impl TypeValidator for ListValidator {
    fn is_match(type_: &str, _dict: &PyDict) -> bool {
        type_ == "list"
    }

    fn build(dict: &PyDict) -> PyResult<Self> {
        Ok(Self {
            item_validator: match dict_get!(dict, "items", &PyDict) {
                Some(items_dict) => Some(Box::new(Validator::build(items_dict)?)),
                None => None,
            },
            min_items: dict_get!(dict, "min_items", usize),
            max_items: dict_get!(dict, "max_items", usize),
        })
    }

    fn validate(&self, py: Python, obj: PyObject) -> PyResult<PyObject> {
        let list: &PyList = obj.extract(py)?;
        if let Some(min_length) = self.min_items {
            if list.len() < min_length {
                return py_error!("list must have at least {} items", min_length);
            }
        }
        if let Some(max_length) = self.max_items {
            if list.len() > max_length {
                return py_error!("list must have at most {} items", max_length);
            }
        }
        let mut output: Vec<PyObject> = Vec::with_capacity(list.len());
        let mut errors = Vec::new();
        for item in list.iter() {
            match self.item_validator {
                Some(ref validator) => match validator.validate(py, item.to_object(py)) {
                    Ok(item) => output.push(item),
                    Err(err) => errors.push(err),
                },
                None => output.push(item.to_object(py)),
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
