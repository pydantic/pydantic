// TODO: remove this file once a new pyo3 version is released
// with https://github.com/PyO3/pyo3/pull/2358

use pyo3::{ffi, pyobject_native_type_core, PyAny};

/// Represents a Python `dict_keys`.
#[cfg(not(PyPy))]
#[repr(transparent)]
pub struct PyDictKeys(PyAny);

#[cfg(not(PyPy))]
pyobject_native_type_core!(
    PyDictKeys,
    ffi::PyDictKeys_Type,
    #checkfunction=ffi::PyDictKeys_Check
);

/// Represents a Python `dict_values`.
#[cfg(not(PyPy))]
#[repr(transparent)]
pub struct PyDictValues(PyAny);

#[cfg(not(PyPy))]
pyobject_native_type_core!(
    PyDictValues,
    ffi::PyDictValues_Type,
    #checkfunction=ffi::PyDictValues_Check
);
