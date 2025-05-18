use std::fmt;
use std::fmt::Write;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyString;

use crate::tools::truncate_safe_repr;

use serde::ser;

/// `UNEXPECTED_TYPE_SER` is a special prefix to denote a `PydanticSerializationUnexpectedValue` error.
pub(super) static UNEXPECTED_TYPE_SER_MARKER: &str = "__PydanticSerializationUnexpectedValue__";
pub(super) static SERIALIZATION_ERR_MARKER: &str = "__PydanticSerializationError__";

// convert a `PyErr` or `PyDowncastError` into a serde serialization error
pub(super) fn py_err_se_err<T: ser::Error, E: fmt::Display>(py_error: E) -> T {
    T::custom(py_error.to_string())
}

#[pyclass(extends=PyValueError, module="pydantic_core._pydantic_core")]
#[derive(Debug, Clone)]
pub struct PythonSerializerError {
    pub message: String,
}

impl fmt::Display for PythonSerializerError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.message)
    }
}

impl std::error::Error for PythonSerializerError {}

impl serde::ser::Error for PythonSerializerError {
    fn custom<T>(msg: T) -> Self
    where
        T: fmt::Display,
    {
        PythonSerializerError {
            message: format!("{msg}"),
        }
    }
}

/// convert a serde serialization error into a `PyErr`
pub(super) fn se_err_py_err(error: PythonSerializerError) -> PyErr {
    let s = error.to_string();
    if let Some(msg) = s.strip_prefix(UNEXPECTED_TYPE_SER_MARKER) {
        if msg.is_empty() {
            PydanticSerializationUnexpectedValue::new_from_msg(None).to_py_err()
        } else {
            PydanticSerializationUnexpectedValue::new_from_msg(Some(msg.to_string())).to_py_err()
        }
    } else if let Some(msg) = s.strip_prefix(SERIALIZATION_ERR_MARKER) {
        PydanticSerializationError::new_err(msg.to_string())
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

impl fmt::Display for PydanticSerializationError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.message)
    }
}

impl PydanticSerializationError {
    pub(crate) fn new_err(msg: String) -> PyErr {
        PyErr::new::<Self, String>(msg)
    }
}

#[pymethods]
impl PydanticSerializationError {
    #[new]
    #[pyo3(signature = (message, /))]
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
    field_type: Option<String>,
    input_value: Option<PyObject>,
}

impl PydanticSerializationUnexpectedValue {
    pub fn new_from_msg(message: Option<String>) -> Self {
        Self {
            message,
            field_type: None,
            input_value: None,
        }
    }

    pub fn new_from_parts(field_type: Option<String>, input_value: Option<PyObject>) -> Self {
        Self {
            message: None,
            field_type,
            input_value,
        }
    }

    pub fn new(message: Option<String>, field_type: Option<String>, input_value: Option<PyObject>) -> Self {
        Self {
            message,
            field_type,
            input_value,
        }
    }

    pub fn to_py_err(&self) -> PyErr {
        PyErr::new::<Self, (Option<String>, Option<String>, Option<PyObject>)>((
            self.message.clone(),
            self.field_type.clone(),
            self.input_value.clone(),
        ))
    }
}

#[pymethods]
impl PydanticSerializationUnexpectedValue {
    #[new]
    #[pyo3(signature = (message=None, field_type=None, input_value=None, /))]
    fn py_new(message: Option<String>, field_type: Option<String>, input_value: Option<PyObject>) -> Self {
        Self {
            message,
            field_type,
            input_value,
        }
    }

    pub(crate) fn __str__(&self, py: Python) -> String {
        let mut message = self.message.as_deref().unwrap_or("").to_string();

        if let Some(field_type) = &self.field_type {
            if !message.is_empty() {
                message.push_str(": ");
            }
            write!(message, "Expected `{field_type}`").expect("writing to string should never fail");
            if self.input_value.is_some() {
                message.push_str(" - serialized value may not be as expected");
            }
        }

        if let Some(input_value) = &self.input_value {
            let bound_input = input_value.bind(py);
            let input_type = bound_input
                .get_type()
                .name()
                .unwrap_or_else(|_| PyString::new(py, "<unknown python object>"))
                .to_string();

            let value_str = truncate_safe_repr(bound_input, None);

            write!(message, " [input_value={value_str}, input_type={input_type}]")
                .expect("writing to string should never fail");
        }

        if message.is_empty() {
            message = "Unexpected Value".to_string();
        }

        message
    }

    pub(crate) fn __repr__(&self, py: Python) -> String {
        format!("PydanticSerializationUnexpectedValue({})", self.__str__(py))
    }
}
