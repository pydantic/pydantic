use core::fmt::Debug;
use std::sync::Arc;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::common::missing_sentinel::get_missing_sentinel_object;
use crate::errors::{ErrorType, ValError, ValResult};
use crate::input::Input;
use crate::tools::SchemaDict;

use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator, build_validator};

#[derive(Debug)]
pub struct MissingSentinelValidator {
    /// The validator of the inner schema (if any). If not set, only the `MISSING` sentinel is a valid input.
    validator: Option<Arc<CombinedValidator>>,
    name: String,
}

impl BuildValidator for MissingSentinelValidator {
    const EXPECTED_TYPE: &'static str = "missing-sentinel";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedValidator>>,
    ) -> PyResult<Arc<CombinedValidator>> {
        let py = schema.py();
        let (validator, name) = match schema.get_as::<Bound<'_, PyDict>>(intern!(py, "schema"))? {
            Some(inner_schema) => {
                let validator = build_validator(&inner_schema, config, definitions)?;
                let name = format!("{}[{}]", Self::EXPECTED_TYPE, validator.get_name());
                (Some(validator), name)
            }
            None => (None, Self::EXPECTED_TYPE.to_string()),
        };
        Ok(CombinedValidator::MissingSentinel(Self { validator, name }).into())
    }
}

impl_py_gc_traverse!(MissingSentinelValidator { validator });

impl Validator for MissingSentinelValidator {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Py<PyAny>> {
        let missing_sentinel = get_missing_sentinel_object(py);

        if let Some(v) = input.as_python()
            && v.is(missing_sentinel)
        {
            return Ok(v.to_owned().into());
        }

        match &self.validator {
            Some(validator) => validator.validate(py, input, state),
            None => Err(ValError::new(ErrorType::MissingSentinelError { context: None }, input)),
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}
