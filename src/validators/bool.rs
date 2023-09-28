use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::is_strict;
use crate::errors::ValResult;
use crate::input::Input;

use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

#[derive(Debug, Clone)]
pub struct BoolValidator {
    strict: bool,
}

impl BuildValidator for BoolValidator {
    const EXPECTED_TYPE: &'static str = "bool";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        _definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        Ok(Self {
            strict: is_strict(schema, config)?,
        }
        .into())
    }
}

impl_py_gc_traverse!(BoolValidator {});

impl Validator for BoolValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        // TODO in theory this could be quicker if we used PyBool rather than going to a bool
        // and back again, might be worth profiling?
        let strict = state.strict_or(self.strict);
        Ok(input.validate_bool(strict)?.into_py(py))
    }

    fn different_strict_behavior(&self, ultra_strict: bool) -> bool {
        !ultra_strict
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }

    fn complete(&self) -> PyResult<()> {
        Ok(())
    }
}
