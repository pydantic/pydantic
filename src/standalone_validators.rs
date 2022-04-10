use std::str::from_utf8;

use crate::errors::{err_val_error, ok_or_internal, ErrorKind, ValResult};
use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict, PyInt, PyString};

pub fn validate_str(py: Python, v: &PyAny) -> ValResult<String> {
    if let Ok(str) = v.cast_as::<PyString>() {
        ok_or_internal!(str.extract())
    } else if let Ok(bytes) = v.cast_as::<PyBytes>() {
        let str = match from_utf8(bytes.as_bytes()) {
            Ok(s) => s.to_string(),
            Err(_) => return err_val_error!(py, v, kind = ErrorKind::StrUnicode),
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
        err_val_error!(py, v, kind = ErrorKind::StrType)
    }
}

#[pyfunction]
pub fn validate_str_py(py: Python, v: &PyAny) -> PyResult<String> {
    match validate_str(py, v) {
        Ok(s) => Ok(s),
        Err(_e) => todo!(),
    }
}

pub fn validate_dict<'py>(py: Python<'py>, v: &'py PyAny) -> ValResult<&'py PyDict> {
    if let Ok(dict) = v.cast_as::<PyDict>() {
        Ok(dict)
        // TODO we probably want to try and support mapping like things here too
    } else {
        err_val_error!(py, v, kind = ErrorKind::DictType)
    }
}

pub fn validate_int<'py>(py: Python<'py>, v: &'py PyAny) -> ValResult<i64> {
    if let Ok(int) = v.extract::<i64>() {
        Ok(int)
    } else if let Ok(str) = v.extract::<String>() {
        match str.parse() {
            Ok(i) => Ok(i),
            Err(_) => err_val_error!(py, str, kind = ErrorKind::IntParsing),
        }
    } else if let Ok(bytes) = v.cast_as::<PyBytes>() {
        let str = match from_utf8(bytes.as_bytes()) {
            Ok(s) => s.to_string(),
            Err(_) => return err_val_error!(py, bytes, kind = ErrorKind::IntParsing),
        };
        match str.parse() {
            Ok(i) => Ok(i),
            Err(_) => err_val_error!(py, str, kind = ErrorKind::IntParsing),
        }
    } else if let Ok(float) = validate_float(py, v) {
        if float % 1.0 == 0.0 {
            Ok(float as i64)
        } else {
            err_val_error!(py, float, kind = ErrorKind::IntFromFloat)
        }
    } else {
        err_val_error!(py, v, kind = ErrorKind::IntType)
    }
}

pub fn validate_float<'py>(py: Python<'py>, v: &'py PyAny) -> ValResult<f64> {
    if let Ok(int) = v.extract::<f64>() {
        Ok(int)
    } else if let Ok(str) = v.extract::<String>() {
        match str.parse() {
            Ok(i) => Ok(i),
            Err(_) => err_val_error!(py, str, kind = ErrorKind::FloatParsing),
        }
    } else if let Ok(bytes) = v.cast_as::<PyBytes>() {
        let str = match from_utf8(bytes.as_bytes()) {
            Ok(s) => s.to_string(),
            Err(_) => return err_val_error!(py, bytes, kind = ErrorKind::FloatParsing),
        };
        match str.parse() {
            Ok(i) => Ok(i),
            Err(_) => err_val_error!(py, str, kind = ErrorKind::FloatParsing),
        }
    } else {
        err_val_error!(py, v, kind = ErrorKind::FloatType)
    }
}
