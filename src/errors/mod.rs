use pyo3::prelude::*;

mod kinds;
mod line_error;
pub mod location;
mod validation_exception;

pub use self::kinds::ErrorKind;
pub use self::line_error::{as_internal, pretty_line_errors, Context, InputValue, ValError, ValLineError, ValResult};
pub use self::validation_exception::ValidationError;

/// Utility for concisely creating a `ValLineError`
/// can either take just `py` and a `value` (the given value) in which case kind `ErrorKind::ValueError` is used as kind
/// e.g. `val_line_error!(py, "the value provided")`
/// or, `py`, `value` and a mapping of other attributes for `ValLineError`
/// e.g. `val_line_error!(py, "the value provided", kind=ErrorKind::ExtraForbidden, message="the message")`
macro_rules! val_line_error {
    ($($key:ident = $val:expr),+ $(,)?) => {
        crate::errors::ValLineError {
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
    ($($key:ident = $val:expr),+ $(,)?) => {
        Err(crate::errors::ValError::LineErrors(vec![crate::errors::val_line_error!($($key = $val),+)]))
    };
}
pub(crate) use err_val_error;

macro_rules! context {
    ($($k:expr => $v:expr),* $(,)?) => {{
        crate::errors::Context::new([$(($k.into(), $v.into()),)*])
    }};
}
pub(crate) use context;

pub fn py_err_string(py: Python, err: PyErr) -> String {
    let value = err.value(py);
    match value.get_type().name() {
        Ok(type_name) => match value.str() {
            Ok(py_str) => {
                let str_cow = py_str.to_string_lossy();
                let str = str_cow.as_ref();
                if !str.is_empty() {
                    format!("{}: {}", type_name, str)
                } else {
                    type_name.to_string()
                }
            }
            Err(_) => format!("{}: <exception str() failed>", type_name),
        },
        Err(_) => "Unknown Error".to_string(),
    }
}
