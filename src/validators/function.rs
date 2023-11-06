use std::sync::Arc;

use pyo3::exceptions::{PyAssertionError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict, PyString};
use pyo3::{intern, PyTraverseError, PyVisit};

use crate::errors::{
    AsLocItem, ErrorType, PydanticCustomError, PydanticKnownError, PydanticOmit, ValError, ValResult, ValidationError,
};
use crate::input::Input;
use crate::py_gc::PyGcTraverse;
use crate::tools::{function_name, safe_repr, SchemaDict};
use crate::PydanticUseDefault;

use super::generator::InternalValidator;
use super::{
    build_validator, BuildValidator, CombinedValidator, DefinitionsBuilder, Extra, InputType, ValidationState,
    Validator,
};

struct FunctionInfo {
    /// The actual function object that will get called
    pub function: Py<PyAny>,
    pub field_name: Option<Py<PyString>>,
    pub info_arg: bool,
}

fn destructure_function_schema(schema: &PyDict) -> PyResult<FunctionInfo> {
    let func_dict: &PyDict = schema.get_as_req(intern!(schema.py(), "function"))?;
    let function: &PyAny = func_dict.get_as_req(intern!(schema.py(), "function"))?;
    let func_type: &str = func_dict.get_as_req(intern!(schema.py(), "type"))?;
    let info_arg = match func_type {
        "with-info" => true,
        "no-info" => false,
        _ => unreachable!(),
    };
    let field_name = func_dict
        .get_as::<&PyString>(intern!(schema.py(), "field_name"))?
        .map(Into::into);
    Ok(FunctionInfo {
        function: function.into(),
        field_name,
        info_arg,
    })
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
                let func_info = destructure_function_schema(schema)?;
                let name = format!(
                    "{}[{}(), {}]",
                    $name,
                    function_name(func_info.function.as_ref(py))?,
                    validator.get_name()
                );
                Ok(Self {
                    validator: Box::new(validator),
                    func: func_info.function,
                    config: match config {
                        Some(c) => c.into(),
                        None => py.None(),
                    },
                    name,
                    field_name: func_info.field_name,
                    info_arg: func_info.info_arg,
                }
                .into())
            }
        }
    };
}

macro_rules! impl_validator {
    ($name:ident) => {
        impl_py_gc_traverse!($name {
            validator,
            func,
            config
        });

        impl Validator for $name {
            fn validate<'data>(
                &self,
                py: Python<'data>,
                input: &'data impl Input<'data>,
                state: &mut ValidationState<'_>,
            ) -> ValResult<'data, PyObject> {
                let validate = |v, s: &mut ValidationState<'_>| self.validator.validate(py, v, s);
                self._validate(validate, py, input, state)
            }
            fn validate_assignment<'data>(
                &self,
                py: Python<'data>,
                obj: &'data PyAny,
                field_name: &'data str,
                field_value: &'data PyAny,
                state: &mut ValidationState,
            ) -> ValResult<'data, PyObject> {
                let validate = move |v, s: &mut ValidationState<'_>| {
                    self.validator
                        .validate_assignment(py, v, field_name, field_value, s)
                };
                self._validate(validate, py, obj, state)
            }

            fn different_strict_behavior(&self, ultra_strict: bool) -> bool {
                if ultra_strict {
                    self.validator.different_strict_behavior(ultra_strict)
                } else {
                    true
                }
            }

            fn get_name(&self) -> &str {
                &self.name
            }

            fn complete(&self) -> PyResult<()> {
                self.validator.complete()
            }
        }
    };
}

#[derive(Debug)]
pub struct FunctionBeforeValidator {
    validator: Box<CombinedValidator>,
    func: PyObject,
    config: PyObject,
    name: String,
    field_name: Option<Py<PyString>>,
    info_arg: bool,
}

impl_build!(FunctionBeforeValidator, "function-before");

impl FunctionBeforeValidator {
    fn _validate<'s, 'data>(
        &'s self,
        call: impl FnOnce(&'data PyAny, &mut ValidationState<'_>) -> ValResult<'data, PyObject>,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &'s mut ValidationState<'_>,
    ) -> ValResult<'data, PyObject> {
        let r = if self.info_arg {
            let info = ValidationInfo::new(py, state.extra(), &self.config, self.field_name.clone());
            self.func.call1(py, (input.to_object(py), info))
        } else {
            self.func.call1(py, (input.to_object(py),))
        };
        let value = r.map_err(|e| convert_err(py, e, input))?;
        call(value.into_ref(py), state)
    }
}

