use pyo3::exceptions::PyTypeError;
use pyo3::once_cell::GILOnceCell;
use std::fmt;

use pyo3::prelude::*;
use pyo3::types::{PyList, PyString, PyTuple};
use serde::ser::SerializeSeq;
use serde::{Serialize, Serializer};

use crate::lookup_key::{LookupPath, PathItem};
use crate::tools::extract_i64;

/// Used to store individual items of the error location, e.g. a string for key/field names
/// or a number for array indices.
#[derive(Clone)]
#[cfg_attr(debug_assertions, derive(Debug))]
pub enum LocItem {
    /// string type key, used to identify items from a dict or anything that implements `__getitem__`
    S(String),
    /// integer key, used to get:
    ///   * items from a list
    ///   * items from a tuple
    ///   * dict with int keys `Dict[int, ...]` (python only)
    ///   * with integer keys in tagged unions
    I(i64),
}

impl fmt::Display for LocItem {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::S(s) if s.contains('.') => write!(f, "`{s}`"),
            Self::S(s) => write!(f, "{s}"),
            Self::I(i) => write!(f, "{i}"),
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

impl From<i64> for LocItem {
    fn from(i: i64) -> Self {
        Self::I(i)
    }
}

impl From<usize> for LocItem {
    fn from(u: usize) -> Self {
        Self::I(u as i64)
    }
}

/// eventually it might be good to combine PathItem and LocItem
impl From<PathItem> for LocItem {
    fn from(path_item: PathItem) -> Self {
        match path_item {
            PathItem::S(s, _) => s.into(),
            PathItem::Pos(val) => val.into(),
            PathItem::Neg(val) => {
                let neg_value = -(val as i64);
                neg_value.into()
            }
        }
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

impl TryFrom<&PyAny> for LocItem {
    type Error = PyErr;

    fn try_from(loc_item: &PyAny) -> PyResult<Self> {
        if let Ok(py_str) = loc_item.downcast::<PyString>() {
            let str = py_str.to_str()?.to_string();
            Ok(Self::S(str))
        } else if let Ok(int) = extract_i64(loc_item) {
            Ok(Self::I(int))
        } else {
            Err(PyTypeError::new_err("Item in a location must be a string or int"))
        }
    }
}

impl Serialize for LocItem {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        match self {
            Self::S(s) => serializer.serialize_str(s.as_str()),
            Self::I(loc) => serializer.serialize_i64(*loc),
        }
    }
}

/// Error locations are represented by a vector of `LocItem`s.
/// e.g. if the error occurred in the third member of a list called `foo`,
/// the location would be `["foo", 2]`.
/// Note: location in List is stored in **REVERSE** so adding an "outer" item to location involves
/// pushing to the vec which is faster than inserting and shifting everything along.
/// Then when "using" location in `Display` and `ToPyObject` order has to be reversed
#[derive(Clone)]
#[cfg_attr(debug_assertions, derive(Debug))]
pub enum Location {
    // no location, avoid creating an unnecessary vec
    Empty,
    // store the in a vec of LocItems, Note: this is the REVERSE of location, see above
    // we could perhaps use a smallvec or similar here, probably only worth it if we store a Cow in LocItem
    List(Vec<LocItem>),
}

impl Default for Location {
    fn default() -> Self {
        Self::Empty
    }
}

static EMPTY_TUPLE: GILOnceCell<PyObject> = GILOnceCell::new();

impl ToPyObject for Location {
    fn to_object(&self, py: Python<'_>) -> PyObject {
        match self {
            Self::List(loc) => PyTuple::new(py, loc.iter().rev()).to_object(py),
            Self::Empty => EMPTY_TUPLE
                .get_or_init(py, || PyTuple::empty(py).to_object(py))
                .clone_ref(py),
        }
    }
}

impl From<&LookupPath> for Location {
    fn from(lookup_path: &LookupPath) -> Self {
        let v = lookup_path
            .iter()
            .rev()
            .map(|path_item| path_item.clone().into())
            .collect();
        Self::List(v)
    }
}

impl fmt::Display for Location {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::List(loc) => {
                let loc_str = loc.iter().rev().map(ToString::to_string).collect::<Vec<_>>();
                writeln!(f, "{}", loc_str.join("."))
            }
            Self::Empty => Ok(()),
        }
    }
}

impl Location {
    /// create a new location vec with a value, 3 is plucked out of thin air, should it just be 1?
    pub fn new_some(item: LocItem) -> Self {
        let mut loc = Vec::with_capacity(3);
        loc.push(item);
        Self::List(loc)
    }

    pub fn with_outer(&mut self, loc_item: LocItem) {
        match self {
            Self::List(ref mut loc) => loc.push(loc_item),
            Self::Empty => {
                *self = Self::new_some(loc_item);
            }
        };
    }
}

impl Serialize for Location {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        match self {
            Self::Empty => serializer.serialize_seq(Some(0))?.end(),
            Self::List(loc) => {
                let mut seq = serializer.serialize_seq(Some(loc.len()))?;
                for e in loc.iter().rev() {
                    seq.serialize_element(e)?;
                }
                seq.end()
            }
        }
    }
}

impl TryFrom<Option<&PyAny>> for Location {
    type Error = PyErr;

    /// Only ever called by ValidationError -> PyLineError to convert user input to our internal Location
    /// Thus this expects the location to *not* be reversed and reverses it before storing it.
    fn try_from(location: Option<&PyAny>) -> PyResult<Self> {
        if let Some(location) = location {
            let mut loc_vec: Vec<LocItem> = if let Ok(tuple) = location.downcast::<PyTuple>() {
                tuple.iter().map(LocItem::try_from).collect::<PyResult<_>>()?
            } else if let Ok(list) = location.downcast::<PyList>() {
                list.iter().map(LocItem::try_from).collect::<PyResult<_>>()?
            } else {
                return Err(PyTypeError::new_err(
                    "Location must be a list or tuple of strings and ints",
                ));
            };
            if loc_vec.is_empty() {
                Ok(Self::Empty)
            } else {
                // Don't force Python users to give use the location reversed
                // just be we internally store it like that
                loc_vec.reverse();
                Ok(Self::List(loc_vec))
            }
        } else {
            Ok(Self::Empty)
        }
    }
}
