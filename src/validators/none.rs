use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::errors::{ErrorTypeDefaults, ValError, ValResult};
use crate::input::Input;

use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

#[derive(Debug, Clone)]
pub struct NoneValidator;

impl BuildValidator for NoneValidator {
    const EXPECTED_TYPE: &'static str = "none";

    fn build(
        _schema: &Bound<'_, PyDict>,
        _config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        Ok(Self.into())
    }
}

impl_py_gc_traverse!(NoneValidator {});

impl Validator for NoneValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _state: &mut ValidationState,
    ) -> ValResult<PyObject> {
        match input.is_none() {
            true => Ok(py.None()),
            false => Err(ValError::new(ErrorTypeDefaults::NoneRequired, input)),
        }
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}
