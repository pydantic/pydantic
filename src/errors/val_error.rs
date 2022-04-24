use std::error::Error;
use std::fmt;
use std::result::Result as StdResult;

use pyo3::prelude::*;

use super::line_error::ValLineError;

pub type ValResult<'a, T> = StdResult<T, ValError<'a>>;

#[derive(Debug)]
pub enum ValError<'a> {
    LineErrors(Vec<ValLineError<'a>>),
    InternalErr(PyErr),
}

impl<'a> fmt::Display for ValError<'a> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ValError::LineErrors(line_errors) => {
                write!(f, "Line errors: {:?}", line_errors)
            }
            ValError::InternalErr(err) => {
                write!(f, "Internal error: {}", err)
            }
        }
    }
}

impl<'a> Error for ValError<'a> {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            ValError::LineErrors(_errors) => None,
            ValError::InternalErr(err) => Some(err),
        }
    }
}

pub fn as_internal<'a>(err: PyErr) -> ValError<'a> {
    ValError::InternalErr(err)
}
