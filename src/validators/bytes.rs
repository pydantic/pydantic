use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::{is_strict, SchemaDict};
use crate::errors::{ErrorKind, ValError, ValResult};
use crate::input::{EitherBytes, Input};
use crate::recursion_guard::RecursionGuard;

use super::{BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct BytesValidator;

impl BuildValidator for BytesValidator {
    const EXPECTED_TYPE: &'static str = "bytes";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        _build_context: &mut BuildContext,
    ) -> PyResult<CombinedValidator> {
        let use_constrained = schema.get_item("max_length").is_some() || schema.get_item("min_length").is_some();
        if use_constrained {
            BytesConstrainedValidator::build(schema, config)
        } else if is_strict(schema, config)? {
            StrictBytesValidator::build()
        } else {
            Ok(Self.into())
        }
    }
}

impl Validator for BytesValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let either_bytes = input.lax_bytes()?;
        Ok(either_bytes.into_py(py))
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let either_bytes = input.strict_bytes()?;
        Ok(either_bytes.into_py(py))
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}

#[derive(Debug, Clone)]
pub struct StrictBytesValidator;

impl StrictBytesValidator {
    fn build() -> PyResult<CombinedValidator> {
        Ok(Self.into())
    }
}

impl Validator for StrictBytesValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let either_bytes = input.strict_bytes()?;
        Ok(either_bytes.into_py(py))
    }

    fn get_name(&self) -> &str {
        "strict-bytes"
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
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let bytes = match self.strict {
            true => input.strict_bytes()?,
            false => input.lax_bytes()?,
        };
        self._validation_logic(py, input, bytes)
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        self._validation_logic(py, input, input.strict_bytes()?)
    }

    fn get_name(&self) -> &str {
        "constrained-bytes"
    }
}

impl BytesConstrainedValidator {
    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<CombinedValidator> {
        Ok(Self {
            strict: is_strict(schema, config)?,
            min_length: schema.get_as("min_length")?,
            max_length: schema.get_as("max_length")?,
        }
        .into())
    }

    fn _validation_logic<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        either_bytes: EitherBytes<'data>,
    ) -> ValResult<'data, PyObject> {
        let len = either_bytes.len().map_err(Into::<ValError>::into)?;

        if let Some(min_length) = self.min_length {
            if len < min_length {
                return Err(ValError::new(ErrorKind::BytesTooShort { min_length }, input));
            }
        }
        if let Some(max_length) = self.max_length {
            if len > max_length {
                return Err(ValError::new(ErrorKind::BytesTooLong { max_length }, input));
            }
        }

        Ok(either_bytes.into_py(py))
    }
}
