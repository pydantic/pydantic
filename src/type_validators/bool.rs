use pyo3::prelude::*;
use pyo3::types::{PyBool, PyDict};

use super::TypeValidator;
use crate::errors::{err_val_error, ErrorKind, ValResult};

#[derive(Debug, Clone)]
pub struct BoolValidator;

impl TypeValidator for BoolValidator {
    fn is_match(type_: &str, _dict: &PyDict) -> bool {
        type_ == "bool"
    }

    fn build(_dict: &PyDict) -> PyResult<Self> {
        Ok(Self)
    }

    fn validate(&self, py: Python, obj: &PyAny) -> ValResult<PyObject> {
        let obj: &PyBool = match obj.extract() {
            Ok(obj) => obj,
            Err(_e) => return err_val_error!(py, obj, kind = ErrorKind::Bool),
        };
        ValResult::Ok(obj.to_object(py))
    }

    fn clone_dyn(&self) -> Box<dyn TypeValidator> {
        Box::new(self.clone())
    }
}
