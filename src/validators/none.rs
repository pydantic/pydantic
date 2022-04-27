use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::errors::{err_val_error, ErrorKind, InputValue, ValResult};
use crate::input::Input;

use super::{validator_boilerplate, Extra, Validator, ValidatorArc};

#[derive(Debug, Clone)]
pub struct NoneValidator;

impl NoneValidator {
    pub const EXPECTED_TYPE: &'static str = "none";
}

impl Validator for NoneValidator {
    fn build(_schema: &PyDict, _config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        Ok(Box::new(Self))
    }

    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        match input.is_none(py) {
            true => Ok(py.None()),
            false => err_val_error!(
                input_value = InputValue::InputRef(input),
                kind = ErrorKind::NoneRequired
            ),
        }
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        self.validate(py, input, extra)
    }

    validator_boilerplate!(Self::EXPECTED_TYPE);
}
