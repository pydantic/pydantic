//! Helpers for the `frozendict` builtin, which is only available on Python 3.15 and above.
//!
//! `PyFrozenDict` is only exposed by PyO3 when building for Python 3.15+, so these helpers
//! abstract over the `Py_3_15` cfg for the rest of the codebase.

use pyo3::prelude::*;
#[cfg(Py_3_15)]
use pyo3::types::PyFrozenDict;
use pyo3::types::PyMapping;

/// Whether the `frozendict` builtin type is available.
pub const FROZENDICT_AVAILABLE: bool = cfg!(Py_3_15);

/// The raw `frozendict` type pointer as a `usize`, or `0` when not available
/// (no Python type lives at address `0`, so comparisons against it never match).
#[cfg_attr(not(Py_3_15), allow(unused_variables))]
pub fn frozendict_type_raw(py: Python<'_>) -> usize {
    #[cfg(Py_3_15)]
    {
        use pyo3::type_object::PyTypeInfo;
        PyFrozenDict::type_object_raw(py) as usize
    }
    #[cfg(not(Py_3_15))]
    {
        0
    }
}

/// Returns `value` as a mapping if it is an instance of `frozendict` (or a subclass).
#[cfg_attr(not(Py_3_15), allow(unused_variables))]
pub fn as_frozendict<'a, 'py>(value: &'a Bound<'py, PyAny>) -> Option<&'a Bound<'py, PyMapping>> {
    #[cfg(Py_3_15)]
    {
        value.cast::<PyFrozenDict>().ok().map(PyFrozenDictMethods::as_mapping)
    }
    #[cfg(not(Py_3_15))]
    {
        None
    }
}

/// Creates a new `frozendict` from `mapping` (e.g. a `dict`).
#[cfg_attr(not(Py_3_15), allow(unused_variables))]
pub fn new_frozendict<'py>(mapping: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
    #[cfg(Py_3_15)]
    {
        PyFrozenDict::from_sequence(mapping).map(Bound::into_any)
    }
    #[cfg(not(Py_3_15))]
    {
        Err(pyo3::exceptions::PyRuntimeError::new_err(
            "The `frozendict` builtin type is only available on Python 3.15 and above",
        ))
    }
}

/// Iterates over the `(key, value)` pairs of `value`, which must be a `frozendict` (or a subclass).
#[cfg(Py_3_15)]
pub fn frozendict_items<'py>(
    value: &Bound<'py, PyAny>,
) -> PyResult<impl Iterator<Item = (Bound<'py, PyAny>, Bound<'py, PyAny>)>> {
    Ok(value.cast::<PyFrozenDict>()?.iter())
}

/// Iterates over the `(key, value)` pairs of `value`, which must be a `frozendict` (or a subclass).
#[cfg(not(Py_3_15))]
pub fn frozendict_items<'py>(
    _value: &Bound<'py, PyAny>,
) -> PyResult<std::iter::Empty<(Bound<'py, PyAny>, Bound<'py, PyAny>)>> {
    Err(pyo3::exceptions::PyRuntimeError::new_err(
        "The `frozendict` builtin type is only available on Python 3.15 and above",
    ))
}
