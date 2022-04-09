use std::fmt::Debug;

use pyo3::exceptions::{PyKeyError, PyTypeError};
use pyo3::prelude::*;
use pyo3::types::{IntoPyDict, PyAny, PyDict};
use pyo3::ToPyObject;

use crate::utils::{dict_get, py_error};

mod bool;
mod float;
mod int;
mod list;
mod model;
mod none;
mod string;
mod dict;

// TODO date, datetime, set, tuple, bytes, custom types, dict, union, literal

pub trait TypeValidator: Send + Debug {
    fn is_match(type_: &str, dict: &PyDict) -> bool
    where
        Self: Sized;

    fn build(dict: &PyDict) -> PyResult<Self>
    where
        Self: Sized;

    fn validate(&self, py: Python, obj: PyObject) -> PyResult<PyObject>;

    fn clone_dyn(&self) -> Box<dyn TypeValidator>;
}

impl Clone for Box<dyn TypeValidator> {
    fn clone(&self) -> Self {
        self.clone_dyn()
    }
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct Validator {
    type_validator: Box<dyn TypeValidator>,
    external_validator: Option<PyObject>,
}

impl Validator {
    pub fn build(obj: &PyAny) -> PyResult<Self> {
        let dict: &PyDict = obj.extract()?;
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
        })
    }
}

#[pymethods]
impl Validator {
    #[new]
    pub fn py_new(obj: &PyAny) -> PyResult<Self> {
        Self::build(obj)
    }

    fn validate(&self, py: Python, obj: PyObject) -> PyResult<PyObject> {
        if let Some(external_validator) = &self.external_validator {
            let validator_kwarg = ValidatorCallable::new(self.type_validator.clone());
            let kwargs = [("validator", validator_kwarg.into_py(py))];
            let result = external_validator.call(py, (), Some(kwargs.into_py_dict(py)))?;
            Ok(result)
        } else {
            self.type_validator.validate(py, obj)
        }
    }

    fn __repr__(&self) -> PyResult<String> {
        Ok(format!("Validator({:?})", self))
    }
}

fn find_type_validator(dict: &PyDict) -> PyResult<Box<dyn TypeValidator>> {
    let type_: String = dict_get!(dict, "type", String).ok_or(PyKeyError::new_err("'type' is required"))?;

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

    macro_rules! all_validators {
        // single validator - will be called last by variant below
        ($validator:path) => {
            if_else!($validator, {
                return py_error!("unknown type: '{}'", type_);
            })
        };
        // without a trailing comma
        ($validator:path, $($validators:path),+) => {
            if_else!($validator, {
                all_validators!($($validators),+)
            })
        };
        // with a trailing comma
        ($validator:path, $($validators:path,)+) => {
            if_else!($validator, {
                all_validators!($($validators),+)
            })
        };
    }

    // order matters here!
    // e.g. SimpleStringValidator must come before FullStringValidator
    all_validators!(
        self::none::NoneValidator,
        self::bool::BoolValidator,
        self::string::SimpleStringValidator,
        self::string::FullStringValidator,
        self::int::SimpleIntValidator,
        self::int::FullIntValidator,
        self::float::SimpleFloatValidator,
        self::float::FullFloatValidator,
        self::list::ListValidator,
        self::dict::DictValidator,
        self::model::ModelValidator,
    )
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct ValidatorCallable {
    type_validator: Box<dyn TypeValidator>,
}

impl ValidatorCallable {
    fn new(type_validator: Box<dyn TypeValidator>) -> Self {
        Self { type_validator }
    }
}

#[pymethods]
impl ValidatorCallable {
    fn __call__(&self, py: Python, arg: PyObject) -> PyResult<PyObject> {
        self.type_validator.validate(py, arg)
    }

    fn __repr__(&self) -> PyResult<String> {
        Ok(format!("ValidatorCallable({:?})", self))
    }
}
