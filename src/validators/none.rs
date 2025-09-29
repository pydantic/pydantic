use std::sync::Arc;

use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::LazyLock;
use crate::errors::{ErrorTypeDefaults, ValError, ValResult};
use crate::input::Input;

use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

#[derive(Debug, Clone)]
pub struct NoneValidator;

static NONE_VALIDATOR: LazyLock<Arc<CombinedValidator>> = LazyLock::new(|| Arc::new(NoneValidator.into()));

impl BuildValidator for NoneValidator {
    const EXPECTED_TYPE: &'static str = "none";

    fn build(
        _schema: &Bound<'_, PyDict>,
        _config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<Arc<CombinedValidator>>,
    ) -> PyResult<Arc<CombinedValidator>> {
        Ok(NONE_VALIDATOR.clone())
    }
}

impl_py_gc_traverse!(NoneValidator {});

impl Validator for NoneValidator {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        _state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Py<PyAny>> {
        match input.is_none() {
            true => Ok(py.None()),
            false => Err(ValError::new(ErrorTypeDefaults::NoneRequired, input)),
        }
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}
