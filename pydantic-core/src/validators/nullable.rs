use std::sync::Arc;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::errors::ValResult;
use crate::input::Input;
use crate::tools::SchemaDict;

use crate::definitions::SharedNodeKey;

use super::ValidationState;
use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, Validator, build_validator};

#[derive(Debug)]
pub struct NullableValidator {
    validator: Arc<CombinedValidator>,
    name: String,
}

impl BuildValidator for NullableValidator {
    const EXPECTED_TYPE: &'static str = "nullable";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedValidator>>,
    ) -> PyResult<Arc<CombinedValidator>> {
        let schema = schema.get_as_req(intern!(schema.py(), "schema"))?;
        let validator = build_validator(&schema, config, definitions)?;

        // A `nullable` node is fully described by the validator it wraps, so any other `nullable`
        // node over the same validator in this build is interchangeable with this one:
        let key = SharedNodeKey::new(Self::EXPECTED_TYPE, &validator, None, 0);
        if let Some(shared) = definitions.get_shared_node(&key) {
            return Ok(shared.clone());
        }

        let name = format!("{}[{}]", Self::EXPECTED_TYPE, validator.get_name());
        let result: Arc<CombinedValidator> = CombinedValidator::Nullable(Self { validator, name }).into();
        definitions.set_shared_node(key, result.clone());
        Ok(result)
    }
}

impl_py_gc_traverse!(NullableValidator { validator });

impl Validator for NullableValidator {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Py<PyAny>> {
        match input.is_none() {
            true => Ok(py.None()),
            false => self.validator.validate(py, input, state),
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}
