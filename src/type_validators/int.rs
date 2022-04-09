use pyo3::prelude::*;
use pyo3::types::PyDict;

use super::TypeValidator;
use crate::utils::{dict_get, py_error};

#[derive(Debug, Clone)]
pub struct SimpleIntValidator;

impl TypeValidator for SimpleIntValidator {
    fn is_match(type_: &str, dict: &PyDict) -> bool {
        type_ == "int"
            && dict.get_item("multiple_of").is_none()
            && dict.get_item("maximum").is_none()
            && dict.get_item("exclusive_maximum").is_none()
            && dict.get_item("minimum").is_none()
            && dict.get_item("exclusive_minimum").is_none()
    }

    fn build(_dict: &PyDict) -> PyResult<Self> {
        Ok(Self)
    }

    fn validate(&self, py: Python, obj: PyObject) -> PyResult<PyObject> {
        let obj = obj.extract(py)?;
        Ok(i64::extract(obj)?.to_object(py))
    }

    fn clone_dyn(&self) -> Box<dyn TypeValidator> {
        Box::new(self.clone())
    }
}

#[derive(Debug, Clone)]
pub struct FullIntValidator {
    multiple_of: Option<i64>,
    maximum: Option<i64>,
    exclusive_maximum: Option<i64>,
    minimum: Option<i64>,
    exclusive_minimum: Option<i64>,
}

impl TypeValidator for FullIntValidator {
    fn is_match(type_: &str, _dict: &PyDict) -> bool {
        type_ == "int"
    }

    fn build(dict: &PyDict) -> PyResult<Self> {
        Ok(Self {
            multiple_of: dict_get!(dict, "multiple_of", i64),
            maximum: dict_get!(dict, "maximum", i64),
            exclusive_maximum: dict_get!(dict, "exclusive_maximum", i64),
            minimum: dict_get!(dict, "minimum", i64),
            exclusive_minimum: dict_get!(dict, "exclusive_minimum", i64),
        })
    }

    fn validate(&self, py: Python, obj: PyObject) -> PyResult<PyObject> {
        let value: i64 = obj.extract(py)?;
        if let Some(multiple_of) = self.multiple_of {
            if value % multiple_of != 0 {
                return py_error!("Value is not multiple of the specified value");
            }
        }
        if let Some(maximum) = self.maximum {
            if value > maximum {
                return py_error!("Value is greater than the specified value");
            }
        }
        if let Some(exclusive_maximum) = self.exclusive_maximum {
            if value >= exclusive_maximum {
                return py_error!("Value is greater than or equal to the specified value");
            }
        }
        if let Some(minimum) = self.minimum {
            if value < minimum {
                return py_error!("Value is less than the specified value");
            }
        }
        if let Some(exclusive_minimum) = self.exclusive_minimum {
            if value <= exclusive_minimum {
                return py_error!("Value is less than or equal to the specified value");
            }
        }
        Ok(value.to_object(py))
    }

    fn clone_dyn(&self) -> Box<dyn TypeValidator> {
        Box::new(self.clone())
    }
}
