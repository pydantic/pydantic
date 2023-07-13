use std::os::raw::c_int;

use pyo3::prelude::*;

mod datetime;
mod input_abstract;
mod input_json;
mod input_python;
mod parse_json;
mod return_enums;
mod shared;

pub use datetime::TzInfo;
pub(crate) use datetime::{
    duration_as_pytimedelta, pydate_as_date, pydatetime_as_datetime, pytime_as_time, pytimedelta_as_duration,
    EitherDate, EitherDateTime, EitherTime, EitherTimedelta,
};
pub(crate) use input_abstract::{Input, InputType};
pub(crate) use parse_json::{JsonInput, JsonObject};
pub(crate) use return_enums::{
    py_string_str, AttributesGenericIterator, DictGenericIterator, EitherBytes, EitherFloat, EitherInt, EitherString,
    GenericArguments, GenericIterable, GenericIterator, GenericMapping, Int, JsonArgs, JsonObjectGenericIterator,
    MappingGenericIterator, PyArgs,
};

// Defined here as it's not exported by pyo3
pub fn py_error_on_minusone(py: Python<'_>, result: c_int) -> PyResult<()> {
    if result != -1 {
        Ok(())
    } else {
        Err(PyErr::fetch(py))
    }
}
