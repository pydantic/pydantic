use pyo3::prelude::*;

mod line_error;
mod location;
mod types;
mod validation_exception;
mod value_exception;

pub use self::line_error::{pretty_line_errors, InputValue, ValError, ValLineError, ValResult};
pub use self::location::LocItem;
pub use self::types::{list_all_errors, ErrorType};
pub use self::validation_exception::ValidationError;
pub use self::value_exception::{PydanticCustomError, PydanticKnownError, PydanticOmit};

pub fn py_err_string(py: Python, err: PyErr) -> String {
    let value = err.value(py);
    match value.get_type().name() {
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
