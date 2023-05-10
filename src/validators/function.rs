use pyo3::exceptions::{PyAssertionError, PyAttributeError, PyRuntimeError, PyTypeError, PyValueError};
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict, PyString};

use crate::build_tools::{function_name, py_err, SchemaDict};
use crate::errors::{
    ErrorType, LocItem, PydanticCustomError, PydanticKnownError, PydanticOmit, ValError, ValResult, ValidationError,
};
use crate::input::Input;
use crate::recursion_guard::RecursionGuard;

use super::generator::InternalValidator;
use super::{
    build_validator, BuildValidator, CombinedValidator, Definitions, DefinitionsBuilder, Extra, InputType, Validator,
};

fn destructure_function_schema(schema: &PyDict) -> PyResult<(bool, bool, &PyAny)> {
    let func_dict: &PyDict = schema.get_as_req(intern!(schema.py(), "function"))?;
    let function: &PyAny = func_dict.get_as_req(intern!(schema.py(), "function"))?;
    let func_type: &str = func_dict.get_as_req(intern!(schema.py(), "type"))?;
    let (is_field_serializer, info_arg) = match func_type {
        "field" => (true, true),
        "general" => (false, true),
        "no-info" => (false, false),
        _ => unreachable!(),
    };
    Ok((is_field_serializer, info_arg, function))
}

macro_rules! impl_build {
    ($impl_name:ident, $name:literal) => {
        impl BuildValidator for $impl_name {
            const EXPECTED_TYPE: &'static str = $name;
            fn build(
                schema: &PyDict,
                config: Option<&PyDict>,
                definitions: &mut DefinitionsBuilder<CombinedValidator>,
            ) -> PyResult<CombinedValidator> {
                let py = schema.py();
                let validator = build_validator(schema.get_as_req(intern!(py, "schema"))?, config, definitions)?;
                let (is_field_validator, info_arg, function) = destructure_function_schema(schema)?;
                let name = format!(
                    "{}[{}(), {}]",
                    $name,
                    function_name(function)?,
                    validator.get_name()
                );
                Ok(Self {
                    validator: Box::new(validator),
                    func: function.into_py(py),
                    config: match config {
                        Some(c) => c.into(),
                        None => py.None(),
                    },
                    name,
                    is_field_validator,
                    info_arg,
                }
                .into())
            }
        }
    };
}

macro_rules! impl_validator {
    ($name:ident) => {
        impl Validator for $name {
            fn validate<'s, 'data>(
                &'s self,
                py: Python<'data>,
                input: &'data impl Input<'data>,
                extra: &Extra,
                definitions: &'data Definitions<CombinedValidator>,
                recursion_guard: &'s mut RecursionGuard,
            ) -> ValResult<'data, PyObject> {
                let validate =
                    move |v: &'data PyAny, e: &Extra| self.validator.validate(py, v, e, definitions, recursion_guard);
                self._validate(validate, py, input.to_object(py).into_ref(py), extra)
            }
            fn validate_assignment<'s, 'data: 's>(
                &'s self,
                py: Python<'data>,
                obj: &'data PyAny,
                field_name: &'data str,
                field_value: &'data PyAny,
                extra: &Extra,
                definitions: &'data Definitions<CombinedValidator>,
                recursion_guard: &'s mut RecursionGuard,
            ) -> ValResult<'data, PyObject> {
                let validate = move |v: &'data PyAny, e: &Extra| {
                    self.validator
                        .validate_assignment(py, v, field_name, field_value, e, definitions, recursion_guard)
                };
                self._validate(validate, py, obj, extra)
            }

            fn different_strict_behavior(
                &self,
                definitions: Option<&DefinitionsBuilder<CombinedValidator>>,
                ultra_strict: bool,
            ) -> bool {
                if ultra_strict {
                    self.validator
                        .different_strict_behavior(definitions, ultra_strict)
                } else {
                    true
                }
            }

            fn get_name(&self) -> &str {
                &self.name
            }

            fn complete(&mut self, definitions: &DefinitionsBuilder<CombinedValidator>) -> PyResult<()> {
                self.validator.complete(definitions)
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
    is_field_validator: bool,
    info_arg: bool,
}

