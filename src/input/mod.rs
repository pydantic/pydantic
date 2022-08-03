use pyo3::prelude::*;

#[cfg(not(PyPy))]
mod _pyo3_dict;
mod datetime;
mod input_abstract;
mod input_json;
mod input_python;
mod parse_json;
mod return_enums;
mod shared;

pub use datetime::{EitherDate, EitherDateTime, EitherTime, EitherTimedelta};
pub use input_abstract::Input;
pub use parse_json::{JsonInput, JsonObject};
pub use return_enums::{
    py_string_str, EitherBytes, EitherString, GenericArguments, GenericListLike, GenericMapping, JsonArgs, PyArgs,
};

pub fn repr_string(v: &PyAny) -> PyResult<String> {
    v.repr()?.extract()
}
