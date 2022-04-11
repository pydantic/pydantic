use pyo3::prelude::*;
use pyo3::types::PyDict;

use super::Validator;
use crate::errors::ValResult;
use crate::standalone_validators::validate_bool;

#[derive(Debug, Clone)]
pub struct BoolValidator;

impl Validator for BoolValidator {
    fn is_match(type_: &str, _dict: &PyDict) -> bool {
        type_ == "bool"
    }

    fn build(_dict: &PyDict) -> PyResult<Self> {
        Ok(Self)
    }

    fn validate(&self, py: Python, input: &PyAny) -> ValResult<PyObject> {
        // TODO in theory this could be quicker if we used PyBool rather than going to a bool
        // and back again, might be worth profiling?
        Ok(validate_bool(py, input)?.into_py(py))
    }

    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}
