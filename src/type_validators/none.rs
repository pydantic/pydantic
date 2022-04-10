use pyo3::prelude::*;
use pyo3::types::PyDict;

use super::TypeValidator;
use crate::errors::{single_val_error, ErrorKind, Location, ValResult};

#[derive(Debug, Clone)]
pub struct NoneValidator;

impl TypeValidator for NoneValidator {
    fn is_match(type_: &str, _dict: &PyDict) -> bool {
        type_ == "null"
    }

    fn build(_dict: &PyDict) -> PyResult<Self> {
        Ok(Self)
    }

    fn validate(&self, py: Python, obj: &PyAny, _loc: &Location) -> ValResult<PyObject> {
        if obj.is_none() {
            ValResult::Ok(obj.to_object(py))
        } else {
            single_val_error!(py, obj, kind = ErrorKind::NoneRequired)
        }
    }

    fn clone_dyn(&self) -> Box<dyn TypeValidator> {
        Box::new(self.clone())
    }
}
