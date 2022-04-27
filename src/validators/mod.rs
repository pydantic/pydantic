use std::fmt;

use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict};
use serde_json::{from_str as parse_json, Value as JsonValue};

use crate::build_tools::{py_error, SchemaDict};
use crate::errors::{as_validation_err, val_line_error, ErrorKind, InputValue, ValError, ValResult};
use crate::input::Input;

use self::recursive::ValidatorArc;

mod bool;
mod dict;
mod float;
mod function;
mod int;
mod list;
mod literal;
mod model;
mod model_class;
mod none;
mod optional;
mod recursive;
mod string;
mod union;

#[pyclass]
#[derive(Debug, Clone)]
pub struct SchemaValidator {
    validator: Box<dyn Validator>,
}

#[pymethods]
impl SchemaValidator {
    #[new]
    pub fn py_new(schema: &PyAny) -> PyResult<Self> {
        Ok(Self {
            validator: build_validator(schema, None)?.0,
        })
    }

    fn validate_python(&self, py: Python, input: &PyAny) -> PyResult<PyObject> {
        let extra = Extra {
            data: None,
            field: None,
        };
        let r = self.validator.validate(py, input, &extra);
        r.map_err(|e| as_validation_err(py, &self.validator.get_name(py), e))
    }

    fn validate_json(&self, py: Python, input: String) -> PyResult<PyObject> {
        match parse_json::<JsonValue>(input.as_str()) {
            Ok(input) => {
                let extra = Extra {
                    data: None,
                    field: None,
                };
                let r = self.validator.validate(py, &input, &extra);
                r.map_err(|e| as_validation_err(py, &self.validator.get_name(py), e))
            }
            Err(e) => {
                let line_err = val_line_error!(
                    input_value = InputValue::InputRef(&input),
                    message = Some(e.to_string()),
                    kind = ErrorKind::InvalidJson
                );
                let err = ValError::LineErrors(vec![line_err]);
                Err(as_validation_err(py, &self.validator.get_name(py), err))
            }
        }
    }

    fn validate_assignment(&self, py: Python, field: String, input: &PyAny, data: &PyDict) -> PyResult<PyObject> {
        let extra = Extra {
            data: Some(data),
            field: Some(field.as_str()),
        };
        let r = self.validator.validate(py, input, &extra);
        r.map_err(|e| as_validation_err(py, &self.validator.get_name(py), e))
    }

    fn __repr__(&self, py: Python) -> String {
        format!(
            "SchemaValidator(name={:?}, validator={:#?})",
            self.validator.get_name(py),
            self.validator
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
                    Ok((val, $dict))
                },
            )+
            _ => {
                return py_error!(r#"Unknown schema type: "{}""#, $type)
            },
        }
    };
}

pub fn build_validator<'a>(
    schema: &'a PyAny,
    config: Option<&'a PyDict>,
) -> PyResult<(Box<dyn Validator>, &'a PyDict)> {
    let dict: &PyDict = match schema.cast_as() {
        Ok(s) => s,
        Err(_) => {
            let dict = PyDict::new(schema.py());
            dict.set_item("type", schema)?;
            dict
        }
    };
    let type_: &str = dict.get_as_req("type")?;
    validator_match!(
        type_,
        dict,
        config,
        // models e.g. heterogeneous dicts
        self::model::ModelValidator,
        // unions
        self::union::UnionValidator,
        self::optional::OptionalValidator,
        // model classes
        self::model_class::ModelClassValidator,
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
        // recursive (self-referencing) models
        self::recursive::RecursiveValidator,
        self::recursive::RecursiveRefValidator,
        // literals
        self::literal::LiteralValidator,
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
pub trait Validator: Send + Sync + fmt::Debug {
    /// Build a new validator from the schema, the return type is a trait to provide an escape hatch for validators
    /// to return other validators, currently only used by StrValidator
    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<Box<dyn Validator>>
    where
        Self: Sized;

    /// Do the actual validation for this schema/type
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
    ) -> ValResult<'data, PyObject>;

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        self.validate(py, input, extra)
    }

    fn set_ref(&mut self, _name: &str, _validator_arc: &ValidatorArc) -> PyResult<()> {
        Ok(())
    }

    fn get_name(&self, py: Python) -> String;

    /// Ugly, but this has to be duplicated on all types to allow for cloning of validators,
    /// cloning is required to allow the SchemaValidator to be passed around in python
    #[no_coverage]
    fn clone_dyn(&self) -> Box<dyn Validator>;
}

impl Clone for Box<dyn Validator> {
    fn clone(&self) -> Self {
        self.clone_dyn()
    }
}

macro_rules! validator_boilerplate {
    ($name:expr) => {
        fn get_name(&self, _py: Python) -> String {
            $name.to_string()
        }

        fn clone_dyn(&self) -> Box<dyn Validator> {
            Box::new(self.clone())
        }
    };
}
pub(crate) use validator_boilerplate;

macro_rules! unused_validator {
    ($name:expr) => {
        #[no_coverage]
        fn validate<'s, 'data>(
            &'s self,
            _py: Python<'data>,
            _input: &'data dyn Input,
            _extra: &Extra,
        ) -> ValResult<'data, PyObject> {
            unimplemented!("{} is never used directly", $name)
        }

        #[no_coverage]
        fn get_name(&self, _py: Python) -> String {
            unimplemented!()
        }

        #[no_coverage]
        fn clone_dyn(&self) -> Box<dyn Validator> {
            unimplemented!()
        }
    };
}
pub(crate) use unused_validator;
