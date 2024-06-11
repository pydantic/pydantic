use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};
use regex::Regex;

use crate::build_tools::{is_strict, py_schema_error_type, schema_or_config, schema_or_config_same};
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
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
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
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<PyObject> {
        input
            .validate_str(state.strict_or(self.strict), self.coerce_numbers_to_str)
            .map(|val_match| val_match.unpack(state).as_py_string(py, state.cache_str()).into_py(py))
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
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
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
            state.maybe_cached_str(py, &str.to_lowercase())
        } else if self.to_upper {
            state.maybe_cached_str(py, &str.to_uppercase())
        } else if self.strip_whitespace {
            state.maybe_cached_str(py, str)
        } else {
            // we haven't modified the string, return the original as it might be a PyString
            either_str.as_py_string(py, state.cache_str())
        };
        Ok(py_string.into_py(py))
    }

    fn get_name(&self) -> &str {
        "constrained-str"
    }
}

impl StrConstrainedValidator {
    fn build(schema: &Bound<'_, PyDict>, config: Option<&Bound<'_, PyDict>>) -> PyResult<Self> {
        let py = schema.py();

        let pattern = schema
            .get_as(intern!(py, "pattern"))?
            .map(|s| {
                let regex_engine = schema_or_config::<Bound<'_, PyString>>(
                    schema,
                    config,
                    intern!(py, "regex_engine"),
                    intern!(py, "regex_engine"),
                )?;
                let regex_engine = regex_engine
                    .as_ref()
                    .map(|s| s.to_str())
                    .transpose()?
                    .unwrap_or(RegexEngine::RUST_REGEX);
                Pattern::compile(s, regex_engine)
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

        let coerce_numbers_to_str: bool =
            schema_or_config_same(schema, config, intern!(py, "coerce_numbers_to_str"))?.unwrap_or(false);

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
            || self.coerce_numbers_to_str
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
    fn extract_pattern_str(pattern: &Bound<'_, PyAny>) -> PyResult<String> {
        if pattern.is_instance_of::<PyString>() {
            Ok(pattern.to_string())
        } else {
            pattern
                .getattr("pattern")
                .and_then(|attr| attr.extract::<String>())
                .map_err(|_| py_schema_error_type!("Invalid pattern, must be str or re.Pattern: {}", pattern))
        }
    }

    fn compile(pattern: Bound<'_, PyAny>, engine: &str) -> PyResult<Self> {
        let pattern_str = Self::extract_pattern_str(&pattern)?;

        let py = pattern.py();

        let re_module = py.import_bound(intern!(py, "re"))?;
        let re_compile = re_module.getattr(intern!(py, "compile"))?;
        let re_pattern = re_module.getattr(intern!(py, "Pattern"))?;

        if pattern.is_instance(&re_pattern)? {
            // if the pattern is already a compiled regex object, we default to using the python re engine
            // so that any flags, etc. are preserved
            Ok(Self {
                pattern: pattern_str,
                engine: RegexEngine::PythonRe(pattern.to_object(py)),
            })
        } else {
            let engine = match engine {
                RegexEngine::RUST_REGEX => {
                    RegexEngine::RustRegex(Regex::new(&pattern_str).map_err(|e| py_schema_error_type!("{}", e))?)
                }
                RegexEngine::PYTHON_RE => RegexEngine::PythonRe(re_compile.call1((pattern,))?.into()),
                _ => return Err(py_schema_error_type!("Invalid regex engine: {}", engine)),
            };

            Ok(Self {
                pattern: pattern_str,
                engine,
            })
        }
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
