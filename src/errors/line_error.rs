use pyo3::exceptions::PyTypeError;
use pyo3::prelude::*;
use pyo3::PyDowncastError;

use crate::input::{Input, JsonInput};

use super::location::{LocItem, Location};
use super::types::ErrorType;
use super::validation_exception::{pretty_py_line_errors, PyLineError};

pub type ValResult<'a, T> = Result<T, ValError<'a>>;

#[cfg_attr(debug_assertions, derive(Debug))]
pub enum ValError<'a> {
    LineErrors(Vec<ValLineError<'a>>),
    InternalErr(PyErr),
    Omit,
}

impl<'a> From<PyErr> for ValError<'a> {
    fn from(py_err: PyErr) -> Self {
        Self::InternalErr(py_err)
    }
}

impl<'a> From<PyDowncastError<'_>> for ValError<'a> {
    fn from(py_downcast: PyDowncastError) -> Self {
        Self::InternalErr(PyTypeError::new_err(py_downcast.to_string()))
    }
}

impl<'a> From<Vec<ValLineError<'a>>> for ValError<'a> {
    fn from(line_errors: Vec<ValLineError<'a>>) -> Self {
        Self::LineErrors(line_errors)
    }
}

impl<'a> ValError<'a> {
    pub fn new(error_type: ErrorType, input: &'a impl Input<'a>) -> ValError<'a> {
        Self::LineErrors(vec![ValLineError::new(error_type, input)])
    }

    pub fn new_with_loc(error_type: ErrorType, input: &'a impl Input<'a>, loc: impl Into<LocItem>) -> ValError<'a> {
        Self::LineErrors(vec![ValLineError::new_with_loc(error_type, input, loc)])
    }

    pub fn new_custom_input(error_type: ErrorType, input_value: InputValue<'a>) -> ValError<'a> {
        Self::LineErrors(vec![ValLineError::new_custom_input(error_type, input_value)])
    }

    /// helper function to call with_outer on line items if applicable
    pub fn with_outer_location(self, loc_item: LocItem) -> Self {
        match self {
            Self::LineErrors(mut line_errors) => {
                for line_error in line_errors.iter_mut() {
                    line_error.location.with_outer(loc_item.clone());
                }
                Self::LineErrors(line_errors)
            }
            other => other,
        }
    }

    /// a bit like clone but change the lifetime to match py
    pub fn duplicate<'py>(&self, py: Python<'py>) -> ValError<'py> {
        match self {
            ValError::LineErrors(errors) => errors.iter().map(|e| e.duplicate(py)).collect::<Vec<_>>().into(),
            ValError::InternalErr(err) => ValError::InternalErr(err.clone_ref(py)),
            ValError::Omit => ValError::Omit,
        }
    }
}

pub fn pretty_line_errors(py: Python, line_errors: Vec<ValLineError>) -> String {
    let py_line_errors: Vec<PyLineError> = line_errors.into_iter().map(|e| e.into_py(py)).collect();
    pretty_py_line_errors(py, py_line_errors.iter())
}

/// A `ValLineError` is a single error that occurred during validation which is converted to a `PyLineError`
/// to eventually form a `ValidationError`.
/// I don't like the name `ValLineError`, but it's the best I could come up with (for now).
#[cfg_attr(debug_assertions, derive(Debug))]
pub struct ValLineError<'a> {
    pub error_type: ErrorType,
    // location is reversed so that adding an "outer" location item is pushing, it's reversed before showing to the user
    pub location: Location,
    pub input_value: InputValue<'a>,
}

impl<'a> ValLineError<'a> {
    pub fn new(error_type: ErrorType, input: &'a impl Input<'a>) -> ValLineError<'a> {
        Self {
            error_type,
            input_value: input.as_error_value(),
            location: Location::default(),
        }
    }

    pub fn new_with_loc(error_type: ErrorType, input: &'a impl Input<'a>, loc: impl Into<LocItem>) -> ValLineError<'a> {
        Self {
            error_type,
            input_value: input.as_error_value(),
            location: Location::new_some(loc.into()),
        }
    }

    pub fn new_custom_input(error_type: ErrorType, input_value: InputValue<'a>) -> ValLineError<'a> {
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

    /// a bit like clone but change the lifetime to match py, used by ValError.duplicate above
    pub fn duplicate<'py>(&'a self, py: Python<'py>) -> ValLineError<'py> {
        ValLineError {
            error_type: self.error_type.clone(),
            input_value: InputValue::<'py>::from(self.input_value.to_object(py)),
            location: self.location.clone(),
        }
    }
}

#[cfg_attr(debug_assertions, derive(Debug))]
pub enum InputValue<'a> {
    PyAny(&'a PyAny),
    JsonInput(&'a JsonInput),
    String(&'a str),
    PyObject(PyObject),
}

impl<'a> From<PyObject> for InputValue<'a> {
    fn from(py_object: PyObject) -> Self {
        Self::PyObject(py_object)
    }
}

impl<'a> ToPyObject for InputValue<'a> {
    fn to_object(&self, py: Python) -> PyObject {
        match self {
            Self::PyAny(input) => input.into_py(py),
            Self::JsonInput(input) => input.to_object(py),
            Self::String(input) => input.into_py(py),
            Self::PyObject(py_obj) => py_obj.into_py(py),
        }
    }
}
