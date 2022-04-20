use std::error::Error;
use std::fmt;
use std::result::Result as StdResult;

use pyo3::prelude::*;

mod kinds;
mod line_error;
mod validation_exception;

use self::validation_exception::display_errors;

pub use self::kinds::ErrorKind;
pub use self::line_error::{Context, LocItem, Location, ValLineError};
pub use self::validation_exception::ValidationError;

pub type ValResult<T> = StdResult<T, ValError>;

#[derive(Debug)]
pub enum ValError {
    LineErrors(Vec<ValLineError>),
    InternalErr(PyErr),
}

impl fmt::Display for ValError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ValError::LineErrors(line_errors) => {
                write!(f, "{}", display_errors(line_errors, "Model", None))
            }
            ValError::InternalErr(err) => {
                write!(f, "Internal error: {}", err)
            }
        }
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

pub fn as_internal(err: PyErr) -> ValError {
    ValError::InternalErr(err)
}

pub fn map_validation_error(model_name: &str, error: ValError) -> PyErr {
    match error {
        ValError::LineErrors(line_errors) => ValidationError::new_err((line_errors, model_name.to_string())),
        ValError::InternalErr(err) => err,
    }
}

/// Utility for concisely creating a `ValLineError`
/// can either take just `py` and a `value` (the given value) in which case kind `ErrorKind::ValueError` is used as kind
/// e.g. `val_line_error!(py, "the value provided")`
/// or, `py`, `value` and a mapping of other attributes for `ValLineError`
/// e.g. `val_line_error!(py, "the value provided", kind=ErrorKind::ExtraForbidden, message="the message")`
macro_rules! val_line_error {
    ($py:ident, $input:expr) => {
        crate::errors::ValLineError {
            input_value: Some($input.into_py($py)),
            ..Default::default()
        }
    };

    ($py:ident, $input:expr, $($key:ident = $val:expr),+) => {
        crate::errors::ValLineError {
            input_value: Some($input.to_py($py)),
            $(
                $key: $val,
            )+
            ..Default::default()
        }
    };
}
pub(crate) use val_line_error;

/// Utility for concisely creating a `Err(ValError::LineErrors([?]))` containing a single `ValLineError`
/// Usage matches `val_line_error`
macro_rules! err_val_error {
    ($py:ident, $input:expr) => {
        Err(crate::errors::ValError::LineErrors(vec![crate::errors::val_line_error!($py, $input)]))
    };

    ($py:ident, $input:expr, $($key:ident = $val:expr),+) => {
        Err(crate::errors::ValError::LineErrors(vec![crate::errors::val_line_error!($py, $input, $($key = $val),+)]))
    };
}
pub(crate) use err_val_error;

macro_rules! context {
    ($($k:expr => $v:expr),*) => {{
        Some(crate::errors::Context::new([$(($k, $v),)*]))
    }};
}
pub(crate) use context;
