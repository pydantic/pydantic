use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::errors::{err_val_error, ErrorKind, InputValue, ValResult};
use crate::input::Input;

use super::{BuildValidator, CombinedValidator, Extra, SlotsBuilder, Validator};

#[derive(Debug, Clone)]
pub struct NoneValidator;

impl BuildValidator for NoneValidator {
    const EXPECTED_TYPE: &'static str = "none";

    fn build(
        _schema: &PyDict,
        _config: Option<&PyDict>,
        _slots_builder: &mut SlotsBuilder,
    ) -> PyResult<CombinedValidator> {
        Ok(Self.into())
    }
}

impl Validator for NoneValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        match input.is_none() {
            true => Ok(py.None()),
            false => err_val_error!(
                input_value = InputValue::InputRef(input),
                kind = ErrorKind::NoneRequired
            ),
        }
    }

    fn get_name(&self, _py: Python) -> String {
        Self::EXPECTED_TYPE.to_string()
    }
}