impl_validator!(FunctionBeforeValidator);

#[derive(Debug)]
pub struct FunctionAfterValidator {
    validator: Box<CombinedValidator>,
    func: PyObject,
    config: PyObject,
    name: String,
    field_name: Option<Py<PyString>>,
    info_arg: bool,
}

impl_build!(FunctionAfterValidator, "function-after");

impl FunctionAfterValidator {
    fn _validate<'s, 'data, I: Input<'data>>(
        &'s self,
        call: impl FnOnce(&'data I, &mut ValidationState<'_>) -> ValResult<'data, PyObject>,
        py: Python<'data>,
        input: &'data I,
        state: &mut ValidationState<'_>,
    ) -> ValResult<'data, PyObject> {
        let v = call(input, state)?;
        let r = if self.info_arg {
            let info = ValidationInfo::new(py, state.extra(), &self.config, self.field_name.clone());
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
    field_name: Option<Py<PyString>>,
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
        let function_info = destructure_function_schema(schema)?;
        Ok(Self {
            func: function_info.function.clone(),
            config: match config {
                Some(c) => c.into(),
                None => py.None(),
            },
            name: format!(
                "function-plain[{}()]",
                function_name(function_info.function.as_ref(py))?
            ),
            field_name: function_info.field_name.clone(),
            info_arg: function_info.info_arg,
        }
        .into())
    }
}

impl_py_gc_traverse!(FunctionPlainValidator { func, config });

impl Validator for FunctionPlainValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        let r = if self.info_arg {
            let info = ValidationInfo::new(py, state.extra(), &self.config, self.field_name.clone());
            self.func.call1(py, (input.to_object(py), info))
        } else {
            self.func.call1(py, (input.to_object(py),))
        };
        r.map_err(|e| convert_err(py, e, input))
    }

    fn different_strict_behavior(&self, ultra_strict: bool) -> bool {
        // best guess, should we change this?
        !ultra_strict
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&self) -> PyResult<()> {
        Ok(())
    }
}

#[derive(Debug)]
pub struct FunctionWrapValidator {
    validator: Arc<CombinedValidator>,
    func: PyObject,
    config: PyObject,
    name: String,
    field_name: Option<Py<PyString>>,
    info_arg: bool,
    hide_input_in_errors: bool,
    validation_error_cause: bool,
}

impl BuildValidator for FunctionWrapValidator {
    const EXPECTED_TYPE: &'static str = "function-wrap";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let validator = build_validator(schema.get_as_req(intern!(py, "schema"))?, config, definitions)?;
        let function_info = destructure_function_schema(schema)?;
        let hide_input_in_errors: bool = config.get_as(intern!(py, "hide_input_in_errors"))?.unwrap_or(false);
        let validation_error_cause: bool = config.get_as(intern!(py, "validation_error_cause"))?.unwrap_or(false);
        Ok(Self {
            validator: Arc::new(validator),
            func: function_info.function.clone(),
            config: match config {
                Some(c) => c.into(),
                None => py.None(),
            },
            name: format!("function-wrap[{}()]", function_name(function_info.function.as_ref(py))?),
            field_name: function_info.field_name.clone(),
            info_arg: function_info.info_arg,
            hide_input_in_errors,
            validation_error_cause,
        }
        .into())
    }
}

impl FunctionWrapValidator {
    fn _validate<'s, 'data>(
        &'s self,
        handler: &'s PyAny,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        let r = if self.info_arg {
            let info = ValidationInfo::new(py, state.extra(), &self.config, self.field_name.clone());
            self.func.call1(py, (input.to_object(py), handler, info))
        } else {
            self.func.call1(py, (input.to_object(py), handler))
        };
        r.map_err(|e| convert_err(py, e, input))
    }
}

impl_py_gc_traverse!(FunctionWrapValidator {
    validator,
    func,
    config
});

impl Validator for FunctionWrapValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        let handler = ValidatorCallable {
            validator: InternalValidator::new(
                py,
                "ValidatorCallable",
                self.validator.clone(),
                state,
                self.hide_input_in_errors,
                self.validation_error_cause,
            ),
        };
        self._validate(
            Py::new(py, handler)?.into_ref(py),
            py,
            input.to_object(py).into_ref(py),
            state,
        )
    }

    fn validate_assignment<'data>(
        &self,
        py: Python<'data>,
        obj: &'data PyAny,
        field_name: &'data str,
        field_value: &'data PyAny,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        let handler = AssignmentValidatorCallable {
            validator: InternalValidator::new(
                py,
                "AssignmentValidatorCallable",
                self.validator.clone(),
                state,
                self.hide_input_in_errors,
                self.validation_error_cause,
            ),
            updated_field_name: field_name.to_string(),
            updated_field_value: field_value.to_object(py),
        };
        self._validate(Py::new(py, handler)?.into_ref(py), py, obj, state)
    }

    fn different_strict_behavior(&self, ultra_strict: bool) -> bool {
        if ultra_strict {
            self.validator.different_strict_behavior(ultra_strict)
        } else {
            true
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&self) -> PyResult<()> {
        self.validator.complete()
    }
}

