use pyo3::exceptions::{PyAssertionError, PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict};

use super::{Extra, ValError, Validator};
use crate::errors::{map_validation_error, val_line_error, ErrorKind, ValResult};
use crate::utils::{dict, dict_get_required, py_error};
use crate::validators::build_validator;

macro_rules! kwargs {
    ($py:ident, $($k:expr => $v:expr),*) => {{
        Some(dict!($py, $($k => $v),*))
    }};
}

macro_rules! build {
    () => {
        fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
            Ok(Box::new(Self {
                validator: build_validator(dict_get_required!(schema, "field", &PyDict)?, config)?,
                func: get_function(schema)?,
                config: config.map(|c| c.into()),
            }))
        }
    };
}

#[derive(Debug, Clone)]
pub struct FunctionBeforeValidator {
    validator: Box<dyn Validator>,
    func: PyObject,
    config: Option<Py<PyDict>>,
}

impl FunctionBeforeValidator {
    pub const EXPECTED_TYPE: &'static str = "function-before";
}

impl Validator for FunctionBeforeValidator {
    build!();

    fn validate(&self, py: Python, input: &PyAny, extra: &Extra) -> ValResult<PyObject> {
        let kwargs = kwargs!(py, "data" => extra.data, "config" => self.config.as_ref());
        let value = self
            .func
            .call(py, (input,), kwargs)
            .map_err(|e| convert_err(py, e, input))?;
        let v: &PyAny = value.as_ref(py);
        self.validator.validate(py, v, extra)
    }

    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}

#[derive(Debug, Clone)]
pub struct FunctionAfterValidator {
    validator: Box<dyn Validator>,
    func: PyObject,
    config: Option<Py<PyDict>>,
}

impl FunctionAfterValidator {
    pub const EXPECTED_TYPE: &'static str = "function-after";
}

impl Validator for FunctionAfterValidator {
    build!();

    fn validate(&self, py: Python, input: &PyAny, extra: &Extra) -> ValResult<PyObject> {
        let v = self.validator.validate(py, input, extra)?;
        let kwargs = kwargs!(py, "data" => extra.data, "config" => self.config.as_ref());
        self.func.call(py, (v,), kwargs).map_err(|e| convert_err(py, e, input))
    }

    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}

#[derive(Debug, Clone)]
pub struct FunctionPlainValidator {
    func: PyObject,
    config: Option<Py<PyDict>>,
}

impl FunctionPlainValidator {
    pub const EXPECTED_TYPE: &'static str = "function-plain";
}

impl Validator for FunctionPlainValidator {
    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        Ok(Box::new(Self {
            func: get_function(schema)?,
            config: config.map(|c| c.into()),
        }))
    }

    fn validate(&self, py: Python, input: &PyAny, extra: &Extra) -> ValResult<PyObject> {
        let kwargs = kwargs!(py, "data" => extra.data, "config" => self.config.as_ref());
        self.func
            .call(py, (input,), kwargs)
            .map_err(|e| convert_err(py, e, input))
    }

    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}

#[derive(Debug, Clone)]
pub struct FunctionWrapValidator {
    validator: Box<dyn Validator>,
    func: PyObject,
    config: Option<Py<PyDict>>,
}

impl FunctionWrapValidator {
    pub const EXPECTED_TYPE: &'static str = "function-wrap";
}

impl Validator for FunctionWrapValidator {
    build!();

    fn validate(&self, py: Python, input: &PyAny, extra: &Extra) -> ValResult<PyObject> {
        let validator_kwarg = ValidatorCallable {
            validator: self.validator.clone(),
            data: extra.data.map(|d| d.into_py(py)),
            field: extra.field.map(|f| f.to_string()),
        };
        let kwargs = kwargs!(
            py,
            "validator" => validator_kwarg,
            "data" => extra.data,
            "config" => self.config.as_ref()
        );
        self.func
            .call(py, (input,), kwargs)
            .map_err(|e| convert_err(py, e, input))
    }

    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct ValidatorCallable {
    validator: Box<dyn Validator>,
    data: Option<Py<PyDict>>,
    field: Option<String>,
}

#[pymethods]
impl ValidatorCallable {
    fn __call__(&self, py: Python, arg: &PyAny) -> PyResult<PyObject> {
        let extra = Extra {
            data: self.data.as_ref().map(|data| data.as_ref(py)),
            field: self.field.as_deref(),
        };
        self.validator
            .validate(py, arg, &extra)
            .map_err(|e| map_validation_error("Model", e))
    }

    fn __repr__(&self) -> String {
        format!("ValidatorCallable({:?})", self.validator)
    }
    fn __str__(&self) -> String {
        self.__repr__()
    }
}

fn get_function(schema: &PyDict) -> PyResult<PyObject> {
    match schema.get_item("function") {
        Some(obj) => {
            if obj.is_callable() {
                Ok(obj.into_py(obj.py()))
            } else {
                return py_error!("function must be callable");
            }
        }
        None => py_error!(r#""function" key is required"#),
    }
}

fn convert_err(py: Python, err: PyErr, input: &PyAny) -> ValError {
    let kind = if err.is_instance_of::<PyValueError>(py) {
        ErrorKind::ValueError
    } else if err.is_instance_of::<PyTypeError>(py) {
        ErrorKind::TypeError
    } else if err.is_instance_of::<PyAssertionError>(py) {
        ErrorKind::AssertionError
    } else {
        return ValError::InternalErr(err);
    };

    let message = match err.value(py).str() {
        Ok(s) => Some(s.to_string()),
        Err(err) => return ValError::InternalErr(err),
    };
    #[allow(clippy::redundant_field_names)]
    let line_error = val_line_error!(py, input, kind = kind, message = message);
    ValError::LineErrors(vec![line_error])
}
