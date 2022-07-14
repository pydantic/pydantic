use pyo3::prelude::*;

use crate::input::{Input, JsonInput};

use super::kinds::ErrorKind;
use super::location::{LocItem, Location};
use super::validation_exception::{pretty_py_line_errors, PyLineError};

pub type ValResult<'a, T> = Result<T, ValError<'a>>;

#[derive(Debug)]
pub enum ValError<'a> {
    LineErrors(Vec<ValLineError<'a>>),
    InternalErr(PyErr),
}

impl<'a> From<PyErr> for ValError<'a> {
    fn from(py_err: PyErr) -> Self {
        Self::InternalErr(py_err)
    }
}

impl<'a> From<Vec<ValLineError<'a>>> for ValError<'a> {
    fn from(line_errors: Vec<ValLineError<'a>>) -> Self {
        Self::LineErrors(line_errors)
    }
}

impl<'a> ValError<'a> {
    pub fn new(kind: ErrorKind, input: &'a impl Input<'a>) -> ValError<'a> {
        Self::LineErrors(vec![ValLineError::new(kind, input)])
    }

    pub fn new_with_loc(kind: ErrorKind, input: &'a impl Input<'a>, loc: impl Into<LocItem>) -> ValError<'a> {
        Self::LineErrors(vec![ValLineError::new_with_loc(kind, input, loc)])
    }
}

pub fn pretty_line_errors(py: Python, line_errors: Vec<ValLineError>) -> String {
    let py_line_errors: Vec<PyLineError> = line_errors.into_iter().map(|e| e.into_py(py)).collect();
    pretty_py_line_errors(Some(py), py_line_errors.iter())
}

/// A `ValLineError` is a single error that occurred during validation which is converted to a `PyLineError`
/// to eventually form a `ValidationError`.
/// I don't like the name `ValLineError`, but it's the best I could come up with (for now).
#[derive(Debug)]
pub struct ValLineError<'a> {
    pub kind: ErrorKind,
    // location is reversed so that adding an "outer" location item is pushing, it's reversed before showing to the user
    pub location: Location,
    pub input_value: InputValue<'a>,
}

impl<'a> ValLineError<'a> {
    pub fn new(kind: ErrorKind, input: &'a impl Input<'a>) -> ValLineError<'a> {
        Self {
            kind,
            input_value: input.as_error_value(),
            location: Location::default(),
        }
    }

    pub fn new_with_loc(kind: ErrorKind, input: &'a impl Input<'a>, loc: impl Into<LocItem>) -> ValLineError<'a> {
        Self {
            kind,
            input_value: input.as_error_value(),
            location: Location::new_some(loc.into()),
        }
    }

    /// location is stored reversed so it's quicker to add "outer" items as that's what we always do
    /// hence `push` here instead of `insert`
    pub fn with_outer_location(mut self, loc_item: LocItem) -> Self {
        self.location.with_outer(loc_item);
        self
    }

    // change the kind on a error in place
    pub fn with_kind(mut self, kind: ErrorKind) -> Self {
        self.kind = kind;
        self
    }

    pub fn into_new<'b>(self, py: Python) -> ValLineError<'b> {
        ValLineError {
            kind: self.kind,
            location: self.location,
            input_value: self.input_value.to_object(py).into(),
        }
    }
}

#[derive(Debug)]
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
