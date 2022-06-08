use std::result::Result as StdResult;

use pyo3::prelude::*;

use super::line_error::ValLineError;

pub type ValResult<'a, T> = StdResult<T, ValError<'a>>;

#[derive(Debug)]
pub enum ValError<'a> {
    LineErrors(Vec<ValLineError<'a>>),
    InternalErr(PyErr),
}

// ValError used to implement Error, see #78 for removed code

pub fn as_internal<'a>(err: PyErr) -> ValError<'a> {
    ValError::InternalErr(err)
}
