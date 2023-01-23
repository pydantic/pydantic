use std::fmt;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use serde::ser;

/// `UNEXPECTED_TYPE_SER` is a special prefix to denote a `PydanticSerializationUnexpectedValue` error.
pub(super) static UNEXPECTED_TYPE_SER: &str = "__PydanticSerializationUnexpectedValue__";

// convert a `PyErr` or `PyDowncastError` into a serde serialization error
pub(super) fn py_err_se_err<T: ser::Error, E: fmt::Display>(py_error: E) -> T {
    T::custom(py_error.to_string())
}

/// convert a serde serialization error into a `PyErr`
pub(super) fn se_err_py_err(error: serde_json::Error) -> PyErr {
    let s = error.to_string();
    if let Some(msg) = s.strip_prefix(UNEXPECTED_TYPE_SER) {
        if msg.is_empty() {
            PydanticSerializationUnexpectedValue::new_err(None)
        } else {
            PydanticSerializationUnexpectedValue::new_err(Some(msg.to_string()))
        }
    } else {
        let msg = format!("Error serializing to JSON: {s}");
        PydanticSerializationError::new_err(msg)
    }
}

#[pyclass(extends=PyValueError, module="pydantic_core._pydantic_core")]
#[derive(Debug, Clone)]
pub struct PydanticSerializationError {
    message: String,
}

impl PydanticSerializationError {
    pub(crate) fn new_err(msg: String) -> PyErr {
        PyErr::new::<Self, String>(msg)
    }
}

#[pymethods]
impl PydanticSerializationError {
    #[new]
    fn py_new(message: String) -> Self {
        Self { message }
    }

    fn __str__(&self) -> &str {
        &self.message
    }

    pub fn __repr__(&self) -> String {
        format!("PydanticSerializationError({})", self.message)
    }
}

#[pyclass(extends=PyValueError, module="pydantic_core._pydantic_core")]
#[derive(Debug, Clone)]
pub struct PydanticSerializationUnexpectedValue {
    message: Option<String>,
}

impl PydanticSerializationUnexpectedValue {
    pub(crate) fn new_err(msg: Option<String>) -> PyErr {
        PyErr::new::<Self, Option<String>>(msg)
    }
}

#[pymethods]
impl PydanticSerializationUnexpectedValue {
    #[new]
    fn py_new(message: Option<String>) -> Self {
        Self { message }
    }

    fn __str__(&self) -> &str {
        match self.message {
            Some(ref s) => s,
            None => "Unexpected Value",
        }
    }

    pub(crate) fn __repr__(&self) -> String {
        format!("PydanticSerializationUnexpectedValue({})", self.__str__())
    }
}
