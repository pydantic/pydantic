use pyo3::once_cell::GILOnceCell;
use std::fmt;

use pyo3::prelude::*;
use pyo3::types::PyTuple;

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

    fn try_from(value: &PyAny) -> PyResult<Self> {
        if let Ok(str) = value.extract::<String>() {
            Ok(str.into())
        } else {
            let int = value.extract::<usize>()?;
            Ok(int.into())
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

impl fmt::Display for Location {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::List(loc) => {
                let loc_str = loc.iter().rev().map(|i| i.to_string()).collect::<Vec<_>>();
                writeln!(f, "{}", loc_str.join(" -> "))
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
