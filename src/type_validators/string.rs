use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict, PyString};

use super::TypeValidator;
use crate::standalone_validators::validate_str;
use crate::utils::{dict_get, py_error, RegexPattern};

#[derive(Debug, Clone)]
pub struct SimpleStringValidator;

impl TypeValidator for SimpleStringValidator {
    fn is_match(type_: &str, dict: &PyDict) -> bool {
        type_ == "string"
            && dict.get_item("pattern").is_none()
            && dict.get_item("min_length").is_none()
            && dict.get_item("max_length").is_none()
            && dict.get_item("strip_whitespace").is_none()
            && dict.get_item("to_lower").is_none()
            && dict.get_item("to_upper").is_none()
    }

    fn build(_dict: &PyDict) -> PyResult<Self> {
        Ok(Self)
    }

    fn validate(&self, py: Python, obj: PyObject) -> PyResult<PyObject> {
        let obj: &PyAny = obj.extract(py)?;
        let s = validate_str(obj)?;
        Ok(s.to_object(py))
    }

    fn clone_dyn(&self) -> Box<dyn TypeValidator> {
        Box::new(self.clone())
    }
}

#[derive(Debug, Clone)]
pub struct FullStringValidator {
    pattern: Option<RegexPattern>,
    max_length: Option<usize>,
    min_length: Option<usize>,
    strip_whitespace: bool,
    to_lower: bool,
    to_upper: bool,
}

impl TypeValidator for FullStringValidator {
    fn is_match(type_: &str, _dict: &PyDict) -> bool {
        type_ == "string"
    }

    fn build(dict: &PyDict) -> PyResult<Self> {
        let pattern = match dict.get_item("pattern") {
            Some(s) => Some(RegexPattern::py_new(s)?.into()),
            None => None,
        };
        let min_length = dict_get!(dict, "min_length", usize);
        let max_length = dict_get!(dict, "max_length", usize);
        let strip_whitespace = dict_get!(dict, "strip_whitespace", bool);
        let to_lower = dict_get!(dict, "to_lower", bool);
        let to_upper = dict_get!(dict, "to_upper", bool);

        Ok(Self {
            pattern,
            min_length,
            max_length,
            strip_whitespace: strip_whitespace.unwrap_or(false),
            to_lower: to_lower.unwrap_or(false),
            to_upper: to_upper.unwrap_or(false),
        })
    }

    fn validate(&self, py: Python, obj: PyObject) -> PyResult<PyObject> {
        let obj: &PyAny = obj.extract(py)?;
        let mut str = validate_str(obj)?;
        if let Some(min_length) = self.min_length {
            if str.len() < min_length {
                return py_error!("{} is shorter than {}", str, min_length);
            }
        }
        if let Some(max_length) = self.max_length {
            if str.len() > max_length {
                return py_error!("{} is longer than {}", str, max_length);
            }
        }
        if let Some(pattern) = &self.pattern {
            if !pattern.is_match(&str) {
                return py_error!("{} does not match {}", str, pattern);
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

    fn clone_dyn(&self) -> Box<dyn TypeValidator> {
        Box::new(self.clone())
    }
}
