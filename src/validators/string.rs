use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};
use regex::Regex;

use crate::build_tools::{is_strict, py_error, schema_or_config};
use crate::errors::{context, err_val_error, ErrorKind, InputValue, ValResult};
use crate::input::Input;

use super::{validator_boilerplate, Extra, Validator};

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
        } else if is_strict(schema, config)? {
            StrictStrValidator::build(schema, config)
        } else {
            Ok(Box::new(Self))
        }
    }

    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        Ok(input.lax_str(py)?.into_py(py))
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        Ok(input.strict_str(py)?.into_py(py))
    }

    validator_boilerplate!(Self::EXPECTED_TYPE);
}

#[derive(Debug, Clone)]
struct StrictStrValidator;

impl Validator for StrictStrValidator {
    fn build(_schema: &PyDict, _config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        Ok(Box::new(Self))
    }

    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        Ok(input.strict_str(py)?.into_py(py))
    }

    validator_boilerplate!("strict-str");
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
        let pattern_str: Option<&str> = schema_or_config(schema, config, "pattern", "str_pattern")?;
        let pattern = match pattern_str {
            Some(s) => Some(build_regex(s)?),
            None => None,
        };
        let min_length: Option<usize> = schema_or_config(schema, config, "min_length", "str_min_length")?;
        let max_length: Option<usize> = schema_or_config(schema, config, "max_length", "str_max_length")?;

        let strip_whitespace: bool =
            schema_or_config(schema, config, "strip_whitespace", "str_strip_whitespace")?.unwrap_or(false);
        let to_lower: bool = schema_or_config(schema, config, "to_lower", "str_to_lower")?.unwrap_or(false);
        let to_upper: bool = schema_or_config(schema, config, "to_upper", "str_to_upper")?.unwrap_or(false);

        Ok(Box::new(Self {
            strict: is_strict(schema, config)?,
            pattern,
            min_length,
            max_length,
            strip_whitespace,
            to_lower,
            to_upper,
        }))
    }

    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        let str = match self.strict {
            true => input.strict_str(py)?,
            false => input.lax_str(py)?,
        };
        self._validation_logic(py, input, str)
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        self._validation_logic(py, input, input.strict_str(py)?)
    }

    validator_boilerplate!("constrained-str");
}

impl StrConstrainedValidator {
    fn _validation_logic<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        str: String,
    ) -> ValResult<'data, PyObject> {
        let mut str = str;
        if let Some(min_length) = self.min_length {
            if str.len() < min_length {
                // return py_error!("{} is shorter than {}", str, min_length);
                return err_val_error!(
                    input_value = InputValue::InputRef(input),
                    kind = ErrorKind::StrTooShort,
                    context = context!("min_length" => min_length)
                );
            }
        }
        if let Some(max_length) = self.max_length {
            if str.len() > max_length {
                return err_val_error!(
                    input_value = InputValue::InputRef(input),
                    kind = ErrorKind::StrTooLong,
                    context = context!("max_length" => max_length)
                );
            }
        }
        if let Some(pattern) = &self.pattern {
            if !pattern.is_match(&str) {
                return err_val_error!(
                    input_value = InputValue::InputRef(input),
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
