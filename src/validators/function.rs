use pyo3::exceptions::{PyAssertionError, PyValueError};
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict};

use crate::build_tools::{py_error, SchemaDict};
use crate::errors::{ErrorKind, ValError, ValResult, ValidationError};
use crate::input::Input;
use crate::recursion_guard::RecursionGuard;

use super::{build_validator, BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug)]
pub struct FunctionBuilder;

impl BuildValidator for FunctionBuilder {
    const EXPECTED_TYPE: &'static str = "function";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext,
    ) -> PyResult<CombinedValidator> {
        let mode: &str = schema.get_as_req(intern!(schema.py(), "mode"))?;
        match mode {
            "before" => FunctionBeforeValidator::build(schema, config, build_context),
            "after" => FunctionAfterValidator::build(schema, config, build_context),
            "plain" => FunctionPlainValidator::build(schema, config),
            "wrap" => FunctionWrapValidator::build(schema, config, build_context),
            _ => py_error!("Unexpected function mode {:?}", mode),
        }
    }
}

macro_rules! kwargs {
    ($py:ident, $($k:ident: $v:expr),* $(,)?) => {{
        Some(pyo3::types::IntoPyDict::into_py_dict([$((stringify!($k), $v.into_py($py)),)*], $py).into())
    }};
}

macro_rules! impl_build {
    ($impl_name:ident, $name:literal) => {
        impl $impl_name {
            pub fn build(
                schema: &PyDict,
                config: Option<&PyDict>,
                build_context: &mut BuildContext,
            ) -> PyResult<CombinedValidator> {
                let py = schema.py();
                let validator = build_validator(schema.get_as_req(intern!(py, "schema"))?, config, build_context)?.0;
                let name = format!("{}[{}]", $name, validator.get_name());
                Ok(Self {
                    validator: Box::new(validator),
                    func: schema.get_as_req::<&PyAny>(intern!(py, "function"))?.into_py(py),
                    config: match config {
                        Some(c) => c.into(),
                        None => py.None(),
                    },
                    name,
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
    config: PyObject,
    name: String,
}

impl_build!(FunctionBeforeValidator, "function-before");

impl Validator for FunctionBeforeValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let kwargs = kwargs!(py, data: extra.data, config: self.config.clone_ref(py), context: extra.context);
        let value = self
            .func
            .call(py, (input.to_object(py),), kwargs)
            .map_err(|e| convert_err(py, e, input))?;
        // maybe there's some way to get the PyAny here and explicitly tell rust it should have lifespan 'a?
        let new_input: &PyAny = value.as_ref(py);
        match self.validator.validate(py, new_input, extra, slots, recursion_guard) {
            Ok(v) => Ok(v),
            Err(ValError::InternalErr(err)) => Err(ValError::InternalErr(err)),
            Err(ValError::LineErrors(line_errors)) => {
                // we have to be explicit about clone line errors to a new lifetime since new_input doesn't have
                // the 'data lifetime
                Err(ValError::LineErrors(
                    line_errors
                        .into_iter()
                        .map(|line_error| line_error.into_new(py))
                        .collect(),
                ))
            }
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, build_context: &BuildContext) -> PyResult<()> {
        self.validator.complete(build_context)
    }
}

#[derive(Debug, Clone)]
pub struct FunctionAfterValidator {
    validator: Box<CombinedValidator>,
    func: PyObject,
    config: PyObject,
    name: String,
}

impl_build!(FunctionAfterValidator, "function-after");

impl Validator for FunctionAfterValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let v = self.validator.validate(py, input, extra, slots, recursion_guard)?;
        let kwargs = kwargs!(py, data: extra.data, config: self.config.clone_ref(py), context: extra.context);
        self.func.call(py, (v,), kwargs).map_err(|e| convert_err(py, e, input))
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, build_context: &BuildContext) -> PyResult<()> {
        self.validator.complete(build_context)
    }
}

#[derive(Debug, Clone)]
pub struct FunctionPlainValidator {
    func: PyObject,
    config: PyObject,
}

impl FunctionPlainValidator {
    pub fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<CombinedValidator> {
        let py = schema.py();
        if schema.get_item(intern!(py, "schema")).is_some() {
            py_error!("Plain functions should not include a sub-schema")
        } else {
            Ok(Self {
                func: schema.get_as_req::<&PyAny>(intern!(py, "function"))?.into_py(py),
                config: match config {
                    Some(c) => c.into(),
                    None => py.None(),
                },
            }
            .into())
        }
    }
}

impl Validator for FunctionPlainValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let kwargs = kwargs!(py, data: extra.data, config: self.config.clone_ref(py), context: extra.context);
        self.func
            .call(py, (input.to_object(py),), kwargs)
            .map_err(|e| convert_err(py, e, input))
    }

    fn get_name(&self) -> &str {
        "function-plain"
    }
}

