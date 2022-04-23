use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_macros::is_strict;
use crate::errors::ValResult;
use crate::input::Input;

use super::{Extra, Validator};

#[derive(Debug, Clone)]
pub struct BoolValidator;

impl BoolValidator {
    pub const EXPECTED_TYPE: &'static str = "bool";
}

impl Validator for BoolValidator {
    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        if is_strict!(schema, config) {
            StrictBoolValidator::build(schema, config)
        } else {
            Ok(Box::new(Self {}))
        }
    }

    fn validate(&self, py: Python, input: &dyn Input, _extra: &Extra) -> ValResult<PyObject> {
        // TODO in theory this could be quicker if we used PyBool rather than going to a bool
        // and back again, might be worth profiling?
        Ok(input.lax_bool(py)?.into_py(py))
    }

    fn validate_strict(&self, py: Python, input: &dyn Input, _extra: &Extra) -> ValResult<PyObject> {
        Ok(input.strict_bool(py)?.into_py(py))
    }

    fn get_name(&self, _py: Python) -> String {
        Self::EXPECTED_TYPE.to_string()
    }

    #[no_coverage]
    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}

#[derive(Debug, Clone)]
struct StrictBoolValidator;

impl Validator for StrictBoolValidator {
    fn build(_schema: &PyDict, _config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        Ok(Box::new(Self {}))
    }

    fn validate(&self, py: Python, input: &dyn Input, _extra: &Extra) -> ValResult<PyObject> {
        Ok(input.strict_bool(py)?.into_py(py))
    }

    fn validate_strict(&self, py: Python, input: &dyn Input, extra: &Extra) -> ValResult<PyObject> {
        self.validate(py, input, extra)
    }

    fn get_name(&self, _py: Python) -> String {
        "strict-bool".to_string()
    }

    #[no_coverage]
    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}
