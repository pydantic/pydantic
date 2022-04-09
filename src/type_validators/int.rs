use pyo3::prelude::*;
use pyo3::types::PyDict;

use super::TypeValidator;
use crate::errors::Location;
use crate::utils::{dict_get, py_error};

#[derive(Debug, Clone)]
pub struct SimpleIntValidator;

impl TypeValidator for SimpleIntValidator {
    fn is_match(type_: &str, dict: &PyDict) -> bool {
        type_ == "int"
            && dict.get_item("multiple_of").is_none()
            && dict.get_item("le").is_none()
            && dict.get_item("lt").is_none()
            && dict.get_item("ge").is_none()
            && dict.get_item("gt").is_none()
    }

    fn build(_dict: &PyDict) -> PyResult<Self> {
        Ok(Self)
    }

    fn validate(&self, py: Python, obj: &PyAny, _loc: &Location) -> PyResult<PyObject> {
        Ok(i64::extract(obj)?.to_object(py))
    }

    fn clone_dyn(&self) -> Box<dyn TypeValidator> {
        Box::new(self.clone())
    }
}

#[derive(Debug, Clone)]
pub struct FullIntValidator {
    multiple_of: Option<i64>,
    le: Option<i64>,
    lt: Option<i64>,
    ge: Option<i64>,
    gt: Option<i64>,
}

impl TypeValidator for FullIntValidator {
    fn is_match(type_: &str, _dict: &PyDict) -> bool {
        type_ == "int"
    }

    fn build(dict: &PyDict) -> PyResult<Self> {
        Ok(Self {
            multiple_of: dict_get!(dict, "multiple_of", i64),
            le: dict_get!(dict, "le", i64),
            lt: dict_get!(dict, "lt", i64),
            ge: dict_get!(dict, "ge", i64),
            gt: dict_get!(dict, "gt", i64),
        })
    }

    fn validate(&self, py: Python, obj: &PyAny, _loc: &Location) -> PyResult<PyObject> {
        let value: i64 = obj.extract()?;
        if let Some(multiple_of) = self.multiple_of {
            if value % multiple_of != 0 {
                return py_error!("Value is not multiple of the specified value");
            }
        }
        if let Some(le) = self.le {
            if value > le {
                return py_error!("Value is greater than the specified value");
            }
        }
        if let Some(lt) = self.lt {
            if value >= lt {
                return py_error!("Value is greater than or equal to the specified value");
            }
        }
        if let Some(ge) = self.ge {
            if value < ge {
                return py_error!("Value is less than the specified value");
            }
        }
        if let Some(gt) = self.gt {
            if value <= gt {
                return py_error!("Value is less than or equal to the specified value");
            }
        }
        Ok(value.to_object(py))
    }

    fn clone_dyn(&self) -> Box<dyn TypeValidator> {
        Box::new(self.clone())
    }
}
