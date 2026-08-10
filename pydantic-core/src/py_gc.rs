use std::ffi::{c_int, c_void};
use std::mem::ManuallyDrop;
use std::sync::Arc;

use ahash::AHashMap;

use crate::tools::BuildHashMap;
use enum_dispatch::enum_dispatch;
use hashbrown::HashTable;
use pyo3::{Bound, Py, PyAny, PyTraverseError, PyVisit, Python, ffi, pybacked::PyBackedStr};

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

impl<K: PyGcTraverse, T: PyGcTraverse> PyGcTraverse for BuildHashMap<K, T> {
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

/// The Python references reported by an object's `tp_traverse`, recorded once so that the `__traverse__` of an
/// object whose references never change after construction (`SchemaValidator`, `SchemaSerializer`) can report
/// them again from a flat list instead of walking its whole (possibly large) Rust structure on every garbage
/// collection pass it takes part in.
///
/// The entries are *not* owned references (they are never dropped): each one is kept alive by the structure it
/// was recorded from, so a snapshot must be owned by (and dropped together with) the object it was taken of, and
/// only be taken of objects whose set of Python references is fixed for their whole lifetime.
pub struct PyGcSnapshot(Box<[ManuallyDrop<Py<PyAny>>]>);

impl PyGcSnapshot {
    /// Records the references `obj`'s `tp_traverse` currently reports, as many times as it reports them
    /// (i.e. exactly `gc.get_referents(obj)`); `None` if the type has no `tp_traverse`.
    pub fn take(obj: &Bound<'_, PyAny>) -> Option<Self> {
        struct Recorder<'py> {
            py: Python<'py>,
            refs: Vec<ManuallyDrop<Py<PyAny>>>,
        }

        unsafe extern "C" fn record(object: *mut ffi::PyObject, arg: *mut c_void) -> c_int {
            // SAFETY: `arg` is the `Recorder` handed to `traverse` below
            let recorder = unsafe { &mut *arg.cast::<Recorder<'_>>() };
            // SAFETY: `object` is a valid object referenced by `obj`; the `Py` created here does not own that
            // reference: it is never dropped (see `PyGcSnapshot`)
            let unowned = unsafe { Bound::from_owned_ptr(recorder.py, object) }.unbind();
            recorder.refs.push(ManuallyDrop::new(unowned));
            0
        }

        // SAFETY: `obj` is a valid object, so its type is a valid type object
        let slot = unsafe { ffi::PyType_GetSlot(ffi::Py_TYPE(obj.as_ptr()), ffi::Py_tp_traverse) };
        if slot.is_null() {
            return None;
        }
        // SAFETY: the `Py_tp_traverse` slot holds a `traverseproc`
        let traverse: ffi::traverseproc = unsafe { std::mem::transmute(slot) };
        let mut recorder = Recorder {
            py: obj.py(),
            refs: Vec::with_capacity(16),
        };
        // SAFETY: this is how the `gc` module itself calls `tp_traverse` (e.g. `gc.get_referents()`); `record`
        // matches `visitproc` and only uses `arg` as the `Recorder` passed here
        unsafe { traverse(obj.as_ptr(), record, (&raw mut recorder).cast()) };
        Some(Self(recorder.refs.into_boxed_slice()))
    }

    /// Visits the recorded references.
    pub fn traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        for obj in &self.0 {
            visit.call(&**obj)?;
        }
        Ok(())
    }
}

impl std::fmt::Debug for PyGcSnapshot {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "PyGcSnapshot({} refs)", self.0.len())
    }
}
