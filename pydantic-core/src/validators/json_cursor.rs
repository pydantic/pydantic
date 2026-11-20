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
    utf8_checked: bool,
}

impl<'data> JsonCursor<'data> {
    pub(super) fn new(data: &'data [u8]) -> Self {
        Self::new_with_utf8_checked(data, false)
    }

    /// A Python string has already passed UTF-8 conversion before cursor entry.
    pub(super) fn new_with_utf8_checked(data: &'data [u8], utf8_checked: bool) -> Self {
        Self {
            jiter: Jiter::new(data).with_allow_inf_nan(),
            data,
            start: 0,
            depth: 0,
            error_value: OnceCell::new(),
            incomplete_validation_error: false,
            utf8_checked,
        }
    }

    pub(super) fn context(&self) -> Self {
        self.at_value(&self.data[self.start..])
    }

    /// Fork a deferred value without resetting its document depth or UTF-8 proof.
    pub(super) fn at_value(&self, data: &'data [u8]) -> Self {
        let mut cursor = Self::new(data);
        cursor.utf8_checked = self.utf8_checked;
        cursor.depth = self.depth;
        cursor
    }

    pub(super) fn parse_error<E>(_: E) -> ValError {
        pyo3::exceptions::PyValueError::new_err("JSON cursor could not complete validation").into()
    }

    pub(super) fn take_value(&mut self) -> ValResult<JsonValue<'data>> {
        let start = self.jiter.current_index();
        let value = self.jiter.next_value().map_err(Self::parse_error)?;
        self.check_value_depth(start)?;
        Ok(value)
    }

    /// Jiter's skip checks JSON escapes, but deliberately omits raw UTF-8 checks.
    /// Check the input once on the first skip instead of checking each skipped span.
    pub(super) fn skip_value(&mut self) -> ValResult<()> {
        let start = self.jiter.current_index();
        self.jiter.next_skip().map_err(Self::parse_error)?;
        self.check_value_depth(start)?;
        if !self.utf8_checked {
            simdutf8::basic::from_utf8(self.data).map_err(Self::parse_error)?;
            self.utf8_checked = true;
        }
        Ok(())
    }

    /// Jiter applies its recursion limit relative to this value, not the document.
    /// Most values cannot exhaust the remaining budget, so avoid rescanning them.
    fn check_value_depth(&self, start: usize) -> ValResult<()> {
        let span = &self.data[start..self.jiter.current_index()];
        if self.depth != 0
            && span.len() > usize::from(200 - self.depth) * 2
            && matches!(span.iter().find(|byte| !byte.is_ascii_whitespace()), Some(b'[' | b'{'))
        {
            self.check_container_depth(span)?;
        }
        Ok(())
    }

    #[inline(never)]
    fn check_container_depth(&self, span: &[u8]) -> ValResult<()> {
        let mut depth = usize::from(self.depth);
        let mut bytes = span.iter();
        while let Some(byte) = bytes.next() {
            match byte {
                b'"' => {
                    // Jiter already checked syntax and escapes. Structural bytes in
                    // strings do not contribute to the document's container depth.
                    while let Some(byte) = bytes.next() {
                        match byte {
                            b'\\' => {
                                bytes.next();
                            }
                            b'"' => break,
                            _ => (),
                        }
                    }
                }
                b'[' | b'{' => {
                    depth += 1;
                    if depth > 200 {
                        // Empty containers at the boundary may still be valid.
                        // Retry the ordinary parser for the exact decision/error.
                        return Err(Self::parse_error(()));
                    }
                }
                b']' | b'}' => depth -= 1,
                _ => (),
            }
        }
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
