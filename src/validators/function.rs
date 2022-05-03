use pyo3::exceptions::{PyAssertionError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict};

use crate::build_tools::{py_error, SchemaDict};
use crate::errors::{as_validation_err, val_line_error, ErrorKind, InputValue, ValError, ValLineError, ValResult};
use crate::input::Input;

use super::{build_validator, BuildValidator, CombinedValidator, Extra, SlotsBuilder, Validator};

#[derive(Debug)]
pub struct FunctionBuilder;

impl BuildValidator for FunctionBuilder {
    const EXPECTED_TYPE: &'static str = "function";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        slots_builder: &mut SlotsBuilder,
    ) -> PyResult<CombinedValidator> {
        let mode: &str = schema.get_as_req("mode")?;
        match mode {
            "before" => FunctionBeforeValidator::build(schema, config, slots_builder),
            "after" => FunctionAfterValidator::build(schema, config, slots_builder),
            "plain" => FunctionPlainValidator::build(schema, config),
            "wrap" => FunctionWrapValidator::build(schema, config, slots_builder),
            _ => py_error!("Unexpected function mode {:?}", mode),
        }
    }
}

macro_rules! kwargs {
    ($py:ident, $($k:expr => $v:expr),* $(,)?) => {{
        Some(pyo3::types::IntoPyDict::into_py_dict([$(($k, $v.into_py($py)),)*], $py).into())
    }};
}

macro_rules! impl_build {
    ($name:ident) => {
        impl $name {
            pub fn build(
                schema: &PyDict,
                config: Option<&PyDict>,
                slots_builder: &mut SlotsBuilder,
            ) -> PyResult<CombinedValidator> {
                Ok(Self {
                    validator: Box::new(build_validator(schema.get_as_req("schema")?, config, slots_builder)?.0),
                    func: get_function(schema)?,
                    config: config.map(|c| c.into()),
                }
                .into())
            }
        }
    };
}

#[derive(Debug, Clone)]
pub struct FunctionBeforeValidator {
    validator: Box<CombinedValidator>,
    func: PyObject,
    config: Option<Py<PyDict>>,
}

impl_build!(FunctionBeforeValidator);

impl Validator for FunctionBeforeValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
        slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        let kwargs = kwargs!(py, "data" => extra.data, "config" => self.config.as_ref());
        let value = self
            .func
            .call(py, (input.to_py(py),), kwargs)
            .map_err(|e| convert_err(py, e, input))?;
        // maybe there's some way to get the PyAny here and explicitly tell rust it should have lifespan 'a?
        let new_input: &PyAny = value.as_ref(py);
        match self.validator.validate(py, new_input, extra, slots) {
            Ok(v) => Ok(v),
            Err(ValError::InternalErr(err)) => Err(ValError::InternalErr(err)),
            Err(ValError::LineErrors(line_errors)) => {
                // we have to be explicit about copying line errors here and converting the input value
                Err(ValError::LineErrors(
                    line_errors
                        .into_iter()
                        .map(|line_error| ValLineError {
                            kind: line_error.kind,
                            location: line_error.location,
                            message: line_error.message,
                            input_value: InputValue::PyObject(line_error.input_value.to_py(py)),
                            context: line_error.context,
                        })
                        .collect(),
                ))
            }
        }
    }

    fn get_name(&self, _py: Python) -> String {
        "function-before".to_string()
    }
}

#[derive(Debug, Clone)]
pub struct FunctionAfterValidator {
    validator: Box<CombinedValidator>,
    func: PyObject,
    config: Option<Py<PyDict>>,
}

impl_build!(FunctionAfterValidator);

impl Validator for FunctionAfterValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
        slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        let v = self.validator.validate(py, input, extra, slots)?;
        let kwargs = kwargs!(py, "data" => extra.data, "config" => self.config.as_ref());
        self.func.call(py, (v,), kwargs).map_err(|e| convert_err(py, e, input))
    }

    fn get_name(&self, _py: Python) -> String {
        "function-after".to_string()
    }
}

#[derive(Debug, Clone)]
pub struct FunctionPlainValidator {
    func: PyObject,
    config: Option<Py<PyDict>>,
}

impl FunctionPlainValidator {
    pub fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<CombinedValidator> {
        Ok(Self {
            func: get_function(schema)?,
            config: config.map(|c| c.into()),
        }
        .into())
    }
}

impl Validator for FunctionPlainValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
        _slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        let kwargs = kwargs!(py, "data" => extra.data, "config" => self.config.as_ref());
        self.func
            .call(py, (input.to_py(py),), kwargs)
            .map_err(|e| convert_err(py, e, input))
    }

    fn get_name(&self, _py: Python) -> String {
        "function-plain".to_string()
    }
}

#[derive(Debug, Clone)]
pub struct FunctionWrapValidator {
    validator: Box<CombinedValidator>,
    func: PyObject,
    config: Option<Py<PyDict>>,
}

impl_build!(FunctionWrapValidator);

impl Validator for FunctionWrapValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
        slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        let validator_kwarg = ValidatorCallable {
            validator: self.validator.clone(),
            slots: slots.to_vec(),
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

    fn get_name(&self, _py: Python) -> String {
        "function-wrap".to_string()
    }
}

#[pyclass]
#[derive(Debug, Clone)]
struct ValidatorCallable {
    validator: Box<CombinedValidator>,
    slots: Vec<CombinedValidator>,
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
            .validate(py, arg, &extra, &self.slots)
            .map_err(|e| as_validation_err(py, "Model", e))
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

fn convert_err<'a>(py: Python<'a>, err: PyErr, input: &'a dyn Input) -> ValError<'a> {
    // Only ValueError and AssertionError are considered as validation errors,
    // TypeError is now considered as a runtime error to catch errors in function signatures
    let kind = if err.is_instance_of::<PyValueError>(py) {
        ErrorKind::ValueError
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
    let line_error = val_line_error!(
        input_value = InputValue::InputRef(input),
        kind = kind,
        message = message
    );
    ValError::LineErrors(vec![line_error])
}
