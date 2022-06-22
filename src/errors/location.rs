use std::fmt;

use pyo3::prelude::*;

/// Used to store individual items of the error location, e.g. a string for key/field names
/// or a number for array indices.
#[derive(Debug, Clone)]
pub enum LocItem {
    /// string type key, used to identify items from a dict or anything that implements `__getitem__`
    S(String),
    /// integer key, used to get items from a list, tuple OR a dict with int keys `Dict[int, ...]` (python only)
    I(usize),
}

impl fmt::Display for LocItem {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::S(s) => write!(f, "{}", s),
            Self::I(i) => write!(f, "{}", i),
        }
    }
}

impl From<String> for LocItem {
    fn from(s: String) -> Self {
        Self::S(s)
    }
}

impl From<&str> for LocItem {
    fn from(s: &str) -> Self {
        Self::S(s.to_string())
    }
}

impl From<usize> for LocItem {
    fn from(i: usize) -> Self {
        Self::I(i)
    }
}

impl ToPyObject for LocItem {
    fn to_object(&self, py: Python<'_>) -> PyObject {
        match self {
            Self::S(val) => val.to_object(py),
            Self::I(val) => val.to_object(py),
        }
    }
}

/// Error locations are represented by a vector of `LocItem`s.
/// e.g. if the error occurred in the third member of a list called `foo`,
/// the location would be `["foo", 2]`.
pub type Location = Vec<LocItem>;
