use pyo3::prelude::*;
use pyo3::{PyTraverseError, PyVisit};

use crate::lookup_key::LookupKey;
use crate::py_gc::PyGcTraverse;

#[derive(Debug, Clone)]
pub enum Discriminator {
    /// use `LookupKey` to find the tag, same as we do to find values in typed_dict aliases
    LookupKey(LookupKey),
    /// call a function to find the tag to use
    Function(PyObject),
}

impl Discriminator {
    pub fn new(py: Python, raw: &Bound<'_, PyAny>) -> PyResult<Self> {
        if raw.is_callable() {
            return Ok(Self::Function(raw.to_object(py)));
        }

        let lookup_key = LookupKey::from_py(py, raw, None)?;
        Ok(Self::LookupKey(lookup_key))
    }

    pub fn to_string_py(&self, py: Python) -> PyResult<String> {
        match self {
            Self::Function(f) => Ok(format!("{}()", f.getattr(py, "__name__")?)),
            Self::LookupKey(lookup_key) => Ok(lookup_key.to_string()),
        }
    }
}

impl PyGcTraverse for Discriminator {
    fn py_gc_traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        match self {
            Self::Function(obj) => visit.call(obj)?,
            Self::LookupKey(_) => {}
        }
        Ok(())
    }
}

pub(crate) const SMALL_UNION_THRESHOLD: usize = 4;
