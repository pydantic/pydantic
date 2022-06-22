use pyo3::prelude::*;

mod datetime;
mod generics;
mod input_abstract;
mod input_json;
mod input_python;
mod parse_json;
mod return_enums;
mod shared;

pub(crate) use datetime::{
    pydate_as_date, pydatetime_as_datetime, pytime_as_time, EitherDate, EitherDateTime, EitherTime,
};
pub use generics::{GenericMapping, GenericSequence};
pub use input_abstract::Input;
pub use parse_json::{JsonInput, JsonObject};
pub use return_enums::{EitherBytes, EitherString};

pub fn repr_string(v: &PyAny) -> PyResult<String> {
    v.repr()?.extract()
}
