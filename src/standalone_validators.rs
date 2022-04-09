use std::str::from_utf8;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyInt, PyString};

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
