use std::borrow::Cow;
use std::marker::PhantomData;
use std::sync::atomic::{AtomicBool, AtomicUsize};
use std::sync::{Arc, OnceLock};

use ahash::{AHashMap, AHashSet};
use enum_dispatch::enum_dispatch;
use hashbrown::HashTable;
use num_bigint::BigInt;
use pyo3::{Py, PyTraverseError, PyVisit, pybacked::PyBackedStr};

/// Derives [`PyGcTraverse`], traversing every field not marked with `#[py_gc(skip)]`.
pub use pydantic_core_derive::PyGcTraverse;

/// Trait implemented by types which can be traversed by the Python GC.
#[enum_dispatch]
pub trait PyGcTraverse {
    fn py_gc_traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError>;
}

/// Implements a no-op [`PyGcTraverse`] for plain data types which can never hold
/// a strong reference to a Python object.
macro_rules! impl_py_gc_traverse_noop {
    ($($ty:ty),* $(,)?) => {
        $(
            impl PyGcTraverse for $ty {
                #[inline]
                fn py_gc_traverse(&self, _visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
                    Ok(())
                }
            }
        )*
    };
}

impl_py_gc_traverse_noop!(
    bool,
    u8,
    u16,
    u32,
    u64,
    u128,
    usize,
    i8,
    i16,
    i32,
    i64,
    i128,
    isize,
    f32,
    f64,
    char,
    String,
    AtomicBool,
    AtomicUsize,
    BigInt,
);

// Plain data types from external crates:
impl_py_gc_traverse_noop!(
    jiter::StringCacheMode,
    regex::Regex,
    speedate::Date,
    speedate::DateTime,
    speedate::Duration,
    speedate::MicrosecondsPrecisionOverflowBehavior,
    speedate::Time,
);

impl<A: smallvec::Array<Item = T>, T: PyGcTraverse> PyGcTraverse for smallvec::SmallVec<A> {
    fn py_gc_traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        for item in self {
            item.py_gc_traverse(visit)?;
        }
        Ok(())
    }
}

impl PyGcTraverse for Cow<'_, str> {
    #[inline]
    fn py_gc_traverse(&self, _visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        Ok(())
    }
}

impl<T> PyGcTraverse for PhantomData<T> {
    #[inline]
    fn py_gc_traverse(&self, _visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        Ok(())
    }
}

impl<A: PyGcTraverse, B: PyGcTraverse> PyGcTraverse for (A, B) {
    fn py_gc_traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        self.0.py_gc_traverse(visit)?;
        self.1.py_gc_traverse(visit)?;
        Ok(())
    }
}

impl<T: PyGcTraverse> PyGcTraverse for AHashSet<T> {
    fn py_gc_traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        for item in self {
            item.py_gc_traverse(visit)?;
        }
        Ok(())
    }
}

impl<T: PyGcTraverse> PyGcTraverse for OnceLock<T> {
    fn py_gc_traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        match self.get() {
            Some(item) => item.py_gc_traverse(visit),
            None => Ok(()),
        }
    }
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

impl<K: PyGcTraverse, V: PyGcTraverse> PyGcTraverse for AHashMap<K, V> {
    fn py_gc_traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        for (key, value) in self {
            key.py_gc_traverse(visit)?;
            value.py_gc_traverse(visit)?;
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
