use std::str::from_utf8;

use crate::errors::{ok_or_internal, val_err, ErrorKind, ValResult};
use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyInt, PyString};

pub fn validate_str(py: Python, v: &PyAny) -> ValResult<String> {
    if let Ok(str) = v.cast_as::<PyString>() {
        ok_or_internal!(str.extract())
    } else if let Ok(bytes) = v.cast_as::<PyBytes>() {
        let str = match from_utf8(bytes.as_bytes()) {
            Ok(s) => s.to_string(),
            // TODO better error here
            Err(_) => return val_err!(py, v, kind = ErrorKind::Str),
        };
        Ok(str)
    } else if let Ok(int) = v.cast_as::<PyInt>() {
        // TODO remove unwrap
        let int = ok_or_internal!(i64::extract(int))?;
        Ok(int.to_string())
    } else if let Ok(float) = f64::extract(v) {
        // don't cast_as here so Decimals are covered - internally f64:extract uses PyFloat_AsDouble
        Ok(float.to_string())
    } else {
        // let name = v.get_type().name().unwrap_or("<unknown type>");
        val_err!(py, v, kind = ErrorKind::Str)
    }
}

#[pyfunction]
pub fn validate_str_py(py: Python, v: &PyAny) -> PyResult<String> {
    match validate_str(py, v) {
        Ok(s) => Ok(s),
        Err(_e) => todo!(),
    }
}