impl_build!(FunctionBeforeValidator, "function-before");

impl FunctionBeforeValidator {
    fn _validate<'s, 'data>(
        &'s self,
        mut call: impl FnMut(&'data PyAny, &Extra) -> ValResult<'data, PyObject>,
        py: Python<'data>,
        input: &'data PyAny,
        extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        let r = if self.info_arg {
            let info = ValidationInfo::new(py, extra, &self.config, self.is_field_validator)?;
            self.func.call1(py, (input.to_object(py), info))
        } else {
            self.func.call1(py, (input.to_object(py),))
        };
        let value = r.map_err(|e| convert_err(py, e, input))?;
        call(value.into_ref(py), extra)
    }
}

impl_validator!(FunctionBeforeValidator);

#[derive(Debug, Clone)]
pub struct FunctionAfterValidator {
    validator: Box<CombinedValidator>,
    func: PyObject,
    config: PyObject,
    name: String,
    is_field_validator: bool,
    info_arg: bool,
}

impl_build!(FunctionAfterValidator, "function-after");

impl FunctionAfterValidator {
    fn _validate<'s, 'data>(
        &'s self,
        mut call: impl FnMut(&'data PyAny, &Extra) -> ValResult<'data, PyObject>,
        py: Python<'data>,
        input: &'data PyAny,
        extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        let v = call(input, extra)?;
        let r = if self.info_arg {
            let info = ValidationInfo::new(py, extra, &self.config, self.is_field_validator)?;
            self.func.call1(py, (v.to_object(py), info))
        } else {
            self.func.call1(py, (v.to_object(py),))
        };
        r.map_err(|e| convert_err(py, e, input))
    }
}

impl_validator!(FunctionAfterValidator);

#[derive(Debug, Clone)]
pub struct FunctionPlainValidator {
    func: PyObject,
    config: PyObject,
    name: String,
    is_field_validator: bool,
    info_arg: bool,
}

impl BuildValidator for FunctionPlainValidator {
    const EXPECTED_TYPE: &'static str = "function-plain";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        _definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let (is_field_validator, info_arg, function) = destructure_function_schema(schema)?;
        Ok(Self {
            func: function.into_py(py),
            config: match config {
                Some(c) => c.into(),
                None => py.None(),
            },
            name: format!("function-plain[{}()]", function_name(function)?),
            is_field_validator,
            info_arg,
        }
        .into())
    }
}

impl Validator for FunctionPlainValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        _definitions: &'data Definitions<CombinedValidator>,
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let r = if self.info_arg {
            let info = ValidationInfo::new(py, extra, &self.config, self.is_field_validator)?;
            self.func.call1(py, (input.to_object(py), info))
        } else {
            self.func.call1(py, (input.to_object(py),))
        };
        r.map_err(|e| convert_err(py, e, input))
    }

    fn different_strict_behavior(
        &self,
        _definitions: Option<&DefinitionsBuilder<CombinedValidator>>,
        ultra_strict: bool,
    ) -> bool {
        // best guess, should we change this?
        !ultra_strict
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, _definitions: &DefinitionsBuilder<CombinedValidator>) -> PyResult<()> {
        Ok(())
    }
}

#[derive(Debug, Clone)]
pub struct FunctionWrapValidator {
    validator: Box<CombinedValidator>,
    func: PyObject,
    config: PyObject,
    name: String,
    is_field_validator: bool,
    info_arg: bool,
}

impl_build!(FunctionWrapValidator, "function-wrap");

