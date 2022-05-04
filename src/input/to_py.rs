use std::fmt::Debug;

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyFrozenSet, PyList, PySet, PyTuple};

use super::parse_json::{JsonArray, JsonInput, JsonObject};

pub trait ToPy: Debug {
    fn to_py(&self, py: Python) -> PyObject;
}

impl ToPy for &JsonArray {
    #[inline]
    fn to_py(&self, py: Python) -> PyObject {
        self.iter().map(|v| v.to_py(py)).collect::<Vec<_>>().into_py(py)
    }
}

impl ToPy for &JsonObject {
    #[inline]
    fn to_py(&self, py: Python) -> PyObject {
        let dict = PyDict::new(py);
        for (k, v) in self.iter() {
            dict.set_item(k, v.to_py(py)).unwrap();
        }
        dict.into_py(py)
    }
}

impl ToPy for JsonInput {
    fn to_py(&self, py: Python) -> PyObject {
        match self {
            JsonInput::Null => py.None(),
            JsonInput::Bool(b) => b.into_py(py),
            JsonInput::Int(i) => i.into_py(py),
            JsonInput::Float(f) => f.into_py(py),
            JsonInput::String(s) => s.into_py(py),
            JsonInput::Array(v) => v.to_py(py),
            JsonInput::Object(o) => o.to_py(py),
        }
    }
}

impl ToPy for String {
    #[inline]
    fn to_py(&self, py: Python) -> PyObject {
        self.into_py(py)
    }
}

impl ToPy for PyAny {
    #[inline]
    fn to_py(&self, py: Python) -> PyObject {
        self.into_py(py)
    }
}

impl ToPy for &PyDict {
    #[inline]
    fn to_py(&self, py: Python) -> PyObject {
        self.into_py(py)
    }
}

impl ToPy for &PyList {
    #[inline]
    fn to_py(&self, py: Python) -> PyObject {
        self.into_py(py)
    }
}

impl ToPy for &PyTuple {
    #[inline]
    fn to_py(&self, py: Python) -> PyObject {
        self.into_py(py)
    }
}

impl ToPy for &PySet {
    #[inline]
    fn to_py(&self, py: Python) -> PyObject {
        self.into_py(py)
    }
}

impl ToPy for &PyFrozenSet {
    #[inline]
    fn to_py(&self, py: Python) -> PyObject {
        self.into_py(py)
    }
}
