use core::fmt;
use std::borrow::Cow;

use pyo3::prelude::*;

mod line_error;
mod location;
mod types;
mod validation_exception;
mod value_exception;

pub use self::line_error::{InputValue, ToErrorValue, ValError, ValLineError, ValResult};
pub use self::location::LocItem;
pub use self::types::{list_all_errors, ErrorType, ErrorTypeDefaults, Number};
pub use self::validation_exception::ValidationError;
pub use self::value_exception::{PydanticCustomError, PydanticKnownError, PydanticOmit, PydanticUseDefault};

pub fn py_err_string(py: Python, err: PyErr) -> String {
    let value = err.value_bound(py);
    match value.get_type().qualname() {
        Ok(type_name) => match value.str() {
            Ok(py_str) => {
                let str_cow = py_str.to_string_lossy();
                let str = str_cow.as_ref();
                if !str.is_empty() {
                    format!("{type_name}: {str}")
                } else {
                    type_name.to_string()
                }
            }
            Err(_) => format!("{type_name}: <exception str() failed>"),
        },
        Err(_) => "Unknown Error".to_string(),
    }
}

// TODO: is_utf8_char_boundary, floor_char_boundary and ceil_char_boundary
// with builtin methods once https://github.com/rust-lang/rust/issues/93743 is resolved
// These are just copy pasted from the current implementation
const fn is_utf8_char_boundary(value: u8) -> bool {
    // This is bit magic equivalent to: b < 128 || b >= 192
    (value as i8) >= -0x40
}

pub fn floor_char_boundary(value: &str, index: usize) -> usize {
    if index >= value.len() {
        value.len()
    } else {
        let lower_bound = index.saturating_sub(3);
        let new_index = value.as_bytes()[lower_bound..=index]
            .iter()
            .rposition(|b| is_utf8_char_boundary(*b));

        // SAFETY: we know that the character boundary will be within four bytes
        unsafe { lower_bound + new_index.unwrap_unchecked() }
    }
}

pub fn ceil_char_boundary(value: &str, index: usize) -> usize {
    let upper_bound = Ord::min(index + 4, value.len());
    value.as_bytes()[index..upper_bound]
        .iter()
        .position(|b| is_utf8_char_boundary(*b))
        .map_or(upper_bound, |pos| pos + index)
}

pub fn write_truncated_to_50_bytes<F: fmt::Write>(f: &mut F, val: Cow<'_, str>) -> std::fmt::Result {
    if val.len() > 50 {
        write!(
            f,
            "{}...{}",
            &val[0..floor_char_boundary(&val, 25)],
            &val[ceil_char_boundary(&val, val.len() - 24)..]
        )
    } else {
        write!(f, "{val}")
    }
}
