use std::fmt;

use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict};
use serde_json::{from_str as parse_json, Value as JsonValue};

use crate::build_macros::{dict_get, dict_get_required, py_error};
use crate::errors::{err_val_error, map_validation_error, ErrorKind, ValResult};
use crate::input::{Input, ToPy};

mod bool;
mod dict;
mod float;
mod function;
mod int;
mod list;
mod model;
mod model_create;
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

    fn validate_python(&self, py: Python, input: &PyAny) -> PyResult<PyObject> {
        let extra = Extra {
            data: None,
            field: None,
        };
        let r = self.validator.validate(py, input, &extra);
        r.map_err(|e| map_validation_error(&self.title, e))
    }

    fn validate_json(&self, py: Python, input: String) -> PyResult<PyObject> {
        let result: ValResult<PyObject> = match parse_json::<JsonValue>(input.as_str()) {
            Ok(input) => {
                let extra = Extra {
                    data: None,
                    field: None,
                };
                self.validator.validate(py, &input, &extra)
            }
            Err(e) => err_val_error!(py, input, message = Some(e.to_string()), kind = ErrorKind::InvalidJson),
        };

        result.map_err(|e| map_validation_error(&self.title, e))
    }

    fn validate_assignment(&self, py: Python, field: String, input: &PyAny, data: &PyDict) -> PyResult<PyObject> {
        let extra = Extra {
            data: Some(data),
            field: Some(field.as_str()),
        };
        let r = self.validator.validate(py, input, &extra);
        r.map_err(|e| map_validation_error(&self.title, e))
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
        // model classes
        self::model_create::ModelClassValidator,
        // strings
        self::string::StrValidator,
        // integers
        self::int::IntValidator,
        // boolean
        self::bool::BoolValidator,
        // floats
        self::float::FloatValidator,
        // list/arrays (recursive)
        self::list::ListValidator,
        // dicts/objects (recursive)
        self::dict::DictValidator,
        // None/null
        self::none::NoneValidator,
        // functions - before, after, plain & wrap
        self::function::FunctionValidator,
    )
}

/// More (mostly immutable) data to pass between validators, should probably be class `Context`,
/// but that would confuse it with context as per samuelcolvin/pydantic#1549
#[derive(Debug)]
pub struct Extra<'a> {
    /// This is used as the `data` kwargs to validator functions, it's also represents the current model
    /// data when validating assignment
    pub data: Option<&'a PyDict>,
    /// The field being assigned to when validating assignment
    pub field: Option<&'a str>,
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
    fn validate(&self, py: Python, input: &dyn Input, extra: &Extra) -> ValResult<PyObject>;

    /// Ugly, but this has to be duplicated on all types to allow for cloning of validators,
    /// cloning is required to allow the SchemaValidator to be passed around in python
    fn clone_dyn(&self) -> Box<dyn Validator>;
}

impl Clone for Box<dyn Validator> {
    fn clone(&self) -> Self {
        self.clone_dyn()
    }
}
