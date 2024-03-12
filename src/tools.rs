use std::borrow::Cow;

use pyo3::exceptions::PyKeyError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};
use pyo3::{ffi, intern, FromPyObject};

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

/// Extract an i64 from a python object more quickly, see
/// https://github.com/PyO3/pyo3/pull/3742#discussion_r1451763928
#[cfg(not(any(target_pointer_width = "32", windows, PyPy)))]
pub fn extract_i64(obj: &Bound<'_, PyAny>) -> Option<i64> {
    let val = unsafe { ffi::PyLong_AsLong(obj.as_ptr()) };
    if val == -1 && PyErr::occurred(obj.py()) {
        unsafe { ffi::PyErr_Clear() };
        None
    } else {
        Some(val)
    }
}

#[cfg(any(target_pointer_width = "32", windows, PyPy))]
pub fn extract_i64(v: &Bound<'_, PyAny>) -> Option<i64> {
    if v.is_instance_of::<pyo3::types::PyInt>() {
        v.extract().ok()
    } else {
        None
    }
}
