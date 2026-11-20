//! Cursor input for incremental JSON validation on the existing validator graph.

use std::cell::OnceCell;

use jiter::{Jiter, JsonValue};

use crate::errors::{InputValue, ToErrorValue, ValError, ValResult};
use crate::input::Input;

use super::{CombinedValidator, ValidationState, Validator};
use pyo3::prelude::*;

/// A cursor which retries parsing failures and incomplete validation attempts.
pub struct JsonCursor<'data> {
    pub(super) jiter: Jiter<'data>,
    pub(super) data: &'data [u8],
    start: usize,
    // Traversal is capped at 200; keep the error flag within the existing cursor size.
    depth: u8,
    error_value: OnceCell<JsonValue<'data>>,
    pub(super) incomplete_validation_error: bool,
}

impl<'data> JsonCursor<'data> {
    pub(super) fn new(data: &'data [u8]) -> Self {
        Self {
            jiter: Jiter::new(data).with_allow_inf_nan(),
            data,
            start: 0,
            depth: 0,
            error_value: OnceCell::new(),
            incomplete_validation_error: false,
        }
    }

    pub(super) fn context(&self) -> Self {
        Self::new(&self.data[self.start..])
    }

    pub(super) fn parse_error<E>(_: E) -> ValError {
        pyo3::exceptions::PyValueError::new_err("JSON cursor could not complete validation").into()
    }

    pub(super) fn take_value(&mut self) -> ValResult<JsonValue<'data>> {
        self.jiter.next_value().map_err(Self::parse_error)
    }

    /// Validate UTF-8 only for values skipped by the incremental model scheduler.
    /// Other values are decoded by their ordinary or direct validators.
    pub(super) fn skip_value(&mut self) -> ValResult<()> {
        let start = self.jiter.current_index();
        self.jiter.next_skip().map_err(Self::parse_error)?;
        std::str::from_utf8(self.jiter.slice_to_current(start)).map_err(Self::parse_error)?;
        Ok(())
    }

    /// Consume the remainder of an object after its current value was consumed.
    #[cold]
    pub(super) fn finish_object(&mut self) -> ValResult<()> {
        while self.jiter.next_key().map_err(Self::parse_error)?.is_some() {
            self.skip_value()?;
        }
        Ok(())
    }

    pub(super) fn value_for_context(&self) -> &JsonValue<'data> {
        // Error input is provisional: malformed subtrees can use a placeholder because
        // the entire failed attempt is retried through ordinary validation.
        self.error_value.get_or_init(|| {
            Jiter::new(&self.data[self.start..])
                .with_allow_inf_nan()
                .next_value()
                .unwrap_or(JsonValue::Null)
        })
    }

    /// Do not let a parent advance from a child which stopped inside its value.
    #[inline]
    pub(super) fn validate_next<'py>(
        &mut self,
        py: Python<'py>,
        validator: &CombinedValidator,
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Py<PyAny>> {
        let result = validator.validate_json_cursor(py, self, state);
        if self.incomplete_validation_error {
            Self::reject_incomplete_error(result)
        } else {
            result
        }
    }

    #[cold]
    fn reject_incomplete_error<T>(result: ValResult<T>) -> ValResult<T> {
        match result {
            Err(ValError::LineErrors(_)) => Err(Self::parse_error(())),
            result => result,
        }
    }

    /// Only direct containers need cursor error context. Scalar and fallback
    /// validators already own the JsonValue used to construct their errors.
    pub(super) fn with_container<T>(&mut self, validate: impl FnOnce(&mut Self) -> ValResult<T>) -> ValResult<T> {
        self.with_container_scope::<T, false>(validate)
    }

    /// The callback may return LineErrors only after consuming the whole container.
    /// Other errors may leave it incomplete and still request ordinary retry.
    pub(super) fn with_complete_container<T>(
        &mut self,
        validate: impl FnOnce(&mut Self) -> ValResult<T>,
    ) -> ValResult<T> {
        self.with_container_scope::<T, true>(validate)
    }

    fn with_container_scope<T, const COMPLETE: bool>(
        &mut self,
        validate: impl FnOnce(&mut Self) -> ValResult<T>,
    ) -> ValResult<T> {
        if self.depth >= 200 {
            return Err(Self::parse_error(()));
        }
        self.depth += 1;
        let previous_start = self.start;
        self.start = self.jiter.current_index();
        let previous_error = self.error_value.take();
        let result = validate(self);
        // A container which exits with an error may not have consumed its value.
        // Completed list item errors are returned outside this scope instead.
        if !COMPLETE && matches!(&result, Err(ValError::LineErrors(_))) {
            self.incomplete_validation_error = true;
        }
        self.start = previous_start;
        self.depth -= 1;
        self.error_value.take();
        if let Some(previous_error) = previous_error {
            let _ = self.error_value.set(previous_error);
        }
        result
    }
}

impl ToErrorValue for &JsonCursor<'_> {
    fn to_error_value(&self) -> InputValue {
        self.value_for_context().as_error_value()
    }
}
