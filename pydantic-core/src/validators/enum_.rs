// Validator for Enums, so named because "enum" is a reserved keyword in Rust.
use std::marker::PhantomData;
use std::sync::Arc;

use pyo3::exceptions::PyValueError;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyFloat, PyInt, PyList, PyString, PyType};

use crate::build_tools::{is_strict, py_schema_err};
use crate::errors::{ErrorType, ValError, ValResult};
use crate::input::{Input, InputType};
use crate::tools::SchemaDict;
use crate::validators::literal::expected_repr;

use super::is_instance::class_repr;
use super::literal::LiteralLookup;
use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, Exactness, ValidationState, Validator};

#[derive(Debug, Clone)]
pub struct BuildEnumValidator;

impl BuildValidator for BuildEnumValidator {
    const EXPECTED_TYPE: &'static str = "enum";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<Arc<CombinedValidator>>,
    ) -> PyResult<Arc<CombinedValidator>> {
        let members: Bound<PyList> = schema.get_as_req(intern!(schema.py(), "members"))?;
        if members.is_empty() {
            return py_schema_err!("`members` should have length > 0");
        }

        let py = schema.py();
        let value_str = intern!(py, "value");
        let expected: Vec<(Bound<'_, PyAny>, Py<PyAny>)> = members
            .iter()
            .map(|v| Ok((v.getattr(value_str)?, v.into())))
            .collect::<PyResult<_>>()?;

        let repr_args: Vec<_> = expected.iter().map(|(k, _)| k.repr()).collect::<PyResult<_>>()?;
        let expected_repr = expected_repr(&repr_args)?;

        let class: Bound<PyType> = schema.get_as_req(intern!(py, "cls"))?;
        let class_repr = class_repr(schema, &class)?;

        let lookup = Box::new(LiteralLookup::new(py, expected.into_iter())?);

        macro_rules! build {
            ($vv:ty, $name_prefix:literal) => {
                EnumValidator {
                    phantom: PhantomData::<$vv>,
                    class: class.clone().into(),
                    lookup,
                    expected_repr,
                    strict: is_strict(schema, config)?,
                    class_repr: class_repr.clone(),
                    name: format!("{}[{class_repr}]", $name_prefix),
                }
            };
        }

        let sub_type: Option<String> = schema.get_as(intern!(py, "sub_type"))?;
        match sub_type.as_deref() {
            Some("int") => Ok(CombinedValidator::IntEnum(build!(IntEnumValidator, "int-enum")).into()),
            Some("str") => Ok(CombinedValidator::StrEnum(build!(StrEnumValidator, "str-enum")).into()),
            Some("float") => Ok(CombinedValidator::FloatEnum(build!(FloatEnumValidator, "float-enum")).into()),
            Some(_) => py_schema_err!("`sub_type` must be one of: 'int', 'str', 'float' or None"),
            None => Ok(CombinedValidator::PlainEnum(build!(PlainEnumValidator, "enum")).into()),
        }
    }
}

pub trait EnumValidateValue: std::fmt::Debug + Clone + Send + Sync {
    fn validate_value<'py, I: Input<'py> + ?Sized>(
        py: Python<'py>,
        input: &I,
        lookup: &LiteralLookup<Py<PyAny>>,
        strict: bool,
    ) -> ValResult<Option<Py<PyAny>>>;
}

#[derive(Debug, Clone)]
pub struct EnumValidator<T: EnumValidateValue> {
    phantom: PhantomData<T>,
    class: Py<PyType>,
    lookup: Box<LiteralLookup<Py<PyAny>>>,
    expected_repr: String,
    strict: bool,
    class_repr: String,
    name: String,
}

impl<T: EnumValidateValue> Validator for EnumValidator<T> {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Py<PyAny>> {
        let class = self.class.bind(py);
        if let Some(exact_py_input) = input.as_python().filter(|any| any.is_exact_instance(class)) {
            return Ok(exact_py_input.clone().unbind());
        }
        let strict = state.strict_or(self.strict);
        if strict && state.extra().input_type == InputType::Python {
            // TODO what about instances of subclasses?
            return Err(ValError::new(
                ErrorType::IsInstanceOf {
                    class: self.class_repr.clone(),
                    context: None,
                },
                input,
            ));
        }

        state.floor_exactness(Exactness::Lax);

        if let Some(v) = T::validate_value(py, input, &self.lookup, strict)? {
            return Ok(v);
        }
        if state.is_json_key()
            && let Some(v) = self.lookup.validate_json_key(py, input)?
        {
            return Ok(v.clone_ref(py));
        }

