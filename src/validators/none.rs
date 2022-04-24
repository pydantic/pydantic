use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::errors::{err_val_error, ErrorKind, InputValue, ValResult};
use crate::input::Input;

use super::{Extra, Validator};

#[derive(Debug, Clone)]
pub struct NoneValidator;

impl NoneValidator {
    pub const EXPECTED_TYPE: &'static str = "none";
}

impl Validator for NoneValidator {
    fn build(_schema: &PyDict, _config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        Ok(Box::new(Self))
    }

    fn validate<'a>(&'a self, py: Python<'a>, input: &'a dyn Input, _extra: &Extra) -> ValResult<'a, PyObject> {
        match input.is_none(py) {
            true => Ok(py.None()),
            false => err_val_error!(
                input_value = InputValue::InputRef(input),
                kind = ErrorKind::NoneRequired
            ),
        }
    }

    fn validate_strict<'a>(&'a self, py: Python<'a>, input: &'a dyn Input, extra: &Extra) -> ValResult<'a, PyObject> {
        self.validate(py, input, extra)
    }

    fn get_name(&self, _py: Python) -> String {
        Self::EXPECTED_TYPE.to_string()
    }

    #[no_coverage]
    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}
