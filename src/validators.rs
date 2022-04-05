use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyList};

#[pyfunction]
pub fn str_validator(v: &PyAny) -> PyResult<String> {
    if let Ok(str) = String::extract(v) {
        Ok(str)
    } else if let Ok(bytes) = v.extract::<&PyBytes>() {
        Ok(std::str::from_utf8(bytes.as_bytes())?.to_string())
    } else if let Ok(int) = i64::extract(v) {
        Ok(int.to_string())
    } else if let Ok(float) = f64::extract(v) {
        Ok(float.to_string())
    } else {
        Err(PyValueError::new_err(format!("{} is not a string", v)))
    }
}

#[pyfunction]
pub fn check_str(
    v: &PyAny,
    min_length: Option<usize>,
    max_length: Option<usize>,
    strip_whitespace: bool,
    to_lower: bool,
    to_upper: bool,
) -> PyResult<String> {
    let mut str = str_validator(v)?;
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

    if strip_whitespace {
        str = str.trim().to_string();
    }

    if to_lower {
        Ok(str.to_lowercase())
    } else if to_upper {
        Ok(str.to_uppercase())
    } else {
        Ok(str)
    }

    // Ok(data.to_object(py))
    // match String::extract(data) {
    //     Ok(s) => Ok(s),
    //     Err(e) => Err(e),
    // }
}

#[pyfunction]
pub fn check_list_str(
    py: Python,
    items: &PyAny,
    min_length: Option<usize>,
    max_length: Option<usize>,
    strip_whitespace: bool,
    to_lower: bool,
    to_upper: bool,
) -> PyResult<PyObject> {
    let items: &PyList = items.extract()?;
    let mut new_vec: Vec<String> = Vec::with_capacity(items.len());
    for item in items.iter() {
        new_vec.push(check_str(
            item,
            min_length,
            max_length,
            strip_whitespace,
            to_lower,
            to_upper,
        )?);
    }
    Ok(new_vec.to_object(py))
}
