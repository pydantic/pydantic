use std::fmt;

use pyo3::prelude::*;
use strum::EnumMessage;

use super::kinds::ErrorKind;

/// Used to store individual items of the error location, e.g. a string for key/field names
/// or a number for array indices.
#[derive(Debug, Clone)]
pub enum LocItem {
    K(String),
    I(usize),
}

impl fmt::Display for LocItem {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let s = match self {
            LocItem::K(s) => s.to_string(),
            LocItem::I(i) => i.to_string(),
        };
        write!(f, "{}", s)
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
    pub context: Option<PyObject>,
    pub expected: Option<PyObject>,
    pub value: Option<PyObject>,
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

#[pymethods]
impl ValLineError {
    #[getter]
    pub fn kind(&self) -> String {
        self.kind.to_string()
    }

    #[getter]
    pub fn location(&self, py: Python) -> PyObject {
        let mut loc: Vec<PyObject> = Vec::with_capacity(self.location.len());
        for location in &self.location {
            let item: PyObject = match location {
                LocItem::K(key) => key.to_object(py),
                LocItem::I(index) => index.to_object(py),
            };
            loc.push(item);
        }
        loc.to_object(py)
    }

    #[getter]
    pub fn message(&self) -> String {
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

    #[getter]
    pub fn context(&self, py: Python) -> Option<PyObject> {
        self.context.as_ref().map(|c| c.to_object(py))
    }

    #[getter]
    pub fn expected(&self, py: Python) -> Option<PyObject> {
        self.expected.as_ref().map(|e| e.to_object(py))
    }

    #[getter]
    pub fn value(&self, py: Python) -> Option<PyObject> {
        self.value.as_ref().map(|v| v.to_object(py))
    }

    fn __repr__(&self) -> PyResult<String> {
        Ok(format!("{:?}", self))
    }
}
