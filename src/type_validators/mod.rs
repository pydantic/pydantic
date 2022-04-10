use std::fmt::Debug;

use pyo3::exceptions::{PyKeyError, PyTypeError};
use pyo3::prelude::*;
use pyo3::types::{IntoPyDict, PyAny, PyDict};
use pyo3::ToPyObject;

use crate::errors::{ValError, ValResult, ValidationError};
use crate::utils::{dict_get, py_error};

mod bool;
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
    type_validator: Box<dyn TypeValidator>,
    model_name: Option<String>,
    external_validator: Option<PyObject>,
}

impl TypeValidator for SchemaValidator {
    fn is_match(_type: &str, _dict: &PyDict) -> bool {
        false
    }

    fn build(dict: &PyDict) -> PyResult<Self> {
        let type_validator = find_type_validator(dict)?;
        let external_validator = match dict.get_item("external_validator") {
            Some(obj) => {
                if !obj.is_callable() {
                    return py_error!(PyTypeError; "'external_validator' must be callable");
                }
                Some(obj.to_object(obj.py()))
            }
            None => None,
        };
        Ok(Self {
            type_validator,
            external_validator,
            model_name: dict_get!(dict, "model_name", String),
        })
    }

    fn validate(&self, py: Python, obj: &PyAny) -> ValResult<PyObject> {
        if let Some(external_validator) = &self.external_validator {
            let validator_kwarg = ValidatorCallable {
                type_validator: self.type_validator.clone(),
            };
            let kwargs = [("validator", validator_kwarg.into_py(py))];
            match external_validator.call(py, (), Some(kwargs.into_py_dict(py))) {
                Ok(output) => Ok(output),
                // TODO this is wrong, we should check for errors which could as validation errors
                Err(err) => Err(ValError::InternalErr(err)),
            }
        } else {
            self.type_validator.validate(py, obj)
        }
    }

    fn clone_dyn(&self) -> Box<dyn TypeValidator> {
        Box::new(self.clone())
    }
}

#[pymethods]
impl SchemaValidator {
    #[new]
    pub fn py_new(py: Python, obj: PyObject) -> PyResult<Self> {
        let dict: &PyDict = obj.cast_as(py)?;
        Self::build(dict)
    }

    fn run(&self, py: Python, obj: &PyAny) -> PyResult<PyObject> {
        match self.validate(py, obj) {
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

    fn __repr__(&self) -> PyResult<String> {
        Ok(format!(
            "SchemaValidator(type_validator={:?}, external_validator={:?})",
            self.type_validator, self.external_validator
        ))
    }
}

fn find_type_validator(dict: &PyDict) -> PyResult<Box<dyn TypeValidator>> {
    let type_: String = dict_get!(dict, "type", String).ok_or_else(|| PyKeyError::new_err("'type' is required"))?;

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
    )
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct ValidatorCallable {
    type_validator: Box<dyn TypeValidator>,
}

#[pymethods]
impl ValidatorCallable {
    fn __call__(&self, py: Python, arg: &PyAny) -> PyResult<PyObject> {
        match self.type_validator.validate(py, arg) {
            Ok(obj) => Ok(obj),
            Err(ValError::LineErrors(line_errors)) => Err(ValidationError::new_err((line_errors, "Model".to_string()))),
            Err(ValError::InternalErr(err)) => Err(err),
        }
    }

    fn __repr__(&self) -> PyResult<String> {
        Ok(format!("ValidatorCallable({:?})", self.type_validator))
    }
}

pub trait TypeValidator: Send + Debug {
    fn is_match(type_: &str, dict: &PyDict) -> bool
    where
        Self: Sized;

    fn build(dict: &PyDict) -> PyResult<Self>
    where
        Self: Sized;

    fn validate(&self, py: Python, obj: &PyAny) -> ValResult<PyObject>;

    fn clone_dyn(&self) -> Box<dyn TypeValidator>;
}

impl Clone for Box<dyn TypeValidator> {
    fn clone(&self) -> Self {
        self.clone_dyn()
    }
}
