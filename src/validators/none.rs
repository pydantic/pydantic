use pyo3::prelude::*;
use pyo3::types::PyDict;

use super::{Extra, Validator};
use crate::errors::ValResult;
use crate::input::Input;

#[derive(Debug, Clone)]
pub struct NoneValidator;

impl NoneValidator {
    pub const EXPECTED_TYPE: &'static str = "none";
}

impl Validator for NoneValidator {
    fn build(_schema: &PyDict, _config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        Ok(Box::new(Self))
    }

    fn validate(&self, py: Python, input: &dyn Input, _extra: &Extra) -> ValResult<PyObject> {
        input.validate_none(py)?;
        ValResult::Ok(py.None())
    }

    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}