        // Fall back to calling the enum class (it handles calling `_missing_()` and such).
        // A `ValueError` means the value is not a valid member. Any other exception is propagated
        // as is (e.g. a `TypeError` if `_missing_()` returns something else than an enum value,
        // meaning the `_missing_()` definition is invalid):
        match class.call1((input.to_object(py)?,)) {
            Ok(res) => Ok(res.unbind()),
            Err(err) if err.is_instance_of::<PyValueError>(py) || is_py310_flag_type_error(class, &err) => {
                // JSON object keys can only be strings, e.g. `{"5": ...}` for a combination of
                // `Flag` members which isn't a member itself (`ANIMALS | FRUIT`):
                if state.is_json_key()
                    && let Ok(int) = input.validate_int(false)
                {
                    match class.call1((int.into_inner(),)) {
                        Ok(res) => return Ok(res.unbind()),
                        Err(err) if err.is_instance_of::<PyValueError>(py) => {}
                        Err(err) => return Err(err.into()),
                    }
                }
                Err(ValError::new(
                    ErrorType::Enum {
                        expected: self.expected_repr.clone(),
                        context: None,
                    },
                    input,
                ))
            }
            Err(err) => Err(err.into()),
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}

/// On Python 3.10, `Flag._missing_()` raises a `TypeError` when called with a non-integer value.
///
/// The `ValueError` was introduced in https://github.com/python/cpython/pull/24215, but reverted
/// for Python 3.10 in https://github.com/python/cpython/pull/27010.
#[cfg(not(Py_3_11))]
fn is_py310_flag_type_error(class: &Bound<'_, PyType>, err: &PyErr) -> bool {
    fn missing_func<'py>(cls: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
        let py = cls.py();
        cls.getattr(intern!(py, "_missing_"))?.getattr(intern!(py, "__func__"))
    }

    let py = class.py();
    if !err.is_instance_of::<pyo3::exceptions::PyTypeError>(py) {
        return false;
    }
    // Only if the stdlib implementation is used, so that errors from user-defined `_missing_()` methods are kept:
    let Ok(flag) = py
        .import(intern!(py, "enum"))
        .and_then(|m| m.getattr(intern!(py, "Flag")))
    else {
        return false;
    };
    match (missing_func(class.as_any()), missing_func(&flag)) {
        (Ok(class_missing), Ok(flag_missing)) => class_missing.is(&flag_missing),
        _ => false,
    }
}

#[cfg(Py_3_11)]
fn is_py310_flag_type_error(_class: &Bound<'_, PyType>, _err: &PyErr) -> bool {
    false
}

#[derive(Debug, Clone)]
pub struct PlainEnumValidator;

impl_py_gc_traverse!(EnumValidator<PlainEnumValidator> { class, lookup });

impl EnumValidateValue for PlainEnumValidator {
    fn validate_value<'py, I: Input<'py> + ?Sized>(
        py: Python<'py>,
        input: &I,
        lookup: &LiteralLookup<Py<PyAny>>,
        strict: bool,
    ) -> ValResult<Option<Py<PyAny>>> {
        match lookup.validate(py, input)? {
            Some((_, v)) => Ok(Some(v.clone_ref(py))),
            None => {
                if !strict && let Some(py_input) = input.as_python() {
                    // necessary for compatibility with 2.6, where str and int subclasses are allowed
                    if py_input.is_instance_of::<PyString>() {
                        return Ok(lookup.validate_str(input, false)?.map(|v| v.clone_ref(py)));
                    } else if py_input.is_instance_of::<PyInt>() {
                        return Ok(lookup.validate_int(py, input, false)?.map(|v| v.clone_ref(py)));
                    // necessary for compatibility with 2.6, where float values are allowed for int enums in lax mode
                    } else if py_input.is_instance_of::<PyFloat>() {
                        return Ok(lookup.validate_int(py, input, false)?.map(|v| v.clone_ref(py)));
                    }
                }
                Ok(None)
            }
        }
    }
}

#[derive(Debug, Clone)]
pub struct IntEnumValidator;

impl_py_gc_traverse!(EnumValidator<IntEnumValidator> { class, lookup });

impl EnumValidateValue for IntEnumValidator {
    fn validate_value<'py, I: Input<'py> + ?Sized>(
        py: Python<'py>,
        input: &I,
        lookup: &LiteralLookup<Py<PyAny>>,
        strict: bool,
    ) -> ValResult<Option<Py<PyAny>>> {
        Ok(lookup.validate_int(py, input, strict)?.map(|v| v.clone_ref(py)))
    }
}

#[derive(Debug, Clone)]
pub struct StrEnumValidator;

impl_py_gc_traverse!(EnumValidator<StrEnumValidator> { class, lookup });

impl EnumValidateValue for StrEnumValidator {
    fn validate_value<'py, I: Input<'py> + ?Sized>(
        py: Python,
        input: &I,
        lookup: &LiteralLookup<Py<PyAny>>,
        strict: bool,
    ) -> ValResult<Option<Py<PyAny>>> {
        Ok(lookup.validate_str(input, strict)?.map(|v| v.clone_ref(py)))
    }
}

#[derive(Debug, Clone)]
pub struct FloatEnumValidator;

impl_py_gc_traverse!(EnumValidator<FloatEnumValidator> { class, lookup });

impl EnumValidateValue for FloatEnumValidator {
    fn validate_value<'py, I: Input<'py> + ?Sized>(
        py: Python<'py>,
        input: &I,
        lookup: &LiteralLookup<Py<PyAny>>,
        strict: bool,
    ) -> ValResult<Option<Py<PyAny>>> {
        Ok(lookup.validate_float(py, input, strict)?.map(|v| v.clone_ref(py)))
    }
}
