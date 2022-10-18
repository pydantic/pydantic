use std::os::raw::c_int;

use pyo3::prelude::*;

mod datetime;
mod input_abstract;
mod input_json;
mod input_python;
mod parse_json;
mod return_enums;
mod shared;

pub use datetime::{EitherDate, EitherDateTime, EitherTime, EitherTimedelta};
pub use input_abstract::Input;
pub use parse_json::{JsonInput, JsonObject, JsonType};
pub use return_enums::{
    py_string_str, EitherBytes, EitherString, GenericArguments, GenericCollection, GenericIterator, GenericMapping,
    JsonArgs, PyArgs,
};

pub fn repr_string(v: &PyAny) -> PyResult<String> {
    v.repr()?.extract()
}

// Defined here as it's not exported by pyo3
pub fn py_error_on_minusone(py: Python<'_>, result: c_int) -> PyResult<()> {
    if result != -1 {
        Ok(())
    } else {
        Err(PyErr::fetch(py))
    }
}
