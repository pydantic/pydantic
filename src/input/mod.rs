use std::os::raw::c_int;

use pyo3::prelude::*;

mod datetime;
mod input_abstract;
mod input_json;
mod input_python;
mod input_string;
mod return_enums;
mod shared;

pub use datetime::TzInfo;
pub(crate) use datetime::{
    duration_as_pytimedelta, pydate_as_date, pydatetime_as_datetime, pytime_as_time, EitherDate, EitherDateTime,
    EitherTime, EitherTimedelta,
};
pub(crate) use input_abstract::{
    Arguments, BorrowInput, ConsumeIterator, Input, InputType, KeywordArgs, PositionalArgs, ValidatedDict,
    ValidatedList, ValidatedSet, ValidatedTuple,
};
pub(crate) use input_string::StringMapping;
pub(crate) use return_enums::{
    no_validator_iter_to_vec, py_string_str, validate_iter_to_set, validate_iter_to_vec, EitherBytes, EitherFloat,
    EitherInt, EitherString, GenericIterator, Int, MaxLengthCheck, ValidationMatch,
};

// Defined here as it's not exported by pyo3
pub fn py_error_on_minusone(py: Python<'_>, result: c_int) -> PyResult<()> {
    if result != -1 {
        Ok(())
    } else {
        Err(PyErr::fetch(py))
    }
}
