use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::is_strict;
use crate::errors::ValResult;
use crate::input::Input;
use crate::recursion_guard::RecursionGuard;

use super::{BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct BoolValidator;

impl BuildValidator for BoolValidator {
    const EXPECTED_TYPE: &'static str = "bool";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        _build_context: &mut BuildContext,
    ) -> PyResult<CombinedValidator> {
        if is_strict(schema, config)? {
            StrictBoolValidator::build()
        } else {
            Ok(Self.into())
        }
    }
}

impl Validator for BoolValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        // TODO in theory this could be quicker if we used PyBool rather than going to a bool
        // and back again, might be worth profiling?
        Ok(input.lax_bool()?.into_py(py))
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        Ok(input.strict_bool()?.into_py(py))
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}

#[derive(Debug, Clone)]
pub struct StrictBoolValidator;

impl StrictBoolValidator {
    pub fn build() -> PyResult<CombinedValidator> {
        Ok(Self.into())
    }
}

impl Validator for StrictBoolValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        Ok(input.strict_bool()?.into_py(py))
    }

    fn get_name(&self) -> &str {
        "strict-bool"
    }
}
