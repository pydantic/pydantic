use std::collections::HashSet;
use std::str::from_utf8;

use lazy_static::lazy_static;
use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict, PyInt, PyList, PyString};

use crate::errors::{as_internal, err_val_error, ErrorKind, ValResult};

pub fn validate_str(py: Python, v: &PyAny) -> ValResult<String> {
    if let Ok(py_str) = v.cast_as::<PyString>() {
        py_str.extract().map_err(as_internal)
    } else if let Ok(bytes) = v.cast_as::<PyBytes>() {
        let str = match from_utf8(bytes.as_bytes()) {
            Ok(s) => s.to_string(),
            Err(_) => return err_val_error!(py, v, kind = ErrorKind::StrUnicode),
        };
        Ok(str)
    } else if let Ok(int) = v.cast_as::<PyInt>() {
        // TODO remove unwrap
        let int = i64::extract(int).map_err(as_internal)?;
        Ok(int.to_string())
    } else if let Ok(float) = f64::extract(v) {
        // don't cast_as here so Decimals are covered - internally f64:extract uses PyFloat_AsDouble
        Ok(float.to_string())
    } else {
        // let name = v.get_type().name().unwrap_or("<unknown type>");
        err_val_error!(py, v, kind = ErrorKind::StrType)
    }
}

pub fn validate_bool(py: Python, v: &PyAny) -> ValResult<bool> {
    if let Ok(bool) = v.extract::<bool>() {
        Ok(bool)
    } else if let Some(str) = _maybe_as_string(py, v, ErrorKind::BoolParsing)? {
        let s_lower = str.to_lowercase();
        if BOOL_FALSE_CELL.contains(s_lower.as_str()) {
            Ok(false)
        } else if BOOL_TRUE_CELL.contains(s_lower.as_str()) {
            Ok(true)
        } else {
            err_val_error!(py, str, kind = ErrorKind::BoolParsing)
        }
    } else if let Ok(int) = v.extract::<i64>() {
        if int == 0 {
            Ok(false)
        } else if int == 1 {
            Ok(true)
        } else {
            err_val_error!(py, int, kind = ErrorKind::BoolParsing)
        }
    } else {
        err_val_error!(py, v, kind = ErrorKind::BoolType)
    }
}

lazy_static! {
    static ref BOOL_FALSE_CELL: HashSet<&'static str> = HashSet::from(["0", "off", "f", "false", "n", "no"]);
}

lazy_static! {
    static ref BOOL_TRUE_CELL: HashSet<&'static str> = HashSet::from(["1", "on", "t", "true", "y", "yes"]);
}

pub fn validate_int(py: Python, v: &PyAny) -> ValResult<i64> {
    if let Ok(int) = v.extract::<i64>() {
        Ok(int)
    } else if let Some(str) = _maybe_as_string(py, v, ErrorKind::IntParsing)? {
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

pub fn validate_float(py: Python, v: &PyAny) -> ValResult<f64> {
    if let Ok(int) = v.extract::<f64>() {
        Ok(int)
    } else if let Some(str) = _maybe_as_string(py, v, ErrorKind::FloatParsing)? {
        match str.parse() {
            Ok(i) => Ok(i),
            Err(_) => err_val_error!(py, str, kind = ErrorKind::FloatParsing),
        }
    } else {
        err_val_error!(py, v, kind = ErrorKind::FloatType)
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

pub fn validate_list<'py>(py: Python<'py>, v: &'py PyAny) -> ValResult<&'py PyList> {
    if let Ok(list) = v.cast_as::<PyList>() {
        Ok(list)
        // TODO support sets, tuples, frozen set etc. like in pydantic
    } else {
        err_val_error!(py, v, kind = ErrorKind::ListType)
    }
}

/// Utility for extracting a string from a PyAny, if possible.
fn _maybe_as_string(py: Python, v: &PyAny, unicode_error: ErrorKind) -> ValResult<Option<String>> {
    if let Ok(str) = v.extract::<String>() {
        Ok(Some(str))
    } else if let Ok(bytes) = v.cast_as::<PyBytes>() {
        let str = match from_utf8(bytes.as_bytes()) {
            Ok(s) => s.to_string(),
            Err(_) => return err_val_error!(py, bytes, kind = unicode_error),
        };
        Ok(Some(str))
    } else {
        Ok(None)
    }
}
