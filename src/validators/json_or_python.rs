use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::definitions::DefinitionsBuilder;
use crate::errors::ValResult;
use crate::input::Input;
use crate::recursion_guard::RecursionGuard;
use crate::tools::SchemaDict;

use super::InputType;
use super::{build_validator, BuildValidator, CombinedValidator, Definitions, Extra, Validator};

#[derive(Debug, Clone)]
pub struct JsonOrPython {
    json: Box<CombinedValidator>,
    python: Box<CombinedValidator>,
    name: String,
}

impl BuildValidator for JsonOrPython {
    const EXPECTED_TYPE: &'static str = "json-or-python";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let json_schema: &PyDict = schema.get_as_req(intern!(py, "json_schema"))?;
        let python_schema: &PyDict = schema.get_as_req(intern!(py, "python_schema"))?;

        let json = build_validator(json_schema, config, definitions)?;
        let python = build_validator(python_schema, config, definitions)?;

        let name = format!(
            "{}[json={},python={}]",
            Self::EXPECTED_TYPE,
            json.get_name(),
            python.get_name(),
        );
        Ok(Self {
            json: Box::new(json),
            python: Box::new(python),
            name,
        }
        .into())
    }
}

impl Validator for JsonOrPython {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        definitions: &'data Definitions<CombinedValidator>,
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        match extra.mode {
            InputType::Python => self.python.validate(py, input, extra, definitions, recursion_guard),
            InputType::Json => self.json.validate(py, input, extra, definitions, recursion_guard),
        }
    }

    fn different_strict_behavior(
        &self,
        definitions: Option<&DefinitionsBuilder<CombinedValidator>>,
        ultra_strict: bool,
    ) -> bool {
        self.json.different_strict_behavior(definitions, ultra_strict)
            || self.python.different_strict_behavior(definitions, ultra_strict)
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, definitions: &DefinitionsBuilder<CombinedValidator>) -> PyResult<()> {
        self.json.complete(definitions)?;
        self.python.complete(definitions)
    }
}
