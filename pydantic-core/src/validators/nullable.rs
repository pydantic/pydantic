use std::sync::Arc;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::definitions::{ChildKey, InternKey};
use crate::errors::ValResult;
use crate::input::Input;
use crate::tools::SchemaDict;

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
        let global_child = super::global_child_key(&validator);
        let ptr_key = InternKey::Nullable(ChildKey::Ptr(Arc::as_ptr(&validator) as usize));
        let build_node = move || {
            let name = format!("{}[{}]", Self::EXPECTED_TYPE, validator.get_name());
            CombinedValidator::Nullable(Self { validator, name }).into()
        };
        match global_child {
            // data-free subtree: shared across all builds in the process
            Some(child) => Ok(super::get_or_intern_global(InternKey::Nullable(child), build_node)),
            None => Ok(definitions.get_or_intern(ptr_key, build_node)),
        }
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
