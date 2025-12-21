use pyo3::prelude::*;
use pyo3::{PyTraverseError, PyVisit};
use smallvec::SmallVec;

use crate::lookup_key::{LookupPath, ValidationAlias};
use crate::py_gc::PyGcTraverse;

#[derive(Debug)]
pub enum Discriminator {
    /// use `LookupPaths` to find the tag, same as we do to find values in typed_dict aliases
    LookupPaths(SmallVec<[LookupPath; 1]>),
    /// call a function to find the tag to use
    Function(Py<PyAny>),
}

impl Discriminator {
    pub fn new(raw: &Bound<'_, PyAny>) -> PyResult<Self> {
        if raw.is_callable() {
            return Ok(Self::Function(raw.clone().unbind()));
        }

        let lookup: ValidationAlias = raw.extract()?;
        Ok(Self::LookupPaths(lookup.into_paths()))
    }

    pub fn to_string_py(&self, py: Python) -> PyResult<String> {
        match self {
            Self::Function(f) => Ok(format!("{}()", f.getattr(py, "__name__")?)),
            Self::LookupPaths(paths) => Ok(paths.iter().map(ToString::to_string).collect::<Vec<_>>().join(" | ")),
        }
    }
}

impl PyGcTraverse for Discriminator {
    fn py_gc_traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        match self {
            Self::Function(obj) => visit.call(obj)?,
            Self::LookupPaths(_) => {}
        }
        Ok(())
    }
}

pub(crate) const SMALL_UNION_THRESHOLD: usize = 4;