#[derive(Debug, Clone)]
pub struct FunctionWrapValidator {
    validator: Box<CombinedValidator>,
    func: PyObject,
    config: PyObject,
    name: String,
}

impl_build!(FunctionWrapValidator, "function-wrap");

impl Validator for FunctionWrapValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let validator_kwarg = ValidatorCallable {
            validator: self.validator.clone(),
            slots: slots.to_vec(),
            data: extra.data.map(|d| d.into_py(py)),
            field: extra.field.map(|f| f.to_string()),
            strict: extra.strict,
            context: extra.context.map(|d| d.into_py(py)),
            recursion_guard: recursion_guard.clone(),
        };
        let kwargs = kwargs!(
            py,
            validator: validator_kwarg,
            data: extra.data,
            config: self.config.clone_ref(py),
            context: extra.context,
        );
        self.func
            .call(py, (input.to_object(py),), kwargs)
            .map_err(|e| convert_err(py, e, input))
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, build_context: &BuildContext) -> PyResult<()> {
        self.validator.complete(build_context)
    }
}

#[pyclass]
#[derive(Debug, Clone)]
struct ValidatorCallable {
    validator: Box<CombinedValidator>,
    slots: Vec<CombinedValidator>,
    data: Option<Py<PyDict>>,
    field: Option<String>,
    strict: Option<bool>,
    context: Option<PyObject>,
    recursion_guard: RecursionGuard,
}

#[pymethods]
impl ValidatorCallable {
    fn __call__(&mut self, py: Python, arg: &PyAny) -> PyResult<PyObject> {
        let extra = Extra {
            data: self.data.as_ref().map(|data| data.as_ref(py)),
            field: self.field.as_deref(),
            strict: self.strict,
            context: self.context.as_ref().map(|data| data.as_ref(py)),
        };
        self.validator
            .validate(py, arg, &extra, &self.slots, &mut self.recursion_guard)
            .map_err(|e| ValidationError::from_val_error(py, "Model".to_object(py), e))
    }

    fn __repr__(&self) -> String {
        format!("ValidatorCallable({:?})", self.validator)
    }

    fn __str__(&self) -> String {
        self.__repr__()
    }
}

fn convert_err<'a>(py: Python<'a>, err: PyErr, input: &'a impl Input<'a>) -> ValError<'a> {
    // Only ValueError and AssertionError are considered as validation errors,
    // TypeError is now considered as a runtime error to catch errors in function signatures
    if err.is_instance_of::<PyValueError>(py) {
        if let Ok(validation_error) = err.value(py).extract::<ValidationError>() {
            validation_error.into()
        } else {
            match py_err_string(py, err) {
                Ok(error) => ValError::new(ErrorKind::ValueError { error }, input),
                Err(e) => e,
            }
        }
    } else if err.is_instance_of::<PyAssertionError>(py) {
        match py_err_string(py, err) {
            Ok(error) => ValError::new(ErrorKind::AssertionError { error }, input),
            Err(e) => e,
        }
    } else {
        ValError::InternalErr(err)
    }
}

fn py_err_string(py: Python, err: PyErr) -> ValResult<String> {
    match err.value(py).str() {
        Ok(py_string) => match py_string.to_str() {
            Ok(s) => match s.is_empty() {
                true => Ok("Unknown error".to_string()),
                false => Ok(s.to_string()),
            },
            Err(e) => Err(ValError::InternalErr(e)),
        },
        Err(e) => Err(ValError::InternalErr(e)),
    }
}