#[pyclass(module = "pydantic_core._pydantic_core")]
#[derive(Debug)]
struct ValidatorCallable {
    validator: InternalValidator,
}

#[pymethods]
impl ValidatorCallable {
    fn __call__(&mut self, py: Python, input_value: &PyAny, outer_location: Option<&PyAny>) -> PyResult<PyObject> {
        let outer_location = outer_location.map(AsLocItem::as_loc_item);
        self.validator.validate(py, input_value, outer_location)
    }

    fn __repr__(&self) -> String {
        format!("ValidatorCallable({:?})", self.validator)
    }

    fn __str__(&self) -> String {
        self.__repr__()
    }

    fn __traverse__(&self, visit: PyVisit) -> Result<(), PyTraverseError> {
        self.validator.py_gc_traverse(&visit)
    }
}

#[pyclass(module = "pydantic_core._pydantic_core")]
#[derive(Debug)]
struct AssignmentValidatorCallable {
    updated_field_name: String,
    updated_field_value: Py<PyAny>,
    validator: InternalValidator,
}

#[pymethods]
impl AssignmentValidatorCallable {
    fn __call__(&mut self, py: Python, input_value: &PyAny, outer_location: Option<&PyAny>) -> PyResult<PyObject> {
        let outer_location = outer_location.map(AsLocItem::as_loc_item);
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
    ($py:expr, $py_err:expr, $error_value:expr, $type_member:ident, $input:ident) => {
        match $error_value.str() {
            Ok(py_string) => match py_string.to_str() {
                Ok(_) => ValError::new(
                    ErrorType::$type_member {
                        error: Some($py_err.into_py($py)),
                        context: None,
                    },
                    $input,
                ),
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
        let error_value = err.value(py);
        if let Ok(pydantic_value_error) = error_value.extract::<PydanticCustomError>() {
            pydantic_value_error.into_val_error(input)
        } else if let Ok(pydantic_error_type) = error_value.extract::<PydanticKnownError>() {
            pydantic_error_type.into_val_error(input)
        } else if let Ok(validation_error) = err.value(py).extract::<ValidationError>() {
            validation_error.into_val_error(py)
        } else {
            py_err_string!(py, err, error_value, ValueError, input)
        }
    } else if err.is_instance_of::<PyAssertionError>(py) {
        py_err_string!(py, err, err.value(py), AssertionError, input)
    } else if err.is_instance_of::<PydanticOmit>(py) {
        ValError::Omit
    } else if err.is_instance_of::<PydanticUseDefault>(py) {
        ValError::UseDefault
    } else {
        ValError::InternalErr(err)
    }
}

#[pyclass(module = "pydantic_core._pydantic_core", get_all)]
pub struct ValidationInfo {
    config: PyObject,
    context: Option<PyObject>,
    data: Option<Py<PyDict>>,
    field_name: Option<Py<PyString>>,
    mode: InputType,
}

impl ValidationInfo {
    fn new(py: Python, extra: &Extra, config: &PyObject, field_name: Option<Py<PyString>>) -> Self {
        Self {
            config: config.clone_ref(py),
            context: extra.context.map(Into::into),
            field_name,
            data: extra.data.map(Into::into),
            mode: extra.input_type,
        }
    }
}

#[pymethods]
impl ValidationInfo {
    fn __repr__(&self, py: Python) -> PyResult<String> {
        let context = match self.context {
            Some(ref context) => safe_repr(context.as_ref(py)),
            None => "None".into(),
        };
        let config = self.config.as_ref(py).repr()?;
        let data = match self.data {
            Some(ref data) => safe_repr(data.as_ref(py)),
            None => "None".into(),
        };
        let field_name = match self.field_name {
            Some(ref field_name) => safe_repr(field_name.as_ref(py)),
            None => "None".into(),
        };
        Ok(format!(
            "ValidationInfo(config={config}, context={context}, data={data}, field_name={field_name})"
        ))
    }
}
