use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::is_strict;
use crate::errors::ValResult;
use crate::input::Input;
use crate::tools::SchemaDict;

use super::Exactness;
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
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let lax_schema = schema.get_as_req(intern!(py, "lax_schema"))?;
        let lax_validator = Box::new(build_validator(&lax_schema, config, definitions)?);

        let strict_schema = schema.get_as_req(intern!(py, "strict_schema"))?;
        let strict_validator = Box::new(build_validator(&strict_schema, config, definitions)?);

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
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<PyObject> {
        if state.strict_or(self.strict) {
            self.strict_validator.validate(py, input, state)
        } else {
            // horrible edge case: if doing smart union validation, we need to try the strict validator
            // anyway and prefer that if it succeeds
            if state.exactness.is_some() {
                if let Ok(strict_result) = self.strict_validator.validate(py, input, state) {
                    return Ok(strict_result);
                }
                // this is now known to be not strict
                state.floor_exactness(Exactness::Lax);
            }
            self.lax_validator.validate(py, input, state)
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}
