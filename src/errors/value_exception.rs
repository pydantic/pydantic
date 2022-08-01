use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};

use crate::input::Input;

use super::{ErrorKind, ValError};

#[pyclass(extends=PyValueError, module="pydantic_core._pydantic_core")]
#[derive(Clone)]
#[cfg_attr(debug_assertions, derive(Debug))]
pub struct PydanticValueError {
    kind: String,
    message_template: String,
    context: Option<Py<PyDict>>,
}

#[pymethods]
impl PydanticValueError {
    #[new]
    fn py_new(py: Python, kind: String, message_template: String, context: Option<&PyDict>) -> Self {
        Self {
            kind,
            message_template,
            context: context.map(|c| c.into_py(py)),
        }
    }

    #[getter]
    pub fn kind(&self) -> String {
        self.kind.clone()
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
                if let Ok(py_str) = value.cast_as::<PyString>() {
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
            Some(ctx) => Ok(format!("{} [kind={}, context={}]", msg, self.kind, ctx.as_ref(py))),
            None => Ok(format!("{} [kind={}, context=None]", msg, self.kind)),
        }
    }
}

impl PydanticValueError {
    pub fn into_val_error<'a>(self, input: &'a impl Input<'a>) -> ValError<'a> {
        let kind = ErrorKind::CustomError { value_error: self };
        ValError::new(kind, input)
    }
}
