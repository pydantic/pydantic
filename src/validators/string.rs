use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};
use regex::Regex;

use crate::build_tools::{is_strict, py_error, schema_or_config};
use crate::errors::{context, err_val_error, ErrorKind, ValResult};
use crate::input::{EitherString, Input};
use crate::recursion_guard::RecursionGuard;

use super::{BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct StrValidator;

impl BuildValidator for StrValidator {
    const EXPECTED_TYPE: &'static str = "str";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        _build_context: &mut BuildContext,
    ) -> PyResult<CombinedValidator> {
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
            StrictStrValidator::build()
        } else {
            Ok(Self.into())
        }
    }
}

impl Validator for StrValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        Ok(input.lax_str()?.into_py(py))
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        Ok(input.strict_str()?.into_py(py))
    }

    fn get_name(&self, _py: Python) -> String {
        Self::EXPECTED_TYPE.to_string()
    }
}

#[derive(Debug, Clone)]
pub struct StrictStrValidator;

impl StrictStrValidator {
    fn build() -> PyResult<CombinedValidator> {
        Ok(Self.into())
    }
}

impl Validator for StrictStrValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        Ok(input.strict_str()?.into_py(py))
    }

    fn get_name(&self, _py: Python) -> String {
        "strict-str".to_string()
    }
}

#[derive(Debug, Clone)]
pub struct StrConstrainedValidator {
    strict: bool,
    pattern: Option<Regex>,
    max_length: Option<usize>,
    min_length: Option<usize>,
    strip_whitespace: bool,
    to_lower: bool,
    to_upper: bool,
}

impl Validator for StrConstrainedValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let str = match self.strict {
            true => input.strict_str()?,
            false => input.lax_str()?,
        };
        self._validation_logic(py, input, str)
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        self._validation_logic(py, input, input.strict_str()?)
    }

    fn get_name(&self, _py: Python) -> String {
        "constrained-str".to_string()
    }
}

impl StrConstrainedValidator {
    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<CombinedValidator> {
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

        Ok(Self {
            strict: is_strict(schema, config)?,
            pattern,
            min_length,
            max_length,
            strip_whitespace,
            to_lower,
            to_upper,
        }
        .into())
    }

    fn _validation_logic<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        either_str: EitherString<'data>,
    ) -> ValResult<'data, PyObject> {
        let cow = either_str.as_cow();
        let mut str = cow.as_ref();
        if let Some(min_length) = self.min_length {
            if str.len() < min_length {
                // return py_error!("{} is shorter than {}", str, min_length);
                return err_val_error!(
                    input_value = input.as_error_value(),
                    kind = ErrorKind::StrTooShort,
                    context = context!("min_length" => min_length)
                );
            }
        }
        if let Some(max_length) = self.max_length {
            if str.len() > max_length {
                return err_val_error!(
                    input_value = input.as_error_value(),
                    kind = ErrorKind::StrTooLong,
                    context = context!("max_length" => max_length)
                );
            }
        }
        if let Some(pattern) = &self.pattern {
            if !pattern.is_match(str) {
                return err_val_error!(
                    input_value = input.as_error_value(),
                    kind = ErrorKind::StrPatternMismatch,
                    context = context!("pattern" => pattern.to_string())
                );
            }
        }

        if self.strip_whitespace {
            str = str.trim();
        }

        let py_string = if self.to_lower {
            PyString::new(py, &str.to_lowercase())
        } else if self.to_upper {
            PyString::new(py, &str.to_uppercase())
        } else if self.strip_whitespace {
            PyString::new(py, str)
        } else {
            // we haven't modified the string, return the original as it might be a PyString
            either_str.as_py_string(py)
        };
        Ok(py_string.into_py(py))
    }
}

fn build_regex(pattern: &str) -> PyResult<Regex> {
    match Regex::new(pattern) {
        Ok(r) => Ok(r),
        Err(e) => py_error!("{}", e),
    }
}
