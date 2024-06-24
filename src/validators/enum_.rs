// Validator for Enums, so named because "enum" is a reserved keyword in Rust.
use std::marker::PhantomData;

use pyo3::exceptions::PyTypeError;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyFloat, PyInt, PyList, PyString, PyType};

use crate::build_tools::{is_strict, py_schema_err};
use crate::errors::{ErrorType, ValError, ValResult};
use crate::input::Input;
use crate::tools::{safe_repr, SchemaDict};

use super::is_instance::class_repr;
use super::literal::{expected_repr_name, LiteralLookup};
use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, Exactness, ValidationState, Validator};

#[derive(Debug, Clone)]
pub struct BuildEnumValidator;

impl BuildValidator for BuildEnumValidator {
    const EXPECTED_TYPE: &'static str = "enum";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let members: Bound<PyList> = schema.get_as_req(intern!(schema.py(), "members"))?;
        if members.is_empty() {
            return py_schema_err!("`members` should have length > 0");
        }

        let py = schema.py();
        let value_str = intern!(py, "value");
        let expected: Vec<(Bound<'_, PyAny>, PyObject)> = members
            .iter()
            .map(|v| Ok((v.getattr(value_str)?, v.into())))
            .collect::<PyResult<_>>()?;

        let repr_args: Vec<String> = expected
            .iter()
            .map(|(k, _)| k.repr()?.extract())
            .collect::<PyResult<_>>()?;

        let class: Bound<PyType> = schema.get_as_req(intern!(py, "cls"))?;
        let class_repr = class_repr(schema, &class)?;

        let lookup = LiteralLookup::new(py, expected.into_iter())?;

        macro_rules! build {
            ($vv:ty, $name_prefix:literal) => {
                EnumValidator {
                    phantom: PhantomData::<$vv>,
                    class: class.clone().into(),
                    lookup,
                    missing: schema.get_as(intern!(py, "missing"))?,
                    expected_repr: expected_repr_name(repr_args, "").0,
                    strict: is_strict(schema, config)?,
                    class_repr: class_repr.clone(),
                    name: format!("{}[{class_repr}]", $name_prefix),
                }
            };
        }

        let sub_type: Option<String> = schema.get_as(intern!(py, "sub_type"))?;
        match sub_type.as_deref() {
            Some("int") => Ok(CombinedValidator::IntEnum(build!(IntEnumValidator, "int-enum"))),
            Some("str") => Ok(CombinedValidator::StrEnum(build!(StrEnumValidator, "str-enum"))),
            Some("float") => Ok(CombinedValidator::FloatEnum(build!(FloatEnumValidator, "float-enum"))),
            Some(_) => py_schema_err!("`sub_type` must be one of: 'int', 'str', 'float' or None"),
            None => Ok(CombinedValidator::PlainEnum(build!(PlainEnumValidator, "enum"))),
        }
    }
}

pub trait EnumValidateValue: std::fmt::Debug + Clone + Send + Sync {
    fn validate_value<'py, I: Input<'py> + ?Sized>(
        py: Python<'py>,
        input: &I,
        lookup: &LiteralLookup<PyObject>,
        strict: bool,
    ) -> ValResult<Option<PyObject>>;
}

#[derive(Debug, Clone)]
pub struct EnumValidator<T: EnumValidateValue> {
    phantom: PhantomData<T>,
    class: Py<PyType>,
    lookup: LiteralLookup<PyObject>,
    missing: Option<PyObject>,
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
    ) -> ValResult<PyObject> {
        let class = self.class.bind(py);
        if input.as_python().is_some_and(|any| any.is_exact_instance(class)) {
            return Ok(input.to_object(py));
        }
        let strict = state.strict_or(self.strict);
        if strict && input.as_python().is_some() {
            // TODO what about instances of subclasses?
            return Err(ValError::new(
                ErrorType::IsInstanceOf {
                    class: self.class_repr.clone(),
                    context: None,
                },
                input,
            ));
        } else if let Some(v) = T::validate_value(py, input, &self.lookup, strict)? {
            state.floor_exactness(Exactness::Lax);
            return Ok(v);
        } else if let Some(ref missing) = self.missing {
            state.floor_exactness(Exactness::Lax);
            let enum_value = missing.bind(py).call1((input.to_object(py),)).map_err(|_| {
                ValError::new(
                    ErrorType::Enum {
                        expected: self.expected_repr.clone(),
                        context: None,
                    },
                    input,
                )
            })?;
            // check enum_value is an instance of the class like
            // https://github.com/python/cpython/blob/v3.12.2/Lib/enum.py#L1148
            if enum_value.is_instance(class)? {
                return Ok(enum_value.into());
            } else if !enum_value.is(&py.None()) {
                let type_error = PyTypeError::new_err(format!(
                    "error in {}._missing_: returned {} instead of None or a valid member",
                    class
                        .name()
                        .and_then(|name| name.extract::<String>())
                        .unwrap_or_else(|_| "<Unknown>".into()),
                    safe_repr(&enum_value)
                ));
                return Err(type_error.into());
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

    fn get_name(&self) -> &str {
        &self.name
    }
}

#[derive(Debug, Clone)]
pub struct PlainEnumValidator;

impl_py_gc_traverse!(EnumValidator<PlainEnumValidator> { class, missing });

impl EnumValidateValue for PlainEnumValidator {
    fn validate_value<'py, I: Input<'py> + ?Sized>(
        py: Python<'py>,
        input: &I,
        lookup: &LiteralLookup<PyObject>,
        strict: bool,
    ) -> ValResult<Option<PyObject>> {
        match lookup.validate(py, input)? {
            Some((_, v)) => Ok(Some(v.clone_ref(py))),
            None => {
                if !strict {
                    if let Some(py_input) = input.as_python() {
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
                }
                Ok(None)
            }
        }
    }
}

#[derive(Debug, Clone)]
pub struct IntEnumValidator;

impl_py_gc_traverse!(EnumValidator<IntEnumValidator> { class, missing });

impl EnumValidateValue for IntEnumValidator {
    fn validate_value<'py, I: Input<'py> + ?Sized>(
        py: Python<'py>,
        input: &I,
        lookup: &LiteralLookup<PyObject>,
        strict: bool,
    ) -> ValResult<Option<PyObject>> {
        Ok(lookup.validate_int(py, input, strict)?.map(|v| v.clone_ref(py)))
    }
}

#[derive(Debug, Clone)]
pub struct StrEnumValidator;

impl_py_gc_traverse!(EnumValidator<StrEnumValidator> { class, missing });

impl EnumValidateValue for StrEnumValidator {
    fn validate_value<'py, I: Input<'py> + ?Sized>(
        py: Python,
        input: &I,
        lookup: &LiteralLookup<PyObject>,
        strict: bool,
    ) -> ValResult<Option<PyObject>> {
        Ok(lookup.validate_str(input, strict)?.map(|v| v.clone_ref(py)))
    }
}

#[derive(Debug, Clone)]
pub struct FloatEnumValidator;

impl_py_gc_traverse!(EnumValidator<FloatEnumValidator> { class, missing });

impl EnumValidateValue for FloatEnumValidator {
    fn validate_value<'py, I: Input<'py> + ?Sized>(
        py: Python<'py>,
        input: &I,
        lookup: &LiteralLookup<PyObject>,
        strict: bool,
    ) -> ValResult<Option<PyObject>> {
        Ok(lookup.validate_float(py, input, strict)?.map(|v| v.clone_ref(py)))
    }
}