impl FunctionWrapValidator {
    fn _validate<'s, 'data>(
        &'s self,
        handler: &'s PyAny,
        py: Python<'data>,
        input: &'data PyAny,
        extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        let r = if self.info_arg {
            let info = ValidationInfo::new(py, extra, &self.config, self.is_field_validator)?;
            self.func.call1(py, (input.to_object(py), handler, info))
        } else {
            self.func.call1(py, (input.to_object(py), handler))
        };
        r.map_err(|e| convert_err(py, e, input))
    }
}

impl Validator for FunctionWrapValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        definitions: &'data Definitions<CombinedValidator>,
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let handler = ValidatorCallable {
            validator: InternalValidator::new(
                py,
                "ValidatorCallable",
                &self.validator,
                definitions,
                extra,
                recursion_guard,
            ),
        };
        self._validate(
            Py::new(py, handler)?.into_ref(py),
            py,
            input.to_object(py).into_ref(py),
            extra,
        )
    }

    fn validate_assignment<'s, 'data: 's>(
        &'s self,
        py: Python<'data>,
        obj: &'data PyAny,
        field_name: &'data str,
        field_value: &'data PyAny,
        extra: &Extra,
        definitions: &'data Definitions<CombinedValidator>,
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let handler = AssignmentValidatorCallable {
            validator: InternalValidator::new(
                py,
                "ValidatorCallable",
                &self.validator,
                definitions,
                extra,
                recursion_guard,
            ),
            updated_field_name: field_name.to_string(),
            updated_field_value: field_value.to_object(py),
        };
        self._validate(Py::new(py, handler)?.into_ref(py), py, obj, extra)
    }

    fn different_strict_behavior(
        &self,
        definitions: Option<&DefinitionsBuilder<CombinedValidator>>,
        ultra_strict: bool,
    ) -> bool {
        if ultra_strict {
            self.validator.different_strict_behavior(definitions, ultra_strict)
        } else {
            true
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, definitions: &DefinitionsBuilder<CombinedValidator>) -> PyResult<()> {
        self.validator.complete(definitions)
    }
}

#[pyclass(module = "pydantic_core._pydantic_core")]
#[derive(Debug, Clone)]
struct ValidatorCallable {
    validator: InternalValidator,
}

#[pymethods]
impl ValidatorCallable {
    fn __call__(&mut self, py: Python, input_value: &PyAny, outer_location: Option<&PyAny>) -> PyResult<PyObject> {
        let outer_location = match outer_location {
            Some(ol) => match LocItem::try_from(ol) {
                Ok(ol) => Some(ol),
                Err(_) => return py_err!(PyTypeError; "outer_location must be a str or int"),
            },
            None => None,
        };
        self.validator.validate(py, input_value, outer_location)
    }

    fn __repr__(&self) -> String {
        format!("ValidatorCallable({:?})", self.validator)
    }

    fn __str__(&self) -> String {
        self.__repr__()
    }
}

#[pyclass(module = "pydantic_core._pydantic_core")]
#[derive(Debug, Clone)]
struct AssignmentValidatorCallable {
    updated_field_name: String,
    updated_field_value: Py<PyAny>,
    validator: InternalValidator,
}

#[pymethods]
impl AssignmentValidatorCallable {
    fn __call__(&mut self, py: Python, input_value: &PyAny, outer_location: Option<&PyAny>) -> PyResult<PyObject> {
        let outer_location = match outer_location {
            Some(ol) => match LocItem::try_from(ol) {
                Ok(ol) => Some(ol),
                Err(_) => return py_err!(PyTypeError; "outer_location must be a str or int"),
            },
            None => None,
        };
        self.validator.validate_assignment(
            py,
            input_value,
            self.updated_field_name.as_str(),
            self.updated_field_value.as_ref(py),
            outer_location,
        )
    }

    fn __repr__(&self) -> String {
        format!("AssignmentValidatorCallable({:?})", self.validator)
    }

    fn __str__(&self) -> String {
        self.__repr__()
    }
}

