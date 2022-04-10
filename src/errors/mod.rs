use std::error::Error;
use std::fmt;
use std::result::Result as StdResult;

use pyo3::prelude::*;

mod kinds;
mod line_error;
mod validation_exception;

pub use self::kinds::ErrorKind;
pub use self::line_error::{LocItem, Location, ValLineError};
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
            ValError::LineErrors(errors) => {
                let count = errors.len();
                let plural = if count == 1 { "" } else { "s" };
                let loc = errors
                    .iter()
                    .map(|i| i.to_string())
                    .collect::<Vec<String>>()
                    .join("\n  ");
                write!(f, "{} validation error{}\n  {}", count, plural, loc)
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

macro_rules! val_error {
    ($py:ident, $value:expr) => {
        crate::errors::ValLineError {
            value: Some($value.to_object($py)),
            ..Default::default()
        }
    };

    ($py:ident, $value:expr, $($key:ident = $val:expr),+) => {
        crate::errors::ValLineError {
            value: Some($value.to_object($py)),
            $(
                $key: $val,
            )+
            ..Default::default()
        }
    };
}
pub(crate) use val_error;

macro_rules! err_val_error {
    ($py:ident, $value:expr) => {
        Err(crate::errors::ValError::LineErrors(vec![crate::errors::val_error!($py, $value)]))
    };

    ($py:ident, $value:expr, $($key:ident = $val:expr),+) => {
        Err(crate::errors::ValError::LineErrors(vec![crate::errors::val_error!($py, $value, $($key = $val),+)]))
    };
}
pub(crate) use err_val_error;

macro_rules! ok_or_internal {
    ($value:expr) => {
        match $value {
            Ok(v) => Ok(v),
            Err(e) => Err(crate::errors::ValError::InternalErr(e)),
        }
    };
}
pub(crate) use ok_or_internal;
