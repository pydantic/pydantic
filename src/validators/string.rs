use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};
use regex::Regex;

use crate::build_tools::{is_strict, py_schema_error_type, schema_or_config};
use crate::errors::{ErrorType, ValError, ValResult};
use crate::input::Input;
use crate::tools::SchemaDict;

use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

#[derive(Debug)]
pub struct StrValidator {
    strict: bool,
    coerce_numbers_to_str: bool,
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
                coerce_numbers_to_str: con_str_validator.coerce_numbers_to_str,
            }
            .into())
        }
    }
}

impl_py_gc_traverse!(StrValidator {});

impl Validator for StrValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<PyObject> {
        input
            .validate_str(state.strict_or(self.strict), self.coerce_numbers_to_str)
            .map(|val_match| val_match.unpack(state).into_py(py))
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}

/// Any new properties set here must be reflected in `has_constraints_set`
#[derive(Debug, Clone, Default)]
pub struct StrConstrainedValidator {
    strict: bool,
    pattern: Option<Pattern>,
    max_length: Option<usize>,
    min_length: Option<usize>,
    strip_whitespace: bool,
    to_lower: bool,
    to_upper: bool,
    coerce_numbers_to_str: bool,
}

impl_py_gc_traverse!(StrConstrainedValidator {});

impl Validator for StrConstrainedValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<PyObject> {
        let either_str = input
            .validate_str(state.strict_or(self.strict), self.coerce_numbers_to_str)?
            .unpack(state);
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
                return Err(ValError::new(
                    ErrorType::StringTooShort {
                        min_length,
                        context: None,
                    },
                    input,
                ));
            }
        }
        if let Some(max_length) = self.max_length {
            if str_len.unwrap() > max_length {
                return Err(ValError::new(
                    ErrorType::StringTooLong {
                        max_length,
                        context: None,
                    },
                    input,
                ));
            }
        }

        if let Some(pattern) = &self.pattern {
            if !pattern.is_match(py, str)? {
                return Err(ValError::new(
                    ErrorType::StringPatternMismatch {
                        pattern: pattern.pattern.clone(),
                        context: None,
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

    fn get_name(&self) -> &str {
        "constrained-str"
    }
}

impl StrConstrainedValidator {
    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<Self> {
        let py = schema.py();

        let pattern = schema
            .get_as(intern!(py, "pattern"))?
            .map(|s| {
                let regex_engine =
                    schema_or_config(schema, config, intern!(py, "regex_engine"), intern!(py, "regex_engine"))?
                        .unwrap_or(RegexEngine::RUST_REGEX);
                Pattern::compile(py, s, regex_engine)
            })
            .transpose()?;
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

        let coerce_numbers_to_str = match config {
            Some(c) => c.get_item("coerce_numbers_to_str")?.map_or(Ok(false), PyAny::is_true)?,
            None => false,
        };

        Ok(Self {
            strict: is_strict(schema, config)?,
            pattern,
            min_length,
            max_length,
            strip_whitespace,
            to_lower,
            to_upper,
            coerce_numbers_to_str,
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

#[derive(Debug, Clone)]
struct Pattern {
    pattern: String,
    engine: RegexEngine,
}

#[derive(Debug, Clone)]
enum RegexEngine {
    RustRegex(Regex),
    PythonRe(PyObject),
}

impl RegexEngine {
    const RUST_REGEX: &'static str = "rust-regex";
    const PYTHON_RE: &'static str = "python-re";
}

impl Pattern {
    fn compile(py: Python<'_>, pattern: String, engine: &str) -> PyResult<Self> {
        let engine = match engine {
            RegexEngine::RUST_REGEX => {
                RegexEngine::RustRegex(Regex::new(&pattern).map_err(|e| py_schema_error_type!("{}", e))?)
            }
            RegexEngine::PYTHON_RE => {
                let re_compile = py.import(intern!(py, "re"))?.getattr(intern!(py, "compile"))?;
                RegexEngine::PythonRe(re_compile.call1((&pattern,))?.into())
            }
            _ => return Err(py_schema_error_type!("Invalid regex engine: {}", engine)),
        };
        Ok(Self { pattern, engine })
    }

    fn is_match(&self, py: Python<'_>, target: &str) -> PyResult<bool> {
        match &self.engine {
            RegexEngine::RustRegex(regex) => Ok(regex.is_match(target)),
            RegexEngine::PythonRe(py_regex) => {
                Ok(!py_regex.call_method1(py, intern!(py, "match"), (target,))?.is_none(py))
            }
        }
    }
}
