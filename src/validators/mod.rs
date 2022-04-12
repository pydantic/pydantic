use std::fmt::Debug;

use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict};

use crate::errors::{ValError, ValResult, ValidationError};
use crate::utils::{dict_get_required, py_error};

mod bool;
mod dict;
mod float;
mod function;
mod int;
mod list;
mod model;
mod none;
mod string;

#[pyclass]
#[derive(Debug, Clone)]
pub struct SchemaValidator {
    model_name: String,
    validator: Box<dyn Validator>,
}

#[pymethods]
impl SchemaValidator {
    #[new]
    pub fn py_new(dict: &PyDict) -> PyResult<Self> {
        let model_name = dict_get_required!(dict, "model_name", String)?;
        Ok(Self {
            model_name,
            validator: build_validator(dict)?,
        })
    }

    fn run(&self, py: Python, input: &PyAny) -> PyResult<PyObject> {
        match self.validator.validate(py, input, PyDict::new(py)) {
            Ok(obj) => Ok(obj),
            Err(ValError::LineErrors(line_errors)) => {
                Err(ValidationError::new_err((line_errors, self.model_name.clone())))
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
        self::function::FunctionBeforeValidator,
        self::function::FunctionAfterValidator,
        self::function::FunctionWrapValidator,
    )
}

pub trait Validator: Send + Debug {
    fn is_match(type_: &str, dict: &PyDict) -> bool
    where
        Self: Sized;

    fn build(dict: &PyDict) -> PyResult<Self>
    where
        Self: Sized;

    fn validate(&self, py: Python, input: &PyAny, data: &PyDict) -> ValResult<PyObject>;

    fn clone_dyn(&self) -> Box<dyn Validator>;
}

impl Clone for Box<dyn Validator> {
    fn clone(&self) -> Self {
        self.clone_dyn()
    }
}
