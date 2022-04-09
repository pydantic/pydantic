use std::fmt::Debug;

use pyo3::prelude::*;
use strum::{Display, EnumMessage};

#[derive(Debug, Display, EnumMessage)]
#[strum(serialize_all = "snake_case")]
pub enum ErrorType {
    #[strum(message = "Invalid value")]
    ValueError,
    #[strum(message = "Field required")]
    Missing,
    #[strum(message = "Extra fields are not permitted")]
    ExtraForbidden,
    #[strum(message = "'None' is not permitted")]
    NoneForbidden,
    #[strum(message = "Value is not a valid boolean")]
    Bool,
}

impl Default for ErrorType {
    fn default() -> Self {
        ErrorType::ValueError
    }
}

#[allow(dead_code)]
#[derive(Debug)]
pub enum ErrorLoc {
    Key(String),
    Index(usize),
}

#[pyclass]
#[derive(Debug, Default)]
pub struct SubError {
    error_type: ErrorType,
    location: Vec<ErrorLoc>,
    custom_message: Option<String>,
    context: Option<PyObject>,
    expected: Option<PyObject>,
    value_provided: Option<PyObject>,
}

impl SubError {
    pub fn from_error(error_type: ErrorType) -> Self {
        Self {
            error_type,
            ..Default::default()
        }
    }

    // pub fn from_msg(custom_message: String) -> Self {
    //     Self {
    //         custom_message: Some(custom_message),
    //         ..Default::default()
    //     }
    // }
}

#[pymethods]
impl SubError {
    #[getter]
    pub fn code(&self) -> String {
        self.error_type.to_string()
    }

    #[getter]
    pub fn loc(&self, py: Python) -> PyObject {
        let mut loc: Vec<PyObject> = Vec::with_capacity(self.location.len());
        for location in &self.location {
            let item: PyObject = match location {
                ErrorLoc::Key(key) => key.to_object(py),
                ErrorLoc::Index(index) => index.to_object(py),
            };
            loc.push(item);
        }
        loc.to_object(py)
    }

    #[getter]
    pub fn message(&self) -> String {
        // TODO string substitution
        if let Some(message) = &self.custom_message {
            message.to_string()
        } else {
            match self.error_type.get_message() {
                Some(message) => message.to_string(),
                None => self.code(),
            }
        }
    }

    #[getter]
    pub fn context(&self, py: Python) -> Option<PyObject> {
        self.context.as_ref().map(|c| c.to_object(py))
    }

    #[getter]
    pub fn expected(&self, py: Python) -> Option<PyObject> {
        self.expected.as_ref().map(|e| e.to_object(py))
    }

    #[getter]
    pub fn value_provided(&self, py: Python) -> Option<PyObject> {
        self.value_provided.as_ref().map(|v| v.to_object(py))
    }

    fn __repr__(&self) -> PyResult<String> {
        Ok(format!("{:?}", self))
    }
}
