use std::fmt;

use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict};

use crate::errors::{ValError, ValResult, ValidationError};
use crate::utils::{dict_get, dict_get_required, py_error};

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
    title: String,
    validator: Box<dyn Validator>,
}

#[pymethods]
impl SchemaValidator {
    #[new]
    pub fn py_new(dict: &PyDict) -> PyResult<Self> {
        let title = dict_get!(dict, "title", String).unwrap_or_else(|| "Model".to_string());
        Ok(Self {
            title,
            validator: build_validator(dict, None)?,
        })
    }

    fn run(&self, py: Python, input: &PyAny) -> PyResult<PyObject> {
        match self.validator.validate(py, input, PyDict::new(py)) {
            Ok(obj) => Ok(obj),
            Err(ValError::LineErrors(line_errors)) => Err(ValidationError::new_err((line_errors, self.title.clone()))),
            Err(ValError::InternalErr(err)) => Err(err),
        }
    }

    fn __repr__(&self) -> String {
        format!(
            "SchemaValidator(title={:?}, validator={:#?})",
            self.title, self.validator
        )
    }
}

// macro to build the match statement for validator selection
macro_rules! validator_match {
    ($type:ident, $dict:ident, $config:ident, $($validator:path,)+) => {
        match $type {
            $(
                <$validator>::EXPECTED_TYPE => {
                    let val = <$validator>::build($dict, $config).map_err(|err| {
                        crate::SchemaError::new_err(format!("Error building \"{}\" validator:\n  {}", $type, err))
                    })?;
                    Ok(val)
                },
            )+
            _ => {
                return py_error!(r#"Unknown schema type: "{}""#, $type)
            },
        }
    };
}

pub fn build_validator(dict: &PyDict, config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
    let type_: &str = dict_get_required!(dict, "type", &str)?;
    validator_match!(
        type_,
        dict,
        config,
        // models e.g. heterogeneous dicts
        self::model::ModelValidator,
        // strings
        self::string::StrValidator,
        self::string::StrConstrainedValidator,
        // integers
        self::int::IntValidator,
        self::int::IntConstrainedValidator,
        // boolean
        self::bool::BoolValidator,
        // floats
        self::float::FloatValidator,
        self::float::FloatConstrainedValidator,
        // list/arrays (recursive)
        self::list::ListValidator,
        // dicts/objects (recursive)
        self::dict::DictValidator,
        // None/null
        self::none::NoneValidator,
        // decorators
        self::function::FunctionBeforeValidator,
        self::function::FunctionAfterValidator,
        self::function::FunctionPlainValidator,
        self::function::FunctionWrapValidator,
    )
}

/// This trait must be implemented by all validators, it allows various validators to be accessed consistently,
/// they also need `EXPECTED_TYPE` as a const, but that can't be part of the trait.
pub trait Validator: Send + fmt::Debug {
    /// Build a new validator from the schema, the return type is a trait to provide an escape hatch for validators
    /// to return other validators, currently only used by StrValidator
    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<Box<dyn Validator>>
    where
        Self: Sized;

    /// Do the actual validation for this schema/type
    fn validate(&self, py: Python, input: &PyAny, data: &PyDict) -> ValResult<PyObject>;

    /// Ugly, but this has to be duplicated on all types to allow for cloning of validators,
    /// cloning is required to allow the SchemaValidator to be passed around in python
    fn clone_dyn(&self) -> Box<dyn Validator>;
}

impl Clone for Box<dyn Validator> {
    fn clone(&self) -> Self {
        self.clone_dyn()
    }
}
