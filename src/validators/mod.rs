use std::fmt;

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
    // macro to build the match statement validator selection
    macro_rules! validator_match {
        ($type:ident, $($validator:path,)+) => {
            match $type {
                $(
                    <$validator>::EXPECTED_TYPE => {
                        let val = <$validator>::build(dict).map_err(|err| {
                            crate::SchemaError::new_err(format!("Error building \"{}\" validator:\n  {}", $type, err))
                        })?;
                        Ok(Box::new(val))
                    },
                )+
                _ => {
                    return py_error!(r#"Unknown schema type: "{}""#, $type)
                },
            }
        };
    }

    let type_: &str = dict_get_required!(dict, "type", &str)?;
    validator_match!(
        type_,
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

pub trait Validator: Send + fmt::Debug {
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
