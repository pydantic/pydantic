use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::errors::ValResult;
use crate::input::Input;

use super::{validation_state::ValidationState, BuildValidator, CombinedValidator, DefinitionsBuilder, Validator};

/// This might seem useless, but it's useful in DictValidator to avoid Option<Validator> a lot
#[derive(Debug, Clone)]
pub struct AnyValidator;

impl BuildValidator for AnyValidator {
    const EXPECTED_TYPE: &'static str = "any";

    fn build(
        _schema: &PyDict,
        _config: Option<&PyDict>,
        _definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        Ok(Self.into())
    }
}

impl_py_gc_traverse!(AnyValidator {});

impl Validator for AnyValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        Ok(input.to_object(py))
    }

    fn different_strict_behavior(&self, _ultra_strict: bool) -> bool {
        false
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }

    fn complete(&self) -> PyResult<()> {
        Ok(())
    }
}
