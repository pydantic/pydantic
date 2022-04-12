use pyo3::prelude::*;
use pyo3::types::PyDict;

use super::Validator;
use crate::errors::{err_val_error, ErrorKind, ValResult};

#[derive(Debug, Clone)]
pub struct NoneValidator;

impl NoneValidator {
    pub const EXPECTED_TYPE: &'static str = "none";
}

impl Validator for NoneValidator {
    fn build(_dict: &PyDict) -> PyResult<Self> {
        Ok(Self)
    }

    fn validate(&self, py: Python, input: &PyAny, _data: &PyDict) -> ValResult<PyObject> {
        if input.is_none() {
            ValResult::Ok(input.into_py(py))
        } else {
            err_val_error!(py, input, kind = ErrorKind::NoneRequired)
        }
    }

    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}
