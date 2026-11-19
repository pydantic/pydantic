//! Cursor input for incremental JSON validation on the existing validator graph.

use std::cell::OnceCell;

use jiter::{Jiter, JsonValue};

use crate::errors::{InputValue, ToErrorValue, ValError, ValResult};
use crate::input::Input;
use pyo3::prelude::*;

use super::{CombinedValidator, ValidationState, Validator};

/// An optimistic cursor; any parsing or validation failure retries ordinary validation.
pub struct JsonCursor<'data> {
    pub(super) jiter: Jiter<'data>,
    pub(super) data: &'data [u8],
    start: usize,
    depth: usize,
    error_value: OnceCell<JsonValue<'data>>,
}

impl<'data> JsonCursor<'data> {
    pub(super) fn new(data: &'data [u8]) -> Self {
        Self {
            jiter: Jiter::new(data).with_allow_inf_nan(),
            data,
            start: 0,
            depth: 0,
            error_value: OnceCell::new(),
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

    pub(super) fn validate_next<'py>(
        &mut self,
        py: Python<'py>,
        validator: &CombinedValidator,
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Py<PyAny>> {
        if self.depth >= 200 {
            return Err(Self::parse_error(()));
        }
        self.depth += 1;
        let previous_start = self.start;
        self.start = self.jiter.current_index();
        let previous_error = self.error_value.take();
        let result = validator.validate_json_cursor(py, self, state);
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
