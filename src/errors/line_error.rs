use std::fmt;

use pyo3::prelude::*;
use strum::EnumMessage;

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

/// A `ValLineError` is a single error that occurred during validation which
/// combine to eventually form a `ValidationError`. I don't like the name `ValLineError`,
/// but it's the best I could come up with (for now).
#[pyclass]
#[derive(Debug, Default, Clone)]
pub struct ValLineError {
    pub kind: ErrorKind,
    pub location: Location,
    pub message: Option<String>,
    pub context: Option<Context>,
    pub expected: Option<PyObject>,
    pub input: Option<PyObject>,
}

impl fmt::Display for ValLineError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if !self.location.is_empty() {
            let loc = self
                .location
                .iter()
                .map(|i| i.to_string())
                .collect::<Vec<String>>()
                .join(" -> ");
            write!(f, "{} | ", loc)?;
        }
        write!(f, "{} (kind={})", self.message(), self.kind())
    }
}

impl ValLineError {
    // TODO in theory we could mutate the error since it won't be used again, but I
    // couldn't get mut to work on the result err.
    pub fn with_location(&self, location: &Location) -> ValLineError {
        let mut new = self.clone();
        if self.location.is_empty() {
            new.location = location.clone();
        } else {
            new.location = [location.clone(), new.location].concat();
        }
        new
    }
}

#[pymethods]
impl ValLineError {
    #[getter]
    fn kind(&self) -> String {
        self.kind.to_string()
    }

    #[getter]
    fn location(&self, py: Python) -> PyObject {
        let mut loc: Vec<PyObject> = Vec::with_capacity(self.location.len());
        for location in &self.location {
            let item: PyObject = match location {
                LocItem::S(key) => key.to_object(py),
                LocItem::I(index) => index.to_object(py),
            };
            loc.push(item);
        }
        loc.to_object(py)
    }

    fn message(&self) -> String {
        let raw = self.raw_message();
        match self.context {
            Some(ref context) => context.render(raw),
            None => raw,
        }
    }

    #[getter]
    fn raw_message(&self) -> String {
        // TODO string substitution
        if let Some(ref message) = self.message {
            message.to_string()
        } else {
            match self.kind.get_message() {
                Some(message) => message.to_string(),
                None => self.kind(),
            }
        }
    }

    // #[getter]
    // fn context(&self, py: Python) -> Option<PyObject> {
    //     self.context.as_ref().map(|c| c.to_object(py))
    // }

    #[getter]
    fn expected(&self, py: Python) -> Option<PyObject> {
        self.expected.as_ref().map(|e| e.to_object(py))
    }

    #[getter]
    fn input_value(&self, py: Python) -> Option<PyObject> {
        // could use something like this to get the input type
        // let name = v.get_type().name().unwrap_or("<unknown type>");
        self.input.as_ref().map(|v| v.to_object(py))
    }

    fn __repr__(&self) -> PyResult<String> {
        Ok(format!("{:?}", self))
    }
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct Context(Vec<(String, ContextValue)>);

impl Context {
    pub fn new<K: Into<String>, V: Into<ContextValue>, I: IntoIterator<Item = (K, V)>>(raw: I) -> Self {
        Self(raw.into_iter().map(|(k, v)| (k.into(), v.into())).collect())
    }

    pub fn render(&self, template: String) -> String {
        let mut rendered = template;
        for (key, value) in &self.0 {
            rendered = rendered.replace(&format!("{{{}}}", key), &value.to_string());
        }
        rendered
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
            ContextValue::S(s) => write!(f, "{}", s),
            ContextValue::I(i) => write!(f, "{}", i),
            ContextValue::F(v) => write!(f, "{}", v),
        }
    }
}

impl From<String> for ContextValue {
    fn from(str: String) -> Self {
        Self::S(str)
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
