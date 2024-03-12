use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::errors::ValResult;
use crate::input::Input;
use crate::tools::SchemaDict;

use super::ValidationState;
use super::{build_validator, BuildValidator, CombinedValidator, DefinitionsBuilder, Validator};

#[derive(Debug)]
pub struct NullableValidator {
    validator: Box<CombinedValidator>,
    name: String,
}

impl BuildValidator for NullableValidator {
    const EXPECTED_TYPE: &'static str = "nullable";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let schema = schema.get_as_req(intern!(schema.py(), "schema"))?;
        let validator = Box::new(build_validator(&schema, config, definitions)?);
        let name = format!("{}[{}]", Self::EXPECTED_TYPE, validator.get_name());
        Ok(Self { validator, name }.into())
    }
}

impl_py_gc_traverse!(NullableValidator { validator });

impl Validator for NullableValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<PyObject> {
        match input.is_none() {
            true => Ok(py.None()),
            false => self.validator.validate(py, input, state),
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}
