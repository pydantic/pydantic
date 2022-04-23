use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};
use regex::Regex;

use crate::build_macros::{dict_get, is_strict, optional_dict_get, py_error};
use crate::errors::{context, err_val_error, ErrorKind, ValResult};
use crate::input::{Input, ToPy};

use super::{Extra, Validator};

#[derive(Debug, Clone)]
pub struct StrValidator;

impl StrValidator {
    pub const EXPECTED_TYPE: &'static str = "str";
}

impl Validator for StrValidator {
    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        let use_constrained = schema.get_item("pattern").is_some()
            || schema.get_item("max_length").is_some()
            || schema.get_item("min_length").is_some()
            || schema.get_item("strip_whitespace").is_some()
            || schema.get_item("to_lower").is_some()
            || schema.get_item("to_upper").is_some()
            || match config {
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
        if use_constrained {
            StrConstrainedValidator::build(schema, config)
        } else if is_strict!(schema, config) {
            StrictStrValidator::build(schema, config)
        } else {
            Ok(Box::new(Self))
        }
    }

    fn validate(&self, py: Python, input: &dyn Input, _extra: &Extra) -> ValResult<PyObject> {
        Ok(input.lax_str(py)?.into_py(py))
    }

    fn validate_strict(&self, py: Python, input: &dyn Input, _extra: &Extra) -> ValResult<PyObject> {
        Ok(input.strict_str(py)?.into_py(py))
    }

    fn get_name(&self, _py: Python) -> String {
        Self::EXPECTED_TYPE.to_string()
    }

    #[no_coverage]
    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}

#[derive(Debug, Clone)]
struct StrictStrValidator;

impl Validator for StrictStrValidator {
    fn build(_schema: &PyDict, _config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        Ok(Box::new(Self))
    }

    fn validate(&self, py: Python, input: &dyn Input, _extra: &Extra) -> ValResult<PyObject> {
        Ok(input.strict_str(py)?.into_py(py))
    }

    fn validate_strict(&self, py: Python, input: &dyn Input, extra: &Extra) -> ValResult<PyObject> {
        self.validate(py, input, extra)
    }

    fn get_name(&self, _py: Python) -> String {
        "strict-str".to_string()
    }

    #[no_coverage]
    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}

#[derive(Debug, Clone)]
struct StrConstrainedValidator {
    strict: bool,
    pattern: Option<Regex>,
    max_length: Option<usize>,
    min_length: Option<usize>,
    strip_whitespace: bool,
    to_lower: bool,
    to_upper: bool,
}

impl Validator for StrConstrainedValidator {
    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        let pattern = match dict_get!(schema, "pattern", &str) {
            Some(s) => Some(build_regex(s)?),
            None => match optional_dict_get!(config, "str_pattern", &str) {
                Some(s) => Some(build_regex(s)?),
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
            strict: is_strict!(schema, config),
            pattern,
            min_length,
            max_length,
            strip_whitespace,
            to_lower,
            to_upper,
        }))
    }

    fn validate(&self, py: Python, input: &dyn Input, _extra: &Extra) -> ValResult<PyObject> {
        let str = match self.strict {
            true => input.strict_str(py)?,
            false => input.lax_str(py)?,
        };
        self._validation_logic(py, str)
    }

    fn validate_strict(&self, py: Python, input: &dyn Input, _extra: &Extra) -> ValResult<PyObject> {
        self._validation_logic(py, input.strict_str(py)?)
    }

    fn get_name(&self, _py: Python) -> String {
        "constrained-str".to_string()
    }

    #[no_coverage]
    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}

impl StrConstrainedValidator {
    fn _validation_logic(&self, py: Python, str: String) -> ValResult<PyObject> {
        let mut str = str;
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
}

fn build_regex(pattern: &str) -> PyResult<Regex> {
    match Regex::new(pattern) {
        Ok(r) => Ok(r),
        Err(e) => py_error!("{}", e.to_string()),
    }
}
