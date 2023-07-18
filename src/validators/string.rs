use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};
use regex::Regex;

use crate::build_tools::{is_strict, py_schema_error_type, schema_or_config};
use crate::errors::{ErrorType, ValError, ValResult};
use crate::input::Input;
use crate::recursion_guard::RecursionGuard;
use crate::tools::SchemaDict;

use super::{BuildValidator, CombinedValidator, Definitions, DefinitionsBuilder, Extra, Validator};

#[derive(Debug, Clone)]
pub struct StrValidator {
    strict: bool,
}

impl BuildValidator for StrValidator {
    const EXPECTED_TYPE: &'static str = "str";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        _definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let con_str_validator = StrConstrainedValidator::build(schema, config)?;

        if con_str_validator.has_constraints_set() {
            Ok(con_str_validator.into())
        } else {
            Ok(Self {
                strict: con_str_validator.strict,
            }
            .into())
        }
    }
}

impl_py_gc_traverse!(StrValidator {});

impl Validator for StrValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        _definitions: &'data Definitions<CombinedValidator>,
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        Ok(input.validate_str(extra.strict.unwrap_or(self.strict))?.into_py(py))
    }

    fn different_strict_behavior(
        &self,
        _definitions: Option<&DefinitionsBuilder<CombinedValidator>>,
        ultra_strict: bool,
    ) -> bool {
        !ultra_strict
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }

    fn complete(&mut self, _definitions: &DefinitionsBuilder<CombinedValidator>) -> PyResult<()> {
        Ok(())
    }
}

/// Any new properties set here must be reflected in `has_constraints_set`
#[derive(Debug, Clone, Default)]
pub struct StrConstrainedValidator {
    strict: bool,
    pattern: Option<Regex>,
    max_length: Option<usize>,
    min_length: Option<usize>,
    strip_whitespace: bool,
    to_lower: bool,
    to_upper: bool,
}

impl_py_gc_traverse!(StrConstrainedValidator {});

impl Validator for StrConstrainedValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        _definitions: &'data Definitions<CombinedValidator>,
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let either_str = input.validate_str(extra.strict.unwrap_or(self.strict))?;
        let cow = either_str.as_cow()?;
        let mut str = cow.as_ref();
        if self.strip_whitespace {
            str = str.trim();
        }

        let str_len: Option<usize> = if self.min_length.is_some() | self.max_length.is_some() {
            Some(str.chars().count())
        } else {
            None
        };
        if let Some(min_length) = self.min_length {
            if str_len.unwrap() < min_length {
                return Err(ValError::new(ErrorType::StringTooShort { min_length }, input));
            }
        }
        if let Some(max_length) = self.max_length {
            if str_len.unwrap() > max_length {
                return Err(ValError::new(ErrorType::StringTooLong { max_length }, input));
            }
        }

        if let Some(pattern) = &self.pattern {
            if !pattern.is_match(str) {
                return Err(ValError::new(
                    ErrorType::StringPatternMismatch {
                        pattern: pattern.to_string(),
                    },
                    input,
                ));
            }
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

    fn different_strict_behavior(
        &self,
        _definitions: Option<&DefinitionsBuilder<CombinedValidator>>,
        ultra_strict: bool,
    ) -> bool {
        !ultra_strict
    }

    fn get_name(&self) -> &str {
        "constrained-str"
    }

    fn complete(&mut self, _definitions: &DefinitionsBuilder<CombinedValidator>) -> PyResult<()> {
        Ok(())
    }
}

impl StrConstrainedValidator {
    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<Self> {
        let py = schema.py();
        let pattern = match schema.get_as(intern!(py, "pattern"))? {
            Some(s) => Some(Regex::new(s).map_err(|e| py_schema_error_type!("{}", e))?),
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
        })
    }

    // whether any of the constraints/customisations are actually enabled
    // except strict which can be set on StrValidator
    fn has_constraints_set(&self) -> bool {
        self.pattern.is_some()
            || self.max_length.is_some()
            || self.min_length.is_some()
            || self.strip_whitespace
            || self.to_lower
            || self.to_upper
    }
}
