use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::is_strict;
use crate::errors::ValResult;
use crate::input::Input;
use crate::tools::SchemaDict;

use super::ValidationState;
use super::{build_validator, BuildValidator, CombinedValidator, DefinitionsBuilder, Validator};

#[derive(Debug)]
pub struct LaxOrStrictValidator {
    strict: bool,
    lax_validator: Box<CombinedValidator>,
    strict_validator: Box<CombinedValidator>,
    name: String,
}

impl BuildValidator for LaxOrStrictValidator {
    const EXPECTED_TYPE: &'static str = "lax-or-strict";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let lax_schema = schema.get_as_req(intern!(py, "lax_schema"))?;
        let lax_validator = Box::new(build_validator(lax_schema, config, definitions)?);

        let strict_schema = schema.get_as_req(intern!(py, "strict_schema"))?;
        let strict_validator = Box::new(build_validator(strict_schema, config, definitions)?);

        let name = format!(
            "{}[lax={},strict={}]",
            Self::EXPECTED_TYPE,
            lax_validator.get_name(),
            strict_validator.get_name()
        );
        Ok(Self {
            strict: is_strict(schema, config)?,
            lax_validator,
            strict_validator,
            name,
        }
        .into())
    }
}

impl_py_gc_traverse!(LaxOrStrictValidator {
    lax_validator,
    strict_validator
});

impl Validator for LaxOrStrictValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        if state.strict_or(self.strict) {
            self.strict_validator.validate(py, input, state)
        } else {
            self.lax_validator.validate(py, input, state)
        }
    }

    fn different_strict_behavior(&self, ultra_strict: bool) -> bool {
        if ultra_strict {
            self.strict_validator.different_strict_behavior(true)
        } else {
            true
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&self) -> PyResult<()> {
        self.lax_validator.complete()?;
        self.strict_validator.complete()
    }
}
