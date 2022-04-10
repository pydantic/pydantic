use std::fmt::Debug;

use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict};

use crate::errors::{ValError, ValResult, ValidationError};
use crate::utils::{dict_get, dict_get_required, py_error};

mod bool;
mod decorator;
mod dict;
mod float;
mod int;
mod list;
mod model;
mod none;
mod string;

// TODO date, datetime, set, tuple, bytes, custom types, dict, union, literal

#[pyclass]
#[derive(Debug, Clone)]
pub struct SchemaValidator {
    validator: Box<dyn Validator>,
    model_name: Option<String>,
}

#[pymethods]
impl SchemaValidator {
    #[new]
    pub fn py_new(py: Python, obj: PyObject) -> PyResult<Self> {
        let dict: &PyDict = obj.cast_as(py)?;
        Ok(Self {
            validator: build_validator(dict)?,
            model_name: dict_get!(dict, "model_name", String),
        })
    }

    fn run(&self, py: Python, obj: &PyAny) -> PyResult<PyObject> {
        match self.validator.validate(py, obj) {
            Ok(obj) => Ok(obj),
            Err(ValError::LineErrors(line_errors)) => {
                let model_name = match self.model_name {
                    Some(ref name) => name.clone(),
                    None => "<unknown>".to_string(),
                };
                let args = (line_errors, model_name);
                Err(ValidationError::new_err(args))
            }
            Err(ValError::InternalErr(err)) => Err(err),
        }
    }

    fn __repr__(&self) -> String {
        format!(
            "SchemaValidator(validator={:?}, model_name={:?})",
            self.validator, self.model_name
        )
    }
}

pub fn build_validator(dict: &PyDict) -> PyResult<Box<dyn Validator>> {
    let type_: String = dict_get_required!(dict, "type", String)?;

    // if_else is used in validator_selection
    macro_rules! if_else {
        ($validator:path, $else:tt) => {
            if <$validator>::is_match(&type_, dict) {
                let val = <$validator>::build(dict)?;
                return Ok(Box::new(val));
            } else {
                $else
            }
        };
    }

    // macro to build a long if/else chain for validator selection
    macro_rules! validator_selection {
        // single validator - will be called last by variant below
        ($validator:path) => {
            if_else!($validator, {
                return py_error!(r#"unknown schema type: "{}""#, type_);
            })
        };
        // without a trailing comma
        ($validator:path, $($validators:path),+) => {
            if_else!($validator, {
                validator_selection!($($validators),+)
            })
        };
        // with a trailing comma
        ($validator:path, $($validators:path,)+) => {
            if_else!($validator, {
                validator_selection!($($validators),+)
            })
        };
    }

    // order matters here!
    // e.g. SimpleStrValidator must come before FullStrValidator
    // also for performance reasons commonly used validators should be first
    validator_selection!(
        // models e.g. heterogeneous dicts
        self::model::ModelValidator,
        // strings
        self::string::SimpleStrValidator,
        self::string::FullStrValidator,
        // integers
        self::int::SimpleIntValidator,
        self::int::FullIntValidator,
        // boolean
        self::bool::BoolValidator,
        // floats
        self::float::SimpleFloatValidator,
        self::float::FullFloatValidator,
        // list/arrays (recursive)
        self::list::ListValidator,
        // dicts/objects (recursive)
        self::dict::DictValidator,
        // None/null
        self::none::NoneValidator,
        // decorators
        self::decorator::PreDecoratorValidator,
        self::decorator::PostDecoratorValidator,
        self::decorator::WrapDecoratorValidator,
    )
}

pub trait Validator: Send + Debug {
    fn is_match(type_: &str, dict: &PyDict) -> bool
    where
        Self: Sized;

    fn build(dict: &PyDict) -> PyResult<Self>
    where
        Self: Sized;

    fn validate(&self, py: Python, obj: &PyAny) -> ValResult<PyObject>;

    fn clone_dyn(&self) -> Box<dyn Validator>;
}

impl Clone for Box<dyn Validator> {
    fn clone(&self) -> Self {
        self.clone_dyn()
    }
}
