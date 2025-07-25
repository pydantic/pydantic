use core::fmt::Debug;

use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::common::missing_sentinel::get_missing_sentinel_object;
use crate::errors::{ErrorType, ValError, ValResult};
use crate::input::Input;

use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

#[derive(Debug, Clone)]
pub struct MissingSentinelValidator {}

impl BuildValidator for MissingSentinelValidator {
    const EXPECTED_TYPE: &'static str = "missing-sentinel";

    fn build(
        _schema: &Bound<'_, PyDict>,
        _config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        Ok(CombinedValidator::MissingSentinel(Self {}))
    }
}

impl_py_gc_traverse!(MissingSentinelValidator {});

impl Validator for MissingSentinelValidator {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        _state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<PyObject> {
        let missing_sentinel = get_missing_sentinel_object(py);

        match input.as_python() {
            Some(v) if v.is(missing_sentinel) => Ok(v.to_owned().into()),
            _ => Err(ValError::new(ErrorType::MissingSentinelError { context: None }, input)),
        }
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}
