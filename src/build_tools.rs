use std::error::Error;
use std::fmt;

use pyo3::exceptions::PyException;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyString};
use pyo3::{intern, FromPyObject, PyErrArguments};

use crate::errors::{ErrorMode, ValError};
use crate::tools::SchemaDict;
use crate::ValidationError;

pub fn schema_or_config<'py, T>(
    schema: &'py PyDict,
    config: Option<&'py PyDict>,
    schema_key: &PyString,
    config_key: &PyString,
) -> PyResult<Option<T>>
where
    T: FromPyObject<'py>,
{
    match schema.get_as(schema_key)? {
        Some(v) => Ok(Some(v)),
        None => match config {
            Some(config) => config.get_as(config_key),
            None => Ok(None),
        },
    }
}

pub fn schema_or_config_same<'py, T>(
    schema: &'py PyDict,
    config: Option<&'py PyDict>,
    key: &PyString,
) -> PyResult<Option<T>>
where
    T: FromPyObject<'py>,
{
    schema_or_config(schema, config, key, key)
}

pub fn is_strict(schema: &PyDict, config: Option<&PyDict>) -> PyResult<bool> {
    let py = schema.py();
    Ok(schema_or_config_same(schema, config, intern!(py, "strict"))?.unwrap_or(false))
}

enum SchemaErrorEnum {
    Message(String),
    ValidationError(ValidationError),
}

// we could perhaps do clever things here to store each schema error, or have different types for the top
// level error group, and other errors, we could perhaps also support error groups!?
#[pyclass(extends=PyException, module="pydantic_core._pydantic_core")]
pub struct SchemaError(SchemaErrorEnum);

impl fmt::Debug for SchemaError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "SchemaError({:?})", self.message())
    }
}

impl fmt::Display for SchemaError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.message())
    }
}

impl Error for SchemaError {
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        None
    }
}

impl SchemaError {
    pub fn new_err<A>(args: A) -> PyErr
    where
        A: PyErrArguments + Send + Sync + 'static,
    {
        PyErr::new::<SchemaError, A>(args)
    }

    pub fn from_val_error(py: Python, error: ValError) -> PyErr {
        match error {
            ValError::LineErrors(raw_errors) => {
                let line_errors = raw_errors.into_iter().map(|e| e.into_py(py)).collect();
                let validation_error =
                    ValidationError::new(line_errors, "Schema".to_object(py), ErrorMode::Python, false);
                let schema_error = SchemaError(SchemaErrorEnum::ValidationError(validation_error));
                match Py::new(py, schema_error) {
                    Ok(err) => PyErr::from_value(err.into_ref(py)),
                    Err(err) => err,
                }
            }
            ValError::InternalErr(err) => err,
            ValError::Omit => Self::new_err("Unexpected Omit error."),
            ValError::UseDefault => Self::new_err("Unexpected UseDefault error."),
        }
    }

    fn message(&self) -> &str {
        match &self.0 {
            SchemaErrorEnum::Message(message) => message.as_str(),
            SchemaErrorEnum::ValidationError(_) => "<ValidationError>",
        }
    }
}

#[pymethods]
impl SchemaError {
    #[new]
    fn py_new(message: String) -> Self {
        Self(SchemaErrorEnum::Message(message))
    }

    fn error_count(&self) -> usize {
        match &self.0 {
            SchemaErrorEnum::Message(_) => 0,
            SchemaErrorEnum::ValidationError(error) => error.error_count(),
        }
    }

    fn errors(&self, py: Python) -> PyResult<Py<PyList>> {
        match &self.0 {
            SchemaErrorEnum::Message(_) => Ok(PyList::empty(py).into_py(py)),
            SchemaErrorEnum::ValidationError(error) => error.errors(py, false, false),
        }
    }

    fn __str__(&self, py: Python) -> String {
        match &self.0 {
            SchemaErrorEnum::Message(message) => message.clone(),
            SchemaErrorEnum::ValidationError(error) => error.display(py, Some("Invalid Schema:"), false),
        }
    }

    fn __repr__(&self, py: Python) -> String {
        match &self.0 {
            SchemaErrorEnum::Message(message) => format!("SchemaError({message:?})"),
            SchemaErrorEnum::ValidationError(error) => error.display(py, Some("Invalid Schema:"), false),
        }
    }
}

macro_rules! py_schema_error_type {
    ($msg:expr) => {
        crate::tools::py_error_type!(crate::build_tools::SchemaError; $msg)
    };
    ($msg:expr, $( $msg_args:expr ),+ ) => {
        crate::tools::py_error_type!(crate::build_tools::SchemaError; $msg, $( $msg_args ),+)
    };
}
pub(crate) use py_schema_error_type;

macro_rules! py_schema_err {
    ($msg:expr) => {
        Err(crate::build_tools::py_schema_error_type!($msg))
    };
    ($msg:expr, $( $msg_args:expr ),+ ) => {
        Err(crate::build_tools::py_schema_error_type!($msg, $( $msg_args ),+))
    };
}
pub(crate) use py_schema_err;

#[derive(Debug, Clone)]
pub(crate) enum ExtraBehavior {
    Allow,
    Forbid,
    Ignore,
}

impl ExtraBehavior {
    pub fn from_schema_or_config(
        py: Python,
        schema: &PyDict,
        config: Option<&PyDict>,
        default: Self,
    ) -> PyResult<Self> {
        let extra_behavior = schema_or_config::<Option<&str>>(
            schema,
            config,
            intern!(py, "extra_behavior"),
            intern!(py, "extra_fields_behavior"),
        )?
        .flatten();
        let res = match extra_behavior {
            Some("allow") => Self::Allow,
            Some("ignore") => Self::Ignore,
            Some("forbid") => Self::Forbid,
            Some(v) => return py_schema_err!("Invalid extra_behavior: `{}`", v),
            None => default,
        };
        Ok(res)
    }
}
