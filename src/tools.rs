use std::borrow::Cow;

use pyo3::exceptions::PyKeyError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};
use pyo3::{intern, FromPyObject};

use jiter::{cached_py_string, pystring_fast_new, StringCacheMode};

pub trait SchemaDict<'py> {
    fn get_as<T>(&self, key: &Bound<'_, PyString>) -> PyResult<Option<T>>
    where
        T: FromPyObject<'py>;

    fn get_as_req<T>(&self, key: &Bound<'_, PyString>) -> PyResult<T>
    where
        T: FromPyObject<'py>;
}

impl<'py> SchemaDict<'py> for Bound<'py, PyDict> {
    fn get_as<T>(&self, key: &Bound<'_, PyString>) -> PyResult<Option<T>>
    where
        T: FromPyObject<'py>,
    {
        match self.get_item(key)? {
            Some(t) => t.extract().map(Some),
            None => Ok(None),
        }
    }

    fn get_as_req<T>(&self, key: &Bound<'_, PyString>) -> PyResult<T>
    where
        T: FromPyObject<'py>,
    {
        match self.get_item(key)? {
            Some(t) => t.extract(),
            None => py_err!(PyKeyError; "{}", key),
        }
    }
}

impl<'py> SchemaDict<'py> for Option<&Bound<'py, PyDict>> {
    fn get_as<T>(&self, key: &Bound<'_, PyString>) -> PyResult<Option<T>>
    where
        T: FromPyObject<'py>,
    {
        match self {
            Some(d) => d.get_as(key),
            None => Ok(None),
        }
    }

    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn get_as_req<T>(&self, key: &Bound<'_, PyString>) -> PyResult<T>
    where
        T: FromPyObject<'py>,
    {
        match self {
            Some(d) => d.get_as_req(key),
            None => py_err!(PyKeyError; "{}", key),
        }
    }
}

macro_rules! py_error_type {
    ($error_type:ty; $msg:expr) => {
        <$error_type>::new_err($msg)
    };

    ($error_type:ty; $msg:expr, $( $msg_args:expr ),+ ) => {
        <$error_type>::new_err(format!($msg, $( $msg_args ),+))
    };
}
pub(crate) use py_error_type;

macro_rules! py_err {
    ($error_type:ty; $msg:expr) => {
        Err(crate::tools::py_error_type!($error_type; $msg))
    };

    ($error_type:ty; $msg:expr, $( $msg_args:expr ),+ ) => {
        Err(crate::tools::py_error_type!($error_type; $msg, $( $msg_args ),+))
    };
}
pub(crate) use py_err;

pub fn function_name(f: &Bound<'_, PyAny>) -> PyResult<String> {
    match f.getattr(intern!(f.py(), "__name__")) {
        Ok(name) => name.extract(),
        _ => f.repr()?.extract(),
    }
}

pub enum ReprOutput<'py> {
    Python(Bound<'py, PyString>),
    Fallback(String),
}

impl ReprOutput<'_> {
    pub fn to_cow(&self) -> Cow<'_, str> {
        match self {
            ReprOutput::Python(s) => s.to_string_lossy(),
            ReprOutput::Fallback(s) => s.into(),
        }
    }
}

impl std::fmt::Display for ReprOutput<'_> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ReprOutput::Python(s) => write!(f, "{}", s.to_string_lossy()),
            ReprOutput::Fallback(s) => write!(f, "{s}"),
        }
    }
}

pub fn safe_repr<'py>(v: &Bound<'py, PyAny>) -> ReprOutput<'py> {
    if let Ok(s) = v.repr() {
        ReprOutput::Python(s)
    } else if let Ok(name) = v.get_type().qualname() {
        ReprOutput::Fallback(format!("<unprintable {name} object>"))
    } else {
        ReprOutput::Fallback("<unprintable object>".to_owned())
    }
}

pub fn extract_i64(v: &Bound<'_, PyAny>) -> Option<i64> {
    #[cfg(PyPy)]
    if !v.is_instance_of::<pyo3::types::PyInt>() {
        // PyPy used __int__ to cast floats to ints after CPython removed it,
        // see https://github.com/pypy/pypy/issues/4949
        //
        // Can remove this after PyPy 7.3.17 is released
        return None;
    }

    v.extract().ok()
}

pub(crate) fn new_py_string<'py>(py: Python<'py>, s: &str, cache_str: StringCacheMode) -> Bound<'py, PyString> {
    // we could use `bytecount::num_chars(s.as_bytes()) == s.len()` as orjson does, but it doesn't appear to be faster
    let ascii_only = false;
    if matches!(cache_str, StringCacheMode::All) {
        cached_py_string(py, s, ascii_only)
    } else {
        pystring_fast_new(py, s, ascii_only)
    }
}
