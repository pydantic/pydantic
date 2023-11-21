use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::errors::ValResult;
use crate::input::Input;

use super::{
    validation_state::Exactness, BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator,
};

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
        state: &mut ValidationState,
    ) -> ValResult<PyObject> {
        // in a union, Any should be preferred to doing lax coercions
        state.floor_exactness(Exactness::Strict);
        Ok(input.to_object(py))
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}
