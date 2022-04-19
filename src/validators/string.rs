use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};

use super::{Extra, Validator};
use crate::errors::{context, err_val_error, ErrorKind, ValResult};
use crate::input::{Input, ToPy};
use crate::utils::{dict_get, RegexPattern};

#[derive(Debug, Clone)]
pub struct StrValidator;

impl StrValidator {
    pub const EXPECTED_TYPE: &'static str = "str";
}

impl Validator for StrValidator {
    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        let use_con_str = match config {
            Some(config) => {
                config.get_item("str_pattern").is_some()
                    || config.get_item("str_max_length").is_some()
                    || config.get_item("str_min_length").is_some()
                    || config.get_item("str_strip_whitespace").is_some()
                    || config.get_item("str_to_lower").is_some()
                    || config.get_item("str_to_upper").is_some()
            }
            None => false,
        };

        if use_con_str {
            StrConstrainedValidator::build(schema, config)
        } else {
            Ok(Box::new(Self))
        }
    }

    fn validate(&self, py: Python, input: &dyn Input, _extra: &Extra) -> ValResult<PyObject> {
        let s = input.validate_str(py)?;
        ValResult::Ok(s.into_py(py))
    }

    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}

#[derive(Debug, Clone)]
pub struct StrConstrainedValidator {
    pattern: Option<RegexPattern>,
    max_length: Option<usize>,
    min_length: Option<usize>,
    strip_whitespace: bool,
    to_lower: bool,
    to_upper: bool,
}

impl StrConstrainedValidator {
    pub const EXPECTED_TYPE: &'static str = "str-constrained";
}

macro_rules! optional_dict_get {
    ($optional_dict:ident, $key:expr, $type:ty) => {
        match $optional_dict {
            Some(d) => dict_get!(d, $key, $type),
            None => None,
        }
    };
}

impl Validator for StrConstrainedValidator {
    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        let pattern = match schema.get_item("pattern") {
            Some(s) => Some(RegexPattern::py_new(s)?),
            None => match schema.get_item("str_pattern") {
                Some(s) => Some(RegexPattern::py_new(s)?),
                None => None,
            },
        };
        let min_length = match dict_get!(schema, "min_length", usize) {
            Some(v) => Some(v),
            None => optional_dict_get!(config, "str_min_length", usize),
        };
        let max_length = match dict_get!(schema, "max_length", usize) {
            Some(v) => Some(v),
            None => optional_dict_get!(config, "str_max_length", usize),
        };

        let strip_whitespace = match dict_get!(schema, "strip_whitespace", bool) {
            Some(v) => v,
            None => optional_dict_get!(config, "str_strip_whitespace", bool).unwrap_or(false),
        };
        let to_lower = match dict_get!(schema, "to_lower", bool) {
            Some(v) => v,
            None => optional_dict_get!(config, "str_to_lower", bool).unwrap_or(false),
        };
        let to_upper = match dict_get!(schema, "to_upper", bool) {
            Some(v) => v,
            None => optional_dict_get!(config, "str_to_upper", bool).unwrap_or(false),
        };

        Ok(Box::new(Self {
            pattern,
            min_length,
            max_length,
            strip_whitespace,
            to_lower,
            to_upper,
        }))
    }

    fn validate(&self, py: Python, input: &dyn Input, _extra: &Extra) -> ValResult<PyObject> {
        let mut str = input.validate_str(py)?;
        if let Some(min_length) = self.min_length {
            if str.len() < min_length {
                // return py_error!("{} is shorter than {}", str, min_length);
                return err_val_error!(
                    py,
                    str,
                    kind = ErrorKind::StrTooShort,
                    context = context!("min_length" => min_length)
                );
            }
        }
        if let Some(max_length) = self.max_length {
            if str.len() > max_length {
                return err_val_error!(
                    py,
                    str,
                    kind = ErrorKind::StrTooLong,
                    context = context!("max_length" => max_length)
                );
            }
        }
        if let Some(pattern) = &self.pattern {
            if !pattern.is_match(&str) {
                return err_val_error!(
                    py,
                    str,
                    kind = ErrorKind::StrPatternMismatch,
                    context = context!("pattern" => pattern.to_string())
                );
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
        ValResult::Ok(py_str.into_py(py))
    }

    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}
