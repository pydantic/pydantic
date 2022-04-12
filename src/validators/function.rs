use pyo3::exceptions::{PyAssertionError, PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{IntoPyDict, PyAny, PyDict};

use super::{ValError, ValidationError, Validator};
use crate::errors::{val_line_error, ErrorKind, ValResult};
use crate::utils::{dict_get_required, py_error};
use crate::validators::build_validator;

macro_rules! kwargs {
    ($py:ident, $($k:expr => $v:expr),*) => {{
        Some([$(($k, $v.into_py($py)),)*].into_py_dict($py))
    }};
}

macro_rules! build {
    () => {
        fn build(dict: &PyDict) -> PyResult<Self> {
            Ok(Self {
                validator: build_validator(dict_get_required!(dict, "field", &PyDict)?)?,
                func: get_function(dict)?,
            })
        }
    };
}

#[derive(Debug, Clone)]
pub struct FunctionBeforeValidator {
    validator: Box<dyn Validator>,
    func: PyObject,
}

impl Validator for FunctionBeforeValidator {
    fn is_match(type_: &str, _dict: &PyDict) -> bool {
        type_ == "function-before"
    }

    build!();

    fn validate(&self, py: Python, input: &PyAny, data: &PyDict) -> ValResult<PyObject> {
        let value = self
            .func
            .call(py, (input,), kwargs!(py, "data" => data.as_ref()))
            .map_err(|e| convert_err(py, e, input))?;
        let v: &PyAny = value.as_ref(py);
        self.validator.validate(py, v, data)
    }

    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}

#[derive(Debug, Clone)]
pub struct FunctionAfterValidator {
    validator: Box<dyn Validator>,
    func: PyObject,
}

impl Validator for FunctionAfterValidator {
    fn is_match(type_: &str, _dict: &PyDict) -> bool {
        type_ == "function-after"
    }

    build!();

    fn validate(&self, py: Python, input: &PyAny, data: &PyDict) -> ValResult<PyObject> {
        let v = self.validator.validate(py, input, data)?;
        self.func
            .call(py, (v,), kwargs!(py, "data" => data.as_ref()))
            .map_err(|e| convert_err(py, e, input))
    }

    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}

#[derive(Debug, Clone)]
pub struct FunctionPlainValidator {
    func: PyObject,
}

impl Validator for FunctionPlainValidator {
    fn is_match(type_: &str, _dict: &PyDict) -> bool {
        type_ == "function-plain"
    }

    fn build(dict: &PyDict) -> PyResult<Self> {
        Ok(Self {
            func: get_function(dict)?,
        })
    }

    fn validate(&self, py: Python, input: &PyAny, data: &PyDict) -> ValResult<PyObject> {
        self.func
            .call(py, (input,), kwargs!(py, "data" => data.as_ref()))
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
}

impl Validator for FunctionWrapValidator {
    fn is_match(type_: &str, _dict: &PyDict) -> bool {
        type_ == "function-wrap"
    }

    build!();

    fn validate(&self, py: Python, input: &PyAny, data: &PyDict) -> ValResult<PyObject> {
        let validator_kwarg = ValidatorCallable {
            validator: self.validator.clone(),
            data: data.into_py(py),
        };
        let kwargs = kwargs!(py, "validator" => validator_kwarg, "data" => data.as_ref());
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
    data: Py<PyDict>,
}

#[pymethods]
impl ValidatorCallable {
    fn __call__(&self, py: Python, arg: &PyAny) -> PyResult<PyObject> {
        match self.validator.validate(py, arg, self.data.as_ref(py)) {
            Ok(output) => Ok(output),
            Err(ValError::LineErrors(line_errors)) => Err(ValidationError::new_err((line_errors, "Model".to_string()))),
            Err(ValError::InternalErr(err)) => Err(err),
        }
    }

    fn __repr__(&self) -> String {
        format!("ValidatorCallable({:?})", self.validator)
    }
    fn __str__(&self) -> String {
        self.__repr__()
    }
}

fn get_function(dict: &PyDict) -> PyResult<PyObject> {
    match dict.get_item("function") {
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
