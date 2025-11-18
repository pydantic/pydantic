use std::sync::Arc;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::py_schema_err;
use crate::errors::ValResult;
use crate::input::Input;
use crate::tools::SchemaDict;

use super::ValidationState;
use super::{build_validator, BuildValidator, CombinedValidator, DefinitionsBuilder, Validator};

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
        let name = format!("{}[{}]", Self::EXPECTED_TYPE, validator.get_name());
        Ok(CombinedValidator::Nullable(Self { validator, name }).into())
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

    fn children(&self) -> Vec<&Arc<CombinedValidator>> {
        vec![&self.validator]
    }

    fn with_new_children(&self, children: Vec<Arc<CombinedValidator>>) -> PyResult<Arc<CombinedValidator>> {
        if children.len() != 1 {
            return py_schema_err!("Nullable must have exactly one child");
        }
        Ok(CombinedValidator::Nullable(Self {
            validator: children.into_iter().next().unwrap(),
            name: self.name.clone(),
        })
        .into())
    }
}
