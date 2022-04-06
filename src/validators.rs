use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyBool, PyDict, PyString};

use crate::utils::{dict_get, RegexPattern};
use crate::validator_functions::validate_str;

trait Validator {
    fn validate(&self, py: Python, obj: PyObject) -> PyResult<PyObject>;
}

#[derive(Debug)]
struct NullValidator;

impl Validator for NullValidator {
    fn validate(&self, py: Python, _obj: PyObject) -> PyResult<PyObject> {
        Ok(py.None())
    }
}

#[allow(dead_code)]
fn schema_null(_dict: &PyDict) -> PyResult<Vec<Box<dyn Validator>>> {
    Ok(vec![Box::new(NullValidator)])
}

#[derive(Debug)]
struct BoolValidator;

impl Validator for BoolValidator {
    fn validate(&self, py: Python, obj: PyObject) -> PyResult<PyObject> {
        let obj: &PyBool = obj.extract(py)?;
        Ok(obj.to_object(py))
    }
}

#[allow(dead_code)]
fn schema_bool(_dict: &PyDict) -> PyResult<Vec<Box<dyn Validator>>> {
    Ok(vec![Box::new(BoolValidator)])
}

#[derive(Debug)]
struct SimpleStringValidator;

impl Validator for SimpleStringValidator {
    fn validate(&self, py: Python, obj: PyObject) -> PyResult<PyObject> {
        let obj: &PyAny = obj.extract(py)?;
        let s = validate_str(obj)?;
        Ok(s.to_object(py))
    }
}

#[derive(Debug)]
struct FullStringValidator {
    // https://json-schema.org/draft/2020-12/json-schema-validation.html#rfc.section.6.3
    pattern: Option<RegexPattern>,
    max_length: Option<usize>,
    min_length: Option<usize>,
    strip_whitespace: bool,
    to_lower: bool,
    to_upper: bool,
}

impl Validator for FullStringValidator {
    fn validate(&self, py: Python, obj: PyObject) -> PyResult<PyObject> {
        let mut str: String = obj.extract(py)?;
        if let Some(min_length) = self.min_length {
            if str.len() < min_length {
                return Err(PyValueError::new_err(format!("{} is shorter than {}", str, min_length)));
            }
        }
        if let Some(max_length) = self.max_length {
            if str.len() > max_length {
                return Err(PyValueError::new_err(format!("{} is longer than {}", str, max_length)));
            }
        }
        if let Some(pattern) = &self.pattern {
            if !pattern.is_match(&str) {
                return Err(PyValueError::new_err(format!("{} does not match {}", str, pattern)));
            }
        }

        if self.strip_whitespace {
            str = str.trim().to_string();
        }

        if self.to_lower {
            str = str.to_lowercase()
        } else if self.to_upper {
            str = str.to_uppercase()
        }
        let py_str = PyString::new(py, &str);
        Ok(py_str.to_object(py))
    }
}

#[allow(dead_code)]
fn schema_string(dict: &PyDict) -> PyResult<Vec<Box<dyn Validator>>> {
    let mut v: Vec<Box<dyn Validator>> = vec![Box::new(SimpleStringValidator)];

    let pattern = dict_get!(dict, "pattern", RegexPattern);
    let min_length = dict_get!(dict, "min_length", usize);
    let max_length = dict_get!(dict, "max_length", usize);
    let strip_whitespace = dict_get!(dict, "strip_whitespace", bool);
    let to_lower = dict_get!(dict, "to_lower", bool);
    let to_upper = dict_get!(dict, "to_upper", bool);

    if pattern.is_some()
        || min_length.is_some()
        || max_length.is_some()
        || strip_whitespace.is_some()
        || to_lower.is_some()
        || to_upper.is_some()
    {
        v.push(Box::new(FullStringValidator {
            pattern,
            min_length,
            max_length,
            strip_whitespace: strip_whitespace.unwrap_or(false),
            to_lower: to_lower.unwrap_or(false),
            to_upper: to_upper.unwrap_or(false),
        }));
    }

    Ok(v)
}
