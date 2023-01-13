use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::{is_strict, SchemaDict};
use crate::errors::{ErrorType, ValError, ValResult};
use crate::input::Input;
use crate::recursion_guard::RecursionGuard;

use super::{BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct BytesValidator {
    strict: bool,
}

impl BuildValidator for BytesValidator {
    const EXPECTED_TYPE: &'static str = "bytes";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        _build_context: &mut BuildContext<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let use_constrained = schema.get_item(intern!(py, "max_length")).is_some()
            || schema.get_item(intern!(py, "min_length")).is_some();
        if use_constrained {
            BytesConstrainedValidator::build(schema, config)
        } else {
            Ok(Self {
                strict: is_strict(schema, config)?,
            }
            .into())
        }
    }
}

impl Validator for BytesValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let either_bytes = input.validate_bytes(extra.strict.unwrap_or(self.strict))?;
        Ok(either_bytes.into_py(py))
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}

#[derive(Debug, Clone)]
pub struct BytesConstrainedValidator {
    strict: bool,
    max_length: Option<usize>,
    min_length: Option<usize>,
}

impl Validator for BytesConstrainedValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let either_bytes = input.validate_bytes(extra.strict.unwrap_or(self.strict))?;
        let len = either_bytes.len()?;

        if let Some(min_length) = self.min_length {
            if len < min_length {
                return Err(ValError::new(ErrorType::BytesTooShort { min_length }, input));
            }
        }
        if let Some(max_length) = self.max_length {
            if len > max_length {
                return Err(ValError::new(ErrorType::BytesTooLong { max_length }, input));
            }
        }

        Ok(either_bytes.into_py(py))
    }

    fn get_name(&self) -> &str {
        "constrained-bytes"
    }
}

impl BytesConstrainedValidator {
    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<CombinedValidator> {
        let py = schema.py();
        Ok(Self {
            strict: is_strict(schema, config)?,
            min_length: schema.get_as(intern!(py, "min_length"))?,
            max_length: schema.get_as(intern!(py, "max_length"))?,
        }
        .into())
    }
}
