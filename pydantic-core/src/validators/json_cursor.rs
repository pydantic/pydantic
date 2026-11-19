//! Cursor input for incremental JSON validation on the existing validator graph.

use std::cell::OnceCell;

use jiter::{Jiter, JsonValue};

use crate::errors::{InputValue, ToErrorValue, ValResult};
use crate::input::Input;
use pyo3::prelude::*;

use super::{CombinedValidator, ValidationState, Validator};

/// A cursor into a document whose complete syntax has already been checked.
pub struct JsonCursor<'data> {
    pub(super) jiter: Jiter<'data>,
    pub(super) data: &'data [u8],
    start: usize,
    error_value: OnceCell<JsonValue<'data>>,
}

impl<'data> JsonCursor<'data> {
    pub(super) fn new(data: &'data [u8]) -> Self {
        Self {
            jiter: Jiter::new(data).with_allow_inf_nan(),
            data,
            start: 0,
            error_value: OnceCell::new(),
        }
    }

    pub(super) fn take_value(&mut self) -> JsonValue<'data> {
        self.jiter
            .next_value()
            .expect("the document has already passed JSON validation")
    }

    pub(super) fn value_for_context(&self) -> &JsonValue<'data> {
        self.error_value.get_or_init(|| {
            Jiter::new(&self.data[self.start..])
                .with_allow_inf_nan()
                .next_value()
                .expect("the document has already passed JSON validation")
        })
    }

    pub(super) fn array_length(&self) -> usize {
        match self.value_for_context() {
            JsonValue::Array(array) => array.len(),
            _ => unreachable!("checked array"),
        }
    }

    /// Finish an array after an early validation error so its parent can continue.
    pub(super) fn skip_array_tail(&mut self) {
        while self.jiter.array_step().expect("checked array").is_some() {
            self.jiter.next_skip().expect("checked array item");
        }
    }

    pub(super) fn validate_next<'py>(
        &mut self,
        py: Python<'py>,
        validator: &CombinedValidator,
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Py<PyAny>> {
        let previous_start = self.start;
        self.start = self.jiter.current_index();
        let previous_error = self.error_value.take();
        let result = validator.validate_json_cursor(py, self, state);
        self.start = previous_start;
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
