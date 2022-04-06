use std::str::from_utf8;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict, PyInt, PyList, PyString};

use crate::utils::RegexPattern;

#[pyfunction]
pub fn validate_str(v: &PyAny) -> PyResult<String> {
    if let Ok(str) = v.cast_as::<PyString>() {
        str.extract()
    } else if let Ok(bytes) = v.cast_as::<PyBytes>() {
        Ok(from_utf8(bytes.as_bytes())?.to_string())
    } else if let Ok(int) = v.cast_as::<PyInt>() {
        Ok(i64::extract(int)?.to_string())
    } else if let Ok(float) = f64::extract(v) {
        // don't cast_as here so Decimals are covered - internally f64:extract uses PyFloat_AsDouble
        Ok(float.to_string())
    } else {
        let name = v.get_type().name().unwrap_or("<unknown type>");
        Err(PyValueError::new_err(format!("{} is not a valid string", name)))
    }
}

#[allow(clippy::too_many_arguments)]
#[pyfunction]
pub fn validate_str_full<'py>(
    py: Python<'py>,
    value: &PyAny,
    min_length: Option<usize>,
    max_length: Option<usize>,
    strip_whitespace: bool,
    to_lower: bool,
    to_upper: bool,
    pattern: Option<&RegexPattern>,
) -> PyResult<&'py PyAny> {
    let mut str = validate_str(value)?;

    if let Some(min_length) = min_length {
        if str.len() < min_length {
            return Err(PyValueError::new_err(format!("{} is shorter than {}", str, min_length)));
        }
    }
    if let Some(max_length) = max_length {
        if str.len() > max_length {
            return Err(PyValueError::new_err(format!("{} is longer than {}", str, max_length)));
        }
    }
    if let Some(pattern) = pattern {
        if !pattern.is_match(&str) {
            return Err(PyValueError::new_err(format!("{} does not match {}", str, pattern)));
        }
    }

    if strip_whitespace {
        str = str.trim().to_string();
    }

    if to_lower {
        str = str.to_lowercase()
    } else if to_upper {
        str = str.to_uppercase()
    }
    let py_str = PyString::new(py, &str);
    Ok(py_str)
}

fn validate_str_list<'py>(
    py: Python<'py>,
    list: &PyList,
    min_length: Option<usize>,
    max_length: Option<usize>,
    strip_whitespace: bool,
    to_lower: bool,
    to_upper: bool,
) -> PyResult<&'py PyAny> {
    let mut new_vec: Vec<&'py PyAny> = Vec::with_capacity(list.len());
    for value in list.iter() {
        let value = validate_str_recursive(py, value, min_length, max_length, strip_whitespace, to_lower, to_upper)?;
        new_vec.push(value);
    }
    // Ok(new_list.to_object(py))
    let new_list = PyList::new(py, &new_vec);
    Ok(new_list)
}

fn validate_str_dict<'py>(
    py: Python<'py>,
    dict: &PyDict,
    min_length: Option<usize>,
    max_length: Option<usize>,
    strip_whitespace: bool,
    to_lower: bool,
    to_upper: bool,
) -> PyResult<&'py PyAny> {
    let new_dict = PyDict::new(py);
    for (key, value) in dict.iter() {
        let value = validate_str_recursive(py, value, min_length, max_length, strip_whitespace, to_lower, to_upper)?;
        new_dict.set_item(key, value)?;
    }
    Ok(new_dict)
}

#[pyfunction]
pub fn validate_str_recursive<'py>(
    py: Python<'py>,
    value: &PyAny,
    min_length: Option<usize>,
    max_length: Option<usize>,
    strip_whitespace: bool,
    to_lower: bool,
    to_upper: bool,
) -> PyResult<&'py PyAny> {
    if let Ok(list) = value.cast_as::<PyList>() {
        validate_str_list(py, list, min_length, max_length, strip_whitespace, to_lower, to_upper)
    } else if let Ok(dict) = value.cast_as::<PyDict>() {
        validate_str_dict(py, dict, min_length, max_length, strip_whitespace, to_lower, to_upper)
    } else {
        validate_str_full(
            py,
            value,
            min_length,
            max_length,
            strip_whitespace,
            to_lower,
            to_upper,
            None,
        )
    }
}
