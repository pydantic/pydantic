use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict, PyList, PyString};

#[pyfunction]
pub fn validate_str(v: &PyAny) -> PyResult<String> {
    if let Ok(str) = v.downcast::<PyString>() {
        str.extract()
    } else if let Ok(bytes) = v.downcast::<PyBytes>() {
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
pub fn validate_str_full(
    v: &PyAny,
    min_length: Option<usize>,
    max_length: Option<usize>,
    strip_whitespace: bool,
    to_lower: bool,
    to_upper: bool,
) -> PyResult<String> {
    let mut str = validate_str(v)?;

    if strip_whitespace {
        str = str.trim().to_string();
    }

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

    if to_lower {
        Ok(str.to_lowercase())
    } else if to_upper {
        Ok(str.to_uppercase())
    } else {
        Ok(str)
    }
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
    if let Ok(list) = value.downcast::<PyList>() {
        validate_str_list(py, list, min_length, max_length, strip_whitespace, to_lower, to_upper)
    } else if let Ok(dict) = value.downcast::<PyDict>() {
        validate_str_dict(py, dict, min_length, max_length, strip_whitespace, to_lower, to_upper)
    } else {
        let s = validate_str_full(value, min_length, max_length, strip_whitespace, to_lower, to_upper)?;
        let s = PyString::new(py, &s);
        Ok(s)
    }
}
