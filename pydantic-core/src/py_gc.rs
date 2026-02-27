use std::sync::Arc;

use ahash::AHashMap;
use enum_dispatch::enum_dispatch;
use hashbrown::HashTable;
use pyo3::{Py, PyTraverseError, PyVisit, pybacked::PyBackedStr};

/// Trait implemented by types which can be traversed by the Python GC.
#[enum_dispatch]
pub trait PyGcTraverse {
    fn py_gc_traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError>;
}

impl<T> PyGcTraverse for Py<T> {
    fn py_gc_traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        visit.call(self)
    }
}

impl PyGcTraverse for PyBackedStr {
    fn py_gc_traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        visit.call(self.as_py_str())
    }
}

impl<T: PyGcTraverse> PyGcTraverse for Vec<T> {
    fn py_gc_traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        for item in self {
            item.py_gc_traverse(visit)?;
        }
        Ok(())
    }
}

impl<T: PyGcTraverse> PyGcTraverse for AHashMap<String, T> {
    fn py_gc_traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        for item in self.values() {
            item.py_gc_traverse(visit)?;
        }
        Ok(())
    }
}

impl<K: PyGcTraverse, T: PyGcTraverse> PyGcTraverse for AHashMap<K, T> {
    fn py_gc_traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        for item in self.values() {
            item.py_gc_traverse(visit)?;
        }
        Ok(())
    }
}

impl<T: PyGcTraverse> PyGcTraverse for Arc<T> {
    fn py_gc_traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        T::py_gc_traverse(self, visit)
    }
}

impl<T: PyGcTraverse> PyGcTraverse for Box<T> {
    fn py_gc_traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        T::py_gc_traverse(self, visit)
    }
}

impl<T: PyGcTraverse> PyGcTraverse for Option<T> {
    fn py_gc_traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        match self {
            Some(item) => T::py_gc_traverse(item, visit),
            None => Ok(()),
        }
    }
}

impl<T: PyGcTraverse> PyGcTraverse for HashTable<T> {
    fn py_gc_traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        self.iter().try_for_each(|item| item.py_gc_traverse(visit))
    }
}

/// A crude alternative to a "derive" macro to help with building PyGcTraverse implementations
macro_rules! impl_py_gc_traverse {
    ($name:ty { }) => {
        impl crate::py_gc::PyGcTraverse for $name {
            fn py_gc_traverse(&self, _visit: &pyo3::PyVisit<'_>) -> Result<(), pyo3::PyTraverseError> {
                Ok(())
            }
        }
    };
    ($name:ty { $($fields:ident),* $(,)? }) => {
        impl crate::py_gc::PyGcTraverse for $name {
            fn py_gc_traverse(&self, visit: &pyo3::PyVisit<'_>) -> Result<(), pyo3::PyTraverseError> {
                $(self.$fields.py_gc_traverse(visit)?;)*
                Ok(())
            }
        }
    };
}
