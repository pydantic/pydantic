use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyString};

pub enum EitherString<'a> {
    Raw(String),
    Py(&'a PyString),
}

impl<'a> EitherString<'a> {
    pub fn as_raw(&self) -> PyResult<String> {
        match self {
            Self::Raw(date) => Ok(date.clone()),
            Self::Py(py_str) => py_str.extract(),
        }
    }
}

impl<'a> From<String> for EitherString<'a> {
    fn from(date: String) -> Self {
        Self::Raw(date)
    }
}

impl<'a> From<&'a PyString> for EitherString<'a> {
    fn from(date: &'a PyString) -> Self {
        Self::Py(date)
    }
}

impl<'a> IntoPy<PyObject> for EitherString<'a> {
    fn into_py(self, py: Python<'_>) -> PyObject {
        match self {
            EitherString::Raw(string) => PyString::new(py, &string).into_py(py),
            EitherString::Py(py_string) => py_string.into_py(py),
        }
    }
}

pub enum EitherBytes<'a> {
    Raw(Vec<u8>),
    Py(&'a PyBytes),
}

impl<'a> From<Vec<u8>> for EitherBytes<'a> {
    fn from(date: Vec<u8>) -> Self {
        Self::Raw(date)
    }
}

impl<'a> From<&'a PyBytes> for EitherBytes<'a> {
    fn from(date: &'a PyBytes) -> Self {
        Self::Py(date)
    }
}

impl<'a> EitherBytes<'a> {
    pub fn len(&'a self) -> PyResult<usize> {
        match self {
            EitherBytes::Raw(bytes) => Ok(bytes.len()),
            EitherBytes::Py(py_bytes) => py_bytes.len(),
        }
    }
}

impl<'a> IntoPy<PyObject> for EitherBytes<'a> {
    fn into_py(self, py: Python<'_>) -> PyObject {
        match self {
            EitherBytes::Raw(bytes) => PyBytes::new(py, &bytes).into_py(py),
            EitherBytes::Py(py_bytes) => py_bytes.into_py(py),
        }
    }
}
