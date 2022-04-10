use std::error::Error;
use std::fmt;
use std::result::Result as StdResult;

use pyo3::prelude::*;
use strum::EnumMessage;

mod kinds;
mod validation_exception;

pub use self::kinds::ErrorKind;
pub use self::validation_exception::ValidationError;

#[derive(Debug, Clone)]
pub enum LocItem {
    Key(String),
    Index(usize),
}

pub type Location = Vec<LocItem>;

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

macro_rules! val_err {
    ($py:ident, $value:expr) => {
        Err(crate::errors::ValError::LineErrors(vec![crate::errors::ValLineError {
            value: Some($value.to_object($py)),
            ..Default::default()
        }]))
    };

    ($py:ident, $value:expr, $($key:ident = $val:expr),+) => {
        Err(crate::errors::ValError::LineErrors(vec![crate::errors::ValLineError {
            value: Some($value.to_object($py)),
            $(
                $key: $val,
            )+
            ..Default::default()
        }]))
    };
}
pub(crate) use val_err;

macro_rules! ok_or_internal {
    ($value:expr) => {
        match $value {
            Ok(v) => Ok(v),
            Err(e) => Err(crate::errors::ValError::InternalErr(e)),
        }
    };
}
pub(crate) use ok_or_internal;

#[derive(Debug)]
pub enum ValError {
    LineErrors(Vec<ValLineError>),
    InternalErr(PyErr),
}

impl fmt::Display for ValError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{:?}", self)
    }
}

impl Error for ValError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            ValError::LineErrors(_errors) => None,
            ValError::InternalErr(err) => Some(err),
        }
    }
}

pub type ValResult<T> = StdResult<T, ValError>;
