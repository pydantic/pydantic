use std::sync::Arc;

use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::input::Input;
use crate::{build_tools::LazyLock, errors::ValResult};

use super::{
    validation_state::Exactness, BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator,
};

/// This might seem useless, but it's useful in DictValidator to avoid Option<Validator> a lot
#[derive(Debug, Clone)]
pub struct AnyValidator;

static ANY_VALIDATOR: LazyLock<Arc<CombinedValidator>> = LazyLock::new(|| Arc::new(AnyValidator.into()));

impl BuildValidator for AnyValidator {
    const EXPECTED_TYPE: &'static str = "any";

    fn build(
        _schema: &Bound<'_, PyDict>,
        _config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<Arc<CombinedValidator>>,
    ) -> PyResult<Arc<CombinedValidator>> {
        Ok(ANY_VALIDATOR.clone())
    }
}

impl_py_gc_traverse!(AnyValidator {});

impl Validator for AnyValidator {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Py<PyAny>> {
        // in a union, Any should be preferred to doing lax coercions
        state.floor_exactness(Exactness::Strict);
        Ok(input.to_object(py)?.unbind())
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}
