//! Cursor input for incremental JSON validation on the existing validator graph.

use std::cell::OnceCell;

use jiter::{Jiter, JsonValue};

use crate::errors::{InputValue, ToErrorValue, ValError, ValResult};
use crate::input::Input;

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
        self.jiter
            .next_value_with_recursion_limit(200 - self.depth)
            .map_err(Self::parse_error)
    }

    /// Check syntax and the remaining depth without establishing raw UTF-8 validity.
    pub(super) fn defer_value(&mut self) -> ValResult<()> {
        self.jiter
            .next_skip_with_recursion_limit(200 - self.depth)
            .map_err(Self::parse_error)
    }

    /// Jiter's skip checks JSON escapes, but deliberately omits raw UTF-8 checks.
    /// Check the input once on the first skip instead of checking each skipped span.
    pub(super) fn skip_value(&mut self) -> ValResult<()> {
        self.defer_value()?;
        if !self.utf8_checked {
            simdutf8::basic::from_utf8(self.data).map_err(Self::parse_error)?;
            self.utf8_checked = true;
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

    /// Only direct containers need cursor error context. Scalar and fallback
    /// validators already own the JsonValue used to construct their errors.
    pub(super) fn with_container<T>(&mut self, validate: impl FnOnce(&mut Self) -> ValResult<T>) -> ValResult<T> {
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
        if matches!(&result, Err(ValError::LineErrors(_))) {
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
