use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::is_strict;
use crate::errors::ValResult;
use crate::input::Input;

use super::{validator_boilerplate, Extra, Validator};

#[derive(Debug, Clone)]
pub struct BoolValidator;

impl BoolValidator {
    pub const EXPECTED_TYPE: &'static str = "bool";
}

impl Validator for BoolValidator {
    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        if is_strict(schema, config)? {
            StrictBoolValidator::build(schema, config)
        } else {
            Ok(Box::new(Self {}))
        }
    }

    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        // TODO in theory this could be quicker if we used PyBool rather than going to a bool
        // and back again, might be worth profiling?
        Ok(input.lax_bool(py)?.into_py(py))
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        Ok(input.strict_bool(py)?.into_py(py))
    }

    validator_boilerplate!(Self::EXPECTED_TYPE);
}

#[derive(Debug, Clone)]
struct StrictBoolValidator;

impl Validator for StrictBoolValidator {
    fn build(_schema: &PyDict, _config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        Ok(Box::new(Self {}))
    }

    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        Ok(input.strict_bool(py)?.into_py(py))
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        self.validate(py, input, extra)
    }

    validator_boilerplate!("strict-bool");
}
