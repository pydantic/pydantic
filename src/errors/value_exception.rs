use pyo3::exceptions::{PyException, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};

use crate::input::Input;

use super::{ErrorType, ValError};

#[pyclass(extends=PyException, module="pydantic_core._pydantic_core")]
#[derive(Debug, Clone)]
pub struct PydanticOmit {}

impl PydanticOmit {
    pub(crate) fn new_err() -> PyErr {
        PyErr::new::<Self, ()>(())
    }
}

#[pymethods]
impl PydanticOmit {
    #[new]
    pub fn py_new() -> Self {
        Self {}
    }

    fn __str__(&self) -> &'static str {
        self.__repr__()
    }

    fn __repr__(&self) -> &'static str {
        "PydanticOmit()"
    }
}

#[pyclass(extends=PyValueError, module="pydantic_core._pydantic_core")]
#[derive(Debug, Clone, Default)]
pub struct PydanticCustomError {
    error_type: String,
    message_template: String,
    context: Option<Py<PyDict>>,
}

#[pymethods]
impl PydanticCustomError {
    #[new]
    pub fn py_new(py: Python, error_type: String, message_template: String, context: Option<&PyDict>) -> Self {
        Self {
            error_type,
            message_template,
            context: context.map(|c| c.into_py(py)),
        }
    }

    #[getter(type)]
    pub fn error_type(&self) -> String {
        self.error_type.clone()
    }

    #[getter]
    pub fn message_template(&self) -> String {
        self.message_template.clone()
    }

    #[getter]
    pub fn context(&self, py: Python) -> Option<Py<PyDict>> {
        self.context.as_ref().map(|c| c.clone_ref(py))
    }

    pub fn message(&self, py: Python) -> PyResult<String> {
        let mut message = self.message_template.clone();
        if let Some(ref context) = self.context {
            for item in context.as_ref(py).items().iter() {
                let (key, value): (&PyString, &PyAny) = item.extract()?;
                if let Ok(py_str) = value.downcast::<PyString>() {
                    message = message.replace(&format!("{{{}}}", key.to_str()?), py_str.to_str()?);
                } else if let Ok(value_int) = value.extract::<i64>() {
                    message = message.replace(&format!("{{{}}}", key.to_str()?), &value_int.to_string());
                } else {
                    // fallback for anything else just in case
                    message = message.replace(&format!("{{{}}}", key.to_str()?), &value.to_string());
                }
            }
        }
        Ok(message)
    }

    fn __str__(&self, py: Python) -> PyResult<String> {
        self.message(py)
    }

    fn __repr__(&self, py: Python) -> PyResult<String> {
        let msg = self.message(py)?;
        match { self.context.as_ref() } {
            Some(ctx) => Ok(format!("{msg} [type={}, context={}]", self.error_type, ctx.as_ref(py))),
            None => Ok(format!("{msg} [type={}, context=None]", self.error_type)),
        }
    }
}

impl PydanticCustomError {
    pub fn into_val_error<'a>(self, input: &'a impl Input<'a>) -> ValError<'a> {
        let error_type = ErrorType::CustomError { value_error: self };
        ValError::new(error_type, input)
    }
}

#[pyclass(extends=PyValueError, module="pydantic_core._pydantic_core")]
#[derive(Debug, Clone)]
pub struct PydanticKnownError {
    error_type: ErrorType,
}

#[pymethods]
impl PydanticKnownError {
    #[new]
    pub fn py_new(py: Python, error_type: &str, context: Option<&PyDict>) -> PyResult<Self> {
        let error_type = ErrorType::new(py, error_type, context)?;
        Ok(Self { error_type })
    }

    #[getter(type)]
    pub fn error_type(&self) -> String {
        self.error_type.to_string()
    }

    #[getter]
    pub fn message_template(&self) -> &'static str {
        self.error_type.message_template()
    }

    #[getter]
    pub fn context(&self, py: Python) -> PyResult<Option<Py<PyDict>>> {
        self.error_type.py_dict(py)
    }

    pub fn message(&self, py: Python) -> PyResult<String> {
        self.error_type.render_message(py)
    }

    fn __str__(&self, py: Python) -> PyResult<String> {
        self.message(py)
    }

    fn __repr__(&self, py: Python) -> PyResult<String> {
        let msg = self.message(py)?;
        match { self.context(py)?.as_ref() } {
            Some(ctx) => Ok(format!(
                "{msg} [type={}, context={}]",
                self.error_type(),
                ctx.as_ref(py)
            )),
            None => Ok(format!("{msg} [type={}, context=None]", self.error_type())),
        }
    }
}

impl PydanticKnownError {
    pub fn into_val_error<'a>(self, input: &'a impl Input<'a>) -> ValError<'a> {
        ValError::new(self.error_type, input)
    }
}
