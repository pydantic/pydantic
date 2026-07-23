use core::fmt::Debug;
use std::sync::{Arc, LazyLock};

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyEllipsis};

use crate::errors::{ErrorType, ValError, ValResult};
use crate::input::Input;

use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

#[derive(Debug, Clone)]
pub struct EllipsisValidator {}

static ELLIPSIS_VALIDATOR: LazyLock<Arc<CombinedValidator>> =
    LazyLock::new(|| CombinedValidator::Ellipsis(EllipsisValidator {}).into());

impl BuildValidator for EllipsisValidator {
    const EXPECTED_TYPE: &'static str = "ellipsis";

    fn build(
        _schema: &Bound<'_, PyDict>,
        _config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<Arc<CombinedValidator>>,
    ) -> PyResult<Arc<CombinedValidator>> {
        Ok(ELLIPSIS_VALIDATOR.clone())
    }
}

impl_py_gc_traverse!(EllipsisValidator {});

impl Validator for EllipsisValidator {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        _state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Py<PyAny>> {
        match input.as_python() {
            Some(v) if v.is(PyEllipsis::get(py)) => Ok(v.to_owned().into()),
            _ => Err(ValError::new(ErrorType::EllipsisError { context: None }, input)),
        }
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}
