use std::fmt;

use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::input::ToPy;

use super::kinds::ErrorKind;

/// Used to store individual items of the error location, e.g. a string for key/field names
/// or a number for array indices.
/// Note: ints are also used for keys of `Dict[int, ...]`
#[derive(Debug, Clone)]
pub enum LocItem {
    S(String),
    I(usize),
}
// we could use the From trait to make creating Location's much easier, would it be worth it?

impl fmt::Display for LocItem {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            LocItem::S(s) => write!(f, "{}", s),
            LocItem::I(i) => write!(f, "{}", i),
        }
    }
}

/// Error locations are represented by a vector of `LocItem`s.
/// e.g. if the error occurred in the third member of a list called `foo`,
/// the location would be `["foo", 2]`.
pub type Location = Vec<LocItem>;

/// A `ValLineError` is a single error that occurred during validation which is converted to a `PyLineError`
/// to eventually form a `ValidationError`.
/// I don't like the name `ValLineError`, but it's the best I could come up with (for now).
#[derive(Debug, Default)]
pub struct ValLineError<'a> {
    pub kind: ErrorKind,
    pub location: Location,
    pub message: Option<String>,
    pub input_value: InputValue<'a>,
    pub context: Context,
}

impl<'a> ValLineError<'a> {
    pub fn with_prefix_location(mut self, location: &Location) -> Self {
        if self.location.is_empty() {
            self.location = location.clone();
        } else {
            // TODO we could perhaps instead store "reverse_location" in the ValLineError, then reverse it in
            // `PyLineError` so we could just extend here.
            self.location = [location.clone(), self.location].concat();
        }
        self
    }
}

#[derive(Debug)]
pub enum InputValue<'a> {
    None,
    InputRef(&'a dyn ToPy),
    PyObject(PyObject),
}

impl Default for InputValue<'_> {
    fn default() -> Self {
        Self::None
    }
}

impl<'a> InputValue<'a> {
    pub fn to_py(&self, py: Python) -> PyObject {
        match self {
            Self::None => py.None(),
            Self::InputRef(input) => input.to_py(py),
            Self::PyObject(py_obj) => py_obj.into_py(py),
        }
    }
}

#[derive(Debug, Clone, Default)]
pub struct Context(Vec<(String, ContextValue)>);

impl Context {
    pub fn new<I: IntoIterator<Item = (String, ContextValue)>>(raw: I) -> Self {
        Self(raw.into_iter().collect())
    }

    pub fn is_empty(&self) -> bool {
        self.0.is_empty()
    }

    pub fn render(&self, template: String) -> String {
        let mut rendered = template;
        for (key, value) in &self.0 {
            rendered = rendered.replace(&format!("{{{}}}", key), &value.to_string());
        }
        rendered
    }
}

impl fmt::Display for Context {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let loc = self
            .0
            .iter()
            .map(|(k, v)| format!("{}: {}", k, v))
            .collect::<Vec<String>>()
            .join(", ");
        write!(f, "{{{}}}", loc)
    }
}

// maybe this is overkill and we should just use fmt::Display an convert to string when creating Context?
#[derive(Debug, Clone)]
pub enum ContextValue {
    S(String),
    I(i64),
    F(f64),
}

impl fmt::Display for ContextValue {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ContextValue::S(v) => write!(f, "{}", v),
            ContextValue::I(v) => write!(f, "{}", v),
            ContextValue::F(v) => write!(f, "{}", v),
        }
    }
}

impl From<String> for ContextValue {
    fn from(str: String) -> Self {
        Self::S(str)
    }
}

impl From<&str> for ContextValue {
    fn from(str: &str) -> Self {
        Self::S(str.to_string())
    }
}

impl From<i64> for ContextValue {
    fn from(int: i64) -> Self {
        Self::I(int)
    }
}

impl From<usize> for ContextValue {
    fn from(u: usize) -> Self {
        Self::I(u as i64)
    }
}

impl From<f64> for ContextValue {
    fn from(f: f64) -> Self {
        Self::F(f)
    }
}

impl ToPyObject for ContextValue {
    fn to_object(&self, py: Python) -> PyObject {
        match self {
            ContextValue::S(v) => v.into_py(py),
            ContextValue::I(v) => v.into_py(py),
            ContextValue::F(v) => v.into_py(py),
        }
    }
}

impl ToPyObject for Context {
    fn to_object(&self, py: Python) -> PyObject {
        let dict = PyDict::new(py);
        for (key, value) in &self.0 {
            dict.set_item(key, value).unwrap();
        }
        dict.into_py(py)
    }
}
