use pyo3::exceptions::{PyAssertionError, PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict};

use crate::build_macros::{dict, dict_get_required, py_error};
use crate::errors::{map_validation_error, val_line_error, ErrorKind, ValError, ValResult};
use crate::input::Input;
use crate::validators::build_validator;

use super::{Extra, Validator};

#[derive(Debug, Clone)]
pub struct FunctionValidator;

impl FunctionValidator {
    pub const EXPECTED_TYPE: &'static str = "function";
}

impl Validator for FunctionValidator {
    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        let mode = dict_get_required!(schema, "mode", &str)?;
        match mode {
            "before" => FunctionBeforeValidator::build(schema, config),
            "after" => FunctionAfterValidator::build(schema, config),
            "plain" => FunctionPlainValidator::build(schema, config),
            "wrap" => FunctionWrapValidator::build(schema, config),
            _ => py_error!("Unexpected function mode {:?}", mode),
        }
    }

    fn validate(&self, _py: Python, _input: &dyn Input, _extra: &Extra) -> ValResult<PyObject> {
        unimplemented!("FunctionValidator is never used directly")
    }

    fn validate_strict(&self, py: Python, input: &dyn Input, extra: &Extra) -> ValResult<PyObject> {
        self.validate(py, input, extra)
    }

    fn get_name(&self, _py: Python) -> String {
        Self::EXPECTED_TYPE.to_string()
    }

    #[no_coverage]
    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}

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
struct FunctionBeforeValidator {
    validator: Box<dyn Validator>,
    func: PyObject,
    config: Option<Py<PyDict>>,
}

impl Validator for FunctionBeforeValidator {
    build!();

    fn validate(&self, py: Python, input: &dyn Input, extra: &Extra) -> ValResult<PyObject> {
        let kwargs = kwargs!(py, "data" => extra.data, "config" => self.config.as_ref());
        let value = self
            .func
            .call(py, (input.to_py(py),), kwargs)
            .map_err(|e| convert_err(py, e, input))?;
        let v: &PyAny = value.as_ref(py);
        self.validator.validate(py, v, extra)
    }

    fn validate_strict(&self, py: Python, input: &dyn Input, extra: &Extra) -> ValResult<PyObject> {
        self.validate(py, input, extra)
    }

    fn get_name(&self, _py: Python) -> String {
        "function-before".to_string()
    }

    #[no_coverage]
    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}

#[derive(Debug, Clone)]
struct FunctionAfterValidator {
    validator: Box<dyn Validator>,
    func: PyObject,
    config: Option<Py<PyDict>>,
}

impl Validator for FunctionAfterValidator {
    build!();

    fn validate(&self, py: Python, input: &dyn Input, extra: &Extra) -> ValResult<PyObject> {
        let v = self.validator.validate(py, input, extra)?;
        let kwargs = kwargs!(py, "data" => extra.data, "config" => self.config.as_ref());
        self.func.call(py, (v,), kwargs).map_err(|e| convert_err(py, e, input))
    }

    fn validate_strict(&self, py: Python, input: &dyn Input, extra: &Extra) -> ValResult<PyObject> {
        self.validate(py, input, extra)
    }

    fn get_name(&self, _py: Python) -> String {
        "function-after".to_string()
    }

    #[no_coverage]
    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}

#[derive(Debug, Clone)]
struct FunctionPlainValidator {
    func: PyObject,
    config: Option<Py<PyDict>>,
}

impl Validator for FunctionPlainValidator {
    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        Ok(Box::new(Self {
            func: get_function(schema)?,
            config: config.map(|c| c.into()),
        }))
    }

    fn validate(&self, py: Python, input: &dyn Input, extra: &Extra) -> ValResult<PyObject> {
        let kwargs = kwargs!(py, "data" => extra.data, "config" => self.config.as_ref());
        self.func
            .call(py, (input.to_py(py),), kwargs)
            .map_err(|e| convert_err(py, e, input))
    }

    fn validate_strict(&self, py: Python, input: &dyn Input, extra: &Extra) -> ValResult<PyObject> {
        self.validate(py, input, extra)
    }

    fn get_name(&self, _py: Python) -> String {
        "function-plain".to_string()
    }

    #[no_coverage]
    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}

#[derive(Debug, Clone)]
struct FunctionWrapValidator {
    validator: Box<dyn Validator>,
    func: PyObject,
    config: Option<Py<PyDict>>,
}

impl Validator for FunctionWrapValidator {
    build!();

    fn validate(&self, py: Python, input: &dyn Input, extra: &Extra) -> ValResult<PyObject> {
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
            .call(py, (input.to_py(py),), kwargs)
            .map_err(|e| convert_err(py, e, input))
    }

    fn validate_strict(&self, py: Python, input: &dyn Input, extra: &Extra) -> ValResult<PyObject> {
        self.validate(py, input, extra)
    }

    fn get_name(&self, _py: Python) -> String {
        "function-wrap".to_string()
    }

    #[no_coverage]
    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}

#[pyclass]
#[derive(Debug, Clone)]
struct ValidatorCallable {
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
                Ok(obj.into())
            } else {
                return py_error!("function must be callable");
            }
        }
        None => py_error!(r#""function" key is required"#),
    }
}

fn convert_err(py: Python, err: PyErr, input: &dyn Input) -> ValError {
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
