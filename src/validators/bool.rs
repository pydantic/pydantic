use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::is_strict;
use crate::errors::ValResult;
use crate::input::Input;

use super::{BuildValidator, CombinedValidator, Extra, SlotsBuilder, Validator};

#[derive(Debug, Clone)]
pub struct BoolValidator;

impl BuildValidator for BoolValidator {
    const EXPECTED_TYPE: &'static str = "bool";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        _slots_builder: &mut SlotsBuilder,
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
        input: &'data dyn Input,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        // TODO in theory this could be quicker if we used PyBool rather than going to a bool
        // and back again, might be worth profiling?
        Ok(input.lax_bool()?.into_py(py))
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        Ok(input.strict_bool()?.into_py(py))
    }

    fn get_name(&self, _py: Python) -> String {
        Self::EXPECTED_TYPE.to_string()
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
        input: &'data dyn Input,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        Ok(input.strict_bool()?.into_py(py))
    }

    fn get_name(&self, _py: Python) -> String {
        "strict-bool".to_string()
    }
}
