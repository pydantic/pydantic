use ahash::AHashMap;
use enum_dispatch::enum_dispatch;
use pyo3::{AsPyPointer, Py, PyTraverseError, PyVisit};

/// Trait implemented by types which can be traversed by the Python GC.
#[enum_dispatch]
pub trait PyGcTraverse {
    fn py_gc_traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError>;
}

impl<T> PyGcTraverse for Py<T>
where
    Py<T>: AsPyPointer,
{
    fn py_gc_traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        visit.call(self)
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

/// A crude alternative to a "derive" macro to help with building PyGcTraverse implementations
macro_rules! impl_py_gc_traverse {
    ($name:ty { }) => {
        impl crate::py_gc::PyGcTraverse for $name {
            fn py_gc_traverse(&self, _visit: &pyo3::PyVisit<'_>) -> Result<(), pyo3::PyTraverseError> {
                Ok(())
            }
        }
    };
    ($name:ty { $($fields:ident),* }) => {
        impl crate::py_gc::PyGcTraverse for $name {
            fn py_gc_traverse(&self, visit: &pyo3::PyVisit<'_>) -> Result<(), pyo3::PyTraverseError> {
                $(self.$fields.py_gc_traverse(visit)?;)*
                Ok(())
            }
        }
    };
}
