use pyo3::create_exception;
use std::fmt::Debug;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use strum::{Display, EnumMessage};

#[derive(Debug, Display, EnumMessage, Clone)]
#[strum(serialize_all = "snake_case")]
pub enum ErrorKind {
    #[strum(message = "Invalid value")]
    ValueError,
    #[strum(message = "Field required")]
    Missing,
    #[strum(message = "Extra fields are not permitted")]
    ExtraForbidden,
    #[strum(message = "'None' is not permitted")]
    NoneForbidden,
    #[strum(message = "Value must be 'None'")]
    NoneRequired,
    #[strum(message = "Value is not a valid boolean")]
    Bool,
    #[strum(message = "Dictionary must have at least {min_length} items")]
    DictTooShort,
    #[strum(message = "Dictionary must have at most {max_length} items")]
    DictTooLong,
}

impl Default for ErrorKind {
    fn default() -> Self {
        ErrorKind::ValueError
    }
}

#[pyclass]
#[derive(Debug, Default, Clone)]
pub struct ValLineError {
    pub kind: ErrorKind,
    pub location: Location,
    pub message: Option<String>,
    pub context: Option<PyObject>,
    pub expected: Option<PyObject>,
    pub value: Option<PyObject>,
}

#[pymethods]
impl ValLineError {
    #[getter]
    pub fn code(&self) -> String {
        self.kind.to_string()
    }

    #[getter]
    pub fn location(&self, py: Python) -> PyObject {
        let mut loc: Vec<PyObject> = Vec::with_capacity(self.location.len());
        for location in &self.location {
            let item: PyObject = match location {
                LocItem::Key(key) => key.to_object(py),
                LocItem::Index(index) => index.to_object(py),
            };
            loc.push(item);
        }
        loc.to_object(py)
    }

    #[getter]
    pub fn message(&self) -> String {
        // TODO string substitution
        if let Some(ref message) = self.message {
            message.to_string()
        } else {
            match self.kind.get_message() {
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
    pub fn value(&self, py: Python) -> Option<PyObject> {
        self.value.as_ref().map(|v| v.to_object(py))
    }

    fn __repr__(&self) -> PyResult<String> {
        Ok(format!("{:?}", self))
    }
}

#[derive(Debug, Clone)]
pub enum LocItem {
    Key(String),
    Index(usize),
}

pub type Location = Vec<LocItem>;

create_exception!(_pydantic_core, ValidationError, PyValueError);
// TODO impl ValidationError methods

pub enum ValResult {
    Ok(PyObject),
    VErr(Vec<ValLineError>),
    IErr(PyErr),
}
