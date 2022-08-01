use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};
use regex::Regex;

use crate::build_tools::{is_strict, py_error, schema_or_config};
use crate::errors::{ErrorKind, ValError, ValResult};
use crate::input::Input;
use crate::recursion_guard::RecursionGuard;

use super::{BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct StrValidator {
    strict: bool,
}

impl BuildValidator for StrValidator {
    const EXPECTED_TYPE: &'static str = "str";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        _build_context: &mut BuildContext,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let use_constrained = schema.get_item(intern!(py, "pattern")).is_some()
            || schema.get_item(intern!(py, "max_length")).is_some()
            || schema.get_item(intern!(py, "min_length")).is_some()
            || schema.get_item(intern!(py, "strip_whitespace")).is_some()
            || schema.get_item(intern!(py, "to_lower")).is_some()
            || schema.get_item(intern!(py, "to_upper")).is_some()
            || match config {
                Some(config) => {
                    config.get_item(intern!(py, "str_pattern")).is_some()
                        || config.get_item(intern!(py, "str_max_length")).is_some()
                        || config.get_item(intern!(py, "str_min_length")).is_some()
                        || config.get_item(intern!(py, "str_strip_whitespace")).is_some()
                        || config.get_item(intern!(py, "str_to_lower")).is_some()
                        || config.get_item(intern!(py, "str_to_upper")).is_some()
                }
                None => false,
            };
        if use_constrained {
            StrConstrainedValidator::build(schema, config)
        } else {
            Ok(Self {
                strict: is_strict(schema, config)?,
            }
            .into())
        }
    }
}

impl Validator for StrValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        Ok(input.validate_str(extra.strict.unwrap_or(self.strict))?.into_py(py))
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
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
        extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let either_str = input.validate_str(extra.strict.unwrap_or(self.strict))?;
        let cow = either_str.as_cow()?;
        let mut str = cow.as_ref();
        if let Some(min_length) = self.min_length {
            if str.len() < min_length {
                // return py_error!("{} is shorter than {}", str, min_length);
                return Err(ValError::new(ErrorKind::StrTooShort { min_length }, input));
            }
        }
        if let Some(max_length) = self.max_length {
            if str.len() > max_length {
                return Err(ValError::new(ErrorKind::StrTooLong { max_length }, input));
            }
        }
        if let Some(pattern) = &self.pattern {
            if !pattern.is_match(str) {
                return Err(ValError::new(
                    ErrorKind::StrPatternMismatch {
                        pattern: pattern.to_string(),
                    },
                    input,
                ));
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

    fn get_name(&self) -> &str {
        "constrained-str"
    }
}

impl StrConstrainedValidator {
    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let pattern_str: Option<&str> =
            schema_or_config(schema, config, intern!(py, "pattern"), intern!(py, "str_pattern"))?;
        let pattern = match pattern_str {
            Some(s) => Some(build_regex(s)?),
            None => None,
        };
        let min_length: Option<usize> =
            schema_or_config(schema, config, intern!(py, "min_length"), intern!(py, "str_min_length"))?;
        let max_length: Option<usize> =
            schema_or_config(schema, config, intern!(py, "max_length"), intern!(py, "str_max_length"))?;

        let strip_whitespace: bool = schema_or_config(
            schema,
            config,
            intern!(py, "strip_whitespace"),
            intern!(py, "str_strip_whitespace"),
        )?
        .unwrap_or(false);
        let to_lower: bool =
            schema_or_config(schema, config, intern!(py, "to_lower"), intern!(py, "str_to_lower"))?.unwrap_or(false);
        let to_upper: bool =
            schema_or_config(schema, config, intern!(py, "to_upper"), intern!(py, "str_to_upper"))?.unwrap_or(false);

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
}

fn build_regex(pattern: &str) -> PyResult<Regex> {
    match Regex::new(pattern) {
        Ok(r) => Ok(r),
        Err(e) => py_error!("{}", e),
    }
}