macro_rules! py_err_string {
    ($error_value:expr, $type_member:ident, $input:ident) => {
        match $error_value.str() {
            Ok(py_string) => match py_string.to_str() {
                Ok(s) => {
                    let error = match s.is_empty() {
                        true => "Unknown error".to_string(),
                        false => s.to_string(),
                    };
                    ValError::new(ErrorType::$type_member { error }, $input)
                }
                Err(e) => ValError::InternalErr(e),
            },
            Err(e) => ValError::InternalErr(e),
        }
    };
}

/// Only `ValueError` (including `PydanticCustomError` and `ValidationError`) and `AssertionError` are considered
/// as validation errors, `TypeError` is now considered as a runtime error to catch errors in function signatures
pub fn convert_err<'a>(py: Python<'a>, err: PyErr, input: &'a impl Input<'a>) -> ValError<'a> {
    if err.is_instance_of::<PyValueError>(py) {
        if let Ok(pydantic_value_error) = err.value(py).extract::<PydanticCustomError>() {
            pydantic_value_error.into_val_error(input)
        } else if let Ok(pydantic_error_type) = err.value(py).extract::<PydanticKnownError>() {
            pydantic_error_type.into_val_error(input)
        } else if let Ok(validation_error) = err.value(py).extract::<ValidationError>() {
            validation_error.into_py(py)
        } else {
            py_err_string!(err.value(py), ValueError, input)
        }
    } else if err.is_instance_of::<PyAssertionError>(py) {
        py_err_string!(err.value(py), AssertionError, input)
    } else if err.is_instance_of::<PydanticOmit>(py) {
        ValError::Omit
    } else {
        ValError::InternalErr(err)
    }
}

#[pyclass(module = "pydantic_core._pydantic_core")]
pub struct ValidationInfo {
    #[pyo3(get)]
    config: PyObject,
    #[pyo3(get)]
    context: Option<PyObject>,
    data: Option<Py<PyDict>>,
    field_name: Option<String>,
    #[pyo3(get)]
    mode: InputType,
}

impl ValidationInfo {
    fn new(py: Python, extra: &Extra, config: &PyObject, is_field_validator: bool) -> PyResult<Self> {
        if is_field_validator {
            match extra.field_name {
                Some(field_name) => Ok(
                    Self {
                        config: config.clone_ref(py),
                        context: extra.context.map(|v| v.into()),
                        field_name: Some(field_name.to_string()),
                        data: extra.data.map(|v| v.into()),
                        mode: extra.mode,
                    }
                ),
                _ => Err(PyRuntimeError::new_err("This validator expected to be run inside the context of a model field but no model field was found")),
            }
        } else {
            Ok(Self {
                config: config.clone_ref(py),
                context: extra.context.map(|v| v.into()),
                field_name: None,
                data: None,
                mode: extra.mode,
            })
        }
    }
}

#[pymethods]
impl ValidationInfo {
    #[getter]
    fn get_data(&self, py: Python) -> PyResult<Py<PyDict>> {
        match self.data {
            Some(ref data) => Ok(data.clone_ref(py)),
            None => Err(PyAttributeError::new_err("No attribute named 'data'")),
        }
    }

    #[getter]
    fn get_field_name<'py>(&self, py: Python<'py>) -> PyResult<&'py PyString> {
        match self.field_name {
            Some(ref field_name) => Ok(PyString::new(py, field_name)),
            None => Err(PyAttributeError::new_err("No attribute named 'field_name'")),
        }
    }

    fn __repr__(&self, py: Python) -> PyResult<String> {
        let context = match self.context {
            Some(ref context) => context.as_ref(py).repr()?.extract()?,
            None => "None",
        };
        let config = self.config.as_ref(py).repr()?;
        let mut s = format!("ValidationInfo(config={config}, context={context}");
        if let Some(ref data) = self.data {
            s += &format!(", data={}", data.as_ref(py).repr()?);
        }
        if let Some(ref field_name) = self.field_name {
            s += &format!(", field_name='{field_name}'");
        }
        s += ")";
        Ok(s)
    }
}
