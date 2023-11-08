use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::errors::{ErrorTypeDefaults, ValError, ValResult};
use crate::input::Input;

use super::validation_state::Exactness;
use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

#[derive(Debug, Clone)]
pub struct CallableValidator;

impl BuildValidator for CallableValidator {
    const EXPECTED_TYPE: &'static str = "callable";

    fn build(
        _schema: &PyDict,
        _config: Option<&PyDict>,
        _definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        Ok(Self.into())
    }
}

impl_py_gc_traverse!(CallableValidator {});

impl Validator for CallableValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        state.floor_exactness(Exactness::Lax);
        match input.callable() {
            true => Ok(input.to_object(py)),
            false => Err(ValError::new(ErrorTypeDefaults::CallableType, input)),
        }
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}
