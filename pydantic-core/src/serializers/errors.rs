use std::fmt;
use std::fmt::Write;

use pyo3::exceptions::{PyBaseException, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyString, PyTuple};
use pyo3::{PyTraverseError, PyVisit, intern};

use crate::tools::truncate_safe_repr;

use serde::ser;

/// `UNEXPECTED_TYPE_SER` is a special prefix to denote a `PydanticSerializationUnexpectedValue` error.
pub(super) static UNEXPECTED_TYPE_SER_MARKER: &str = "__PydanticSerializationUnexpectedValue__";
pub(super) static SERIALIZATION_ERR_MARKER: &str = "__PydanticSerializationError__";

// convert a `PyErr` or `PyDowncastError` into a serde serialization error
pub(super) fn py_err_se_err<T: ser::Error, E: fmt::Display>(py_error: E) -> T {
    T::custom(py_error.to_string())
}

/// Wrapper type which allows convenient conversion between `PyErr` and `ser::Error` in `?` expressions.
pub(crate) struct WrappedSerError<T: ser::Error>(pub T);

pub fn unwrap_ser_error<T: ser::Error>(wrapped: WrappedSerError<T>) -> T {
    wrapped.0
}

impl<T: ser::Error> From<PyErr> for WrappedSerError<T> {
    fn from(py_err: PyErr) -> Self {
        WrappedSerError(T::custom(py_err.to_string()))
    }
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

#[pyclass(extends=PyValueError, module="pydantic_core._pydantic_core", frozen)]
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
    pub(crate) fn new_err<T: Into<String>>(msg: T) -> PyErr {
        PyErr::new::<Self, String>(msg.into())
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

#[derive(Debug, Clone)]
enum UnexpectedValueMessage {
    Text(String),
    /// Errors encountered during (nested) union serialization, only formatted when the message is
    /// needed, as formatting them can be expensive.
    UnionErrors(Vec<Py<PyBaseException>>),
}

#[pyclass(extends=PyValueError, module="pydantic_core._pydantic_core", frozen)]
#[derive(Debug, Clone)]
pub struct PydanticSerializationUnexpectedValue {
    message: Option<UnexpectedValueMessage>,
    field_name: Option<Py<PyString>>,
    field_type: Option<String>,
    input_value: Option<Py<PyAny>>,
}

impl PydanticSerializationUnexpectedValue {
    pub fn new_from_msg(message: Option<String>) -> Self {
        Self {
            message: message.map(UnexpectedValueMessage::Text),
            field_name: None,
            field_type: None,
            input_value: None,
        }
    }

    /// Create an error from the errors encountered during union serialization.
    #[cold]
    pub fn new_from_union_errors(py: Python<'_>, errors: &[PyErr]) -> PyErr {
        let union_errors = errors.iter().map(|err| err.value(py).clone().unbind()).collect();
        let this = Self {
            message: Some(UnexpectedValueMessage::UnionErrors(union_errors)),
            field_name: None,
            field_type: None,
            input_value: None,
        };
        match Bound::new(py, this) {
            Ok(err) => PyErr::from_value(err.into_any()),
            Err(err) => err,
        }
    }

    pub fn new_from_parts(
        field_name: Option<Py<PyString>>,
        field_type: Option<String>,
        input_value: Option<Py<PyAny>>,
    ) -> Self {
        Self {
            message: None,
            field_name,
            field_type,
            input_value,
        }
    }

    pub fn new(
        message: Option<String>,
        field_name: Option<Py<PyString>>,
        field_type: Option<String>,
        input_value: Option<Py<PyAny>>,
    ) -> Self {
        Self {
            message: message.map(UnexpectedValueMessage::Text),
            field_name,
            field_type,
            input_value,
        }
    }

    /// The message of the error, formatting the union errors if any.
    fn message(&self, py: Python<'_>) -> Option<String> {
        match self.message.as_ref()? {
            UnexpectedValueMessage::Text(message) => Some(message.clone()),
            UnexpectedValueMessage::UnionErrors(errors) => Some(
                errors
                    .iter()
                    .map(|err| PyErr::from_value(err.bind(py).clone().into_any()).to_string())
                    .collect::<Vec<_>>()
                    .join("\n"),
            ),
        }
    }

    pub fn to_py_err(&self) -> PyErr {
        PyErr::new::<Self, _>((
            Python::attach(|py| self.message(py)),
            self.field_name.clone(),
            self.field_type.clone(),
            self.input_value.clone(),
        ))
    }
}

#[pymethods]
impl PydanticSerializationUnexpectedValue {
    #[new]
    #[pyo3(signature = (message=None, field_name=None, field_type=None, input_value=None, /))]
    fn py_new(
        message: Option<String>,
        field_name: Option<Py<PyString>>,
        field_type: Option<String>,
        input_value: Option<Py<PyAny>>,
    ) -> Self {
        Self {
            message: message.map(UnexpectedValueMessage::Text),
            field_name,
            field_type,
            input_value,
        }
    }

    pub(crate) fn __str__(&self, py: Python) -> String {
        let mut message = self.message(py).unwrap_or_default();

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

            if let Some(field_name) = &self.field_name {
                write!(
                    message,
                    " [field_name='{field_name}', input_value={value_str}, input_type={input_type}]"
                )
                .expect("writing to string should never fail");
            } else {
                write!(message, " [input_value={value_str}, input_type={input_type}]")
                    .expect("writing to string should never fail");
            }
        }

        if message.is_empty() {
            message = "Unexpected Value".to_string();
        }

        message
    }

    pub(crate) fn __repr__(&self, py: Python) -> String {
        format!("PydanticSerializationUnexpectedValue({})", self.__str__(py))
    }

    // Instances created from Rust don't go through `BaseException.__init__()` and have empty `args`,
    // so `BaseException.__reduce__()` can't be relied on:
    fn __reduce__<'py>(slf: &Bound<'py, Self>) -> PyResult<Bound<'py, PyTuple>> {
        let py = slf.py();
        let args = slf.getattr(intern!(py, "args"))?.cast_into::<PyTuple>()?;
        // Only use the stored values if `args` is empty, as `args` reflects the arguments
        // passed to (potentially overridden) `__new__()` implementations of subclasses:
        let args = if args.is_empty() {
            let this = slf.get();
            (this.message(py), &this.field_name, &this.field_type, &this.input_value).into_pyobject(py)?
        } else {
            args
        };
        match slf.getattr_opt(intern!(py, "__dict__"))? {
            // e.g. attributes set on subclass instances, or exception notes:
            Some(dict) if dict.is_truthy()? => (slf.get_type(), args, dict).into_pyobject(py),
            _ => (slf.get_type(), args).into_pyobject(py),
        }
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        if let Some(field_name) = &self.field_name {
            visit.call(field_name)?;
        }
        if let Some(input_value) = &self.input_value {
            visit.call(input_value)?;
        }
        if let Some(UnexpectedValueMessage::UnionErrors(errors)) = &self.message {
            for err in errors {
                visit.call(err)?;
            }
        }
        Ok(())
    }
}
