use pyo3::exceptions::PyTypeError;
use pyo3::prelude::*;
use pyo3::PyDowncastError;

use jiter::JsonValue;

use crate::input::Input;

use super::location::{LocItem, Location};
use super::types::ErrorType;

pub type ValResult<T> = Result<T, ValError>;

pub trait AsErrorValue {
    fn as_error_value(&self) -> InputValue;
}

impl<'a, T: Input<'a>> AsErrorValue for T {
    fn as_error_value(&self) -> InputValue {
        Input::as_error_value(self)
    }
}

#[cfg_attr(debug_assertions, derive(Debug))]
pub enum ValError {
    LineErrors(Vec<ValLineError>),
    InternalErr(PyErr),
    Omit,
    UseDefault,
}

impl From<PyErr> for ValError {
    fn from(py_err: PyErr) -> Self {
        Self::InternalErr(py_err)
    }
}

impl From<PyDowncastError<'_>> for ValError {
    fn from(py_downcast: PyDowncastError) -> Self {
        Self::InternalErr(PyTypeError::new_err(py_downcast.to_string()))
    }
}

impl From<Vec<ValLineError>> for ValError {
    fn from(line_errors: Vec<ValLineError>) -> Self {
        Self::LineErrors(line_errors)
    }
}

impl ValError {
    pub fn new(error_type: ErrorType, input: &impl AsErrorValue) -> ValError {
        Self::LineErrors(vec![ValLineError::new(error_type, input)])
    }

    pub fn new_with_loc(error_type: ErrorType, input: &impl AsErrorValue, loc: impl Into<LocItem>) -> ValError {
        Self::LineErrors(vec![ValLineError::new_with_loc(error_type, input, loc)])
    }

    pub fn new_custom_input(error_type: ErrorType, input_value: InputValue) -> ValError {
        Self::LineErrors(vec![ValLineError::new_custom_input(error_type, input_value)])
    }

    /// helper function to call with_outer on line items if applicable
    pub fn with_outer_location(self, loc_item: LocItem) -> Self {
        match self {
            Self::LineErrors(mut line_errors) => {
                for line_error in &mut line_errors {
                    line_error.location.with_outer(loc_item.clone());
                }
                Self::LineErrors(line_errors)
            }
            other => other,
        }
    }
}

/// A `ValLineError` is a single error that occurred during validation which is converted to a `PyLineError`
/// to eventually form a `ValidationError`.
/// I don't like the name `ValLineError`, but it's the best I could come up with (for now).
#[cfg_attr(debug_assertions, derive(Debug))]
pub struct ValLineError {
    pub error_type: ErrorType,
    // location is reversed so that adding an "outer" location item is pushing, it's reversed before showing to the user
    pub location: Location,
    pub input_value: InputValue,
}

impl ValLineError {
    pub fn new(error_type: ErrorType, input: &impl AsErrorValue) -> ValLineError {
        Self {
            error_type,
            input_value: input.as_error_value(),
            location: Location::default(),
        }
    }

    pub fn new_with_loc(error_type: ErrorType, input: &impl AsErrorValue, loc: impl Into<LocItem>) -> ValLineError {
        Self {
            error_type,
            input_value: input.as_error_value(),
            location: Location::new_some(loc.into()),
        }
    }

    pub fn new_with_full_loc(error_type: ErrorType, input: &impl AsErrorValue, location: Location) -> ValLineError {
        Self {
            error_type,
            input_value: input.as_error_value(),
            location,
        }
    }

    pub fn new_custom_input(error_type: ErrorType, input_value: InputValue) -> ValLineError {
        Self {
            error_type,
            input_value,
            location: Location::default(),
        }
    }

    /// location is stored reversed so it's quicker to add "outer" items as that's what we always do
    /// hence `push` here instead of `insert`
    pub fn with_outer_location(mut self, loc_item: LocItem) -> Self {
        self.location.with_outer(loc_item);
        self
    }

    // change the error_type on a error in place
    pub fn with_type(mut self, error_type: ErrorType) -> Self {
        self.error_type = error_type;
        self
    }
}

#[cfg_attr(debug_assertions, derive(Debug))]
#[derive(Clone)]
pub enum InputValue {
    Python(PyObject),
    Json(JsonValue),
}

impl ToPyObject for InputValue {
    fn to_object(&self, py: Python) -> PyObject {
        match self {
            Self::Python(input) => input.clone_ref(py),
            Self::Json(input) => input.to_object(py),
        }
    }
}
