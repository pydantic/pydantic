use std::sync::Arc;

use pyo3::exceptions::{PyTypeError, PyValueError};
use pyo3::intern;
use pyo3::sync::PyOnceLock;
use pyo3::types::{IntoPyDict, PyDict, PyString, PyType};
use pyo3::{prelude::*, PyTypeInfo};

use crate::build_tools::is_strict;
use crate::errors::ErrorTypeDefaults;
use crate::errors::ValResult;
use crate::errors::{ErrorType, Number, ToErrorValue, ValError};
use crate::input::Input;

use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

static FRACTION_TYPE: PyOnceLock<Py<PyType>> = PyOnceLock::new();

pub fn get_fraction_type(py: Python<'_>) -> &Bound<'_, PyType> {
    FRACTION_TYPE
        .get_or_init(py, || {
            py.import("fractions")
                .and_then(|fraction_module| fraction_module.getattr("Fraction"))
                .unwrap()
                .extract()
                .unwrap()
        })
        .bind(py)
}

fn validate_as_fraction(
    py: Python,
    schema: &Bound<'_, PyDict>,
    key: &Bound<'_, PyString>,
) -> PyResult<Option<Py<PyAny>>> {
    match schema.get_item(key)? {
        Some(value) => match value.validate_fraction(false, py) {
            Ok(v) => Ok(Some(v.into_inner().unbind())),
            Err(_) => Err(PyValueError::new_err(format!(
                "'{key}' must be coercible to a Fraction instance",
            ))),
        },
        None => Ok(None),
    }
}

#[derive(Debug, Clone)]
pub struct FractionValidator {
    strict: bool,
    le: Option<Py<PyAny>>,
    lt: Option<Py<PyAny>>,
    ge: Option<Py<PyAny>>,
    gt: Option<Py<PyAny>>,
}

impl BuildValidator for FractionValidator {
    const EXPECTED_TYPE: &'static str = "fraction";
    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<Arc<CombinedValidator>>,
    ) -> PyResult<Arc<CombinedValidator>> {
        let py = schema.py();

        Ok(CombinedValidator::Fraction(Self {
            strict: is_strict(schema, config)?,
            le: validate_as_fraction(py, schema, intern!(py, "le"))?,
            lt: validate_as_fraction(py, schema, intern!(py, "lt"))?,
            ge: validate_as_fraction(py, schema, intern!(py, "ge"))?,
            gt: validate_as_fraction(py, schema, intern!(py, "gt"))?,
        })
        .into())
    }
}

impl_py_gc_traverse!(FractionValidator { le, lt, ge, gt });

impl Validator for FractionValidator {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Py<PyAny>> {
        let fraction = input.validate_fraction(state.strict_or(self.strict), py)?.unpack(state);

        if let Some(le) = &self.le {
            if !fraction.le(le)? {
                return Err(ValError::new(
                    ErrorType::LessThanEqual {
                        le: Number::String(le.to_string()),
                        context: Some([("le", le)].into_py_dict(py)?.into()),
                    },
                    input,
                ));
            }
        }
        if let Some(lt) = &self.lt {
            if !fraction.lt(lt)? {
                return Err(ValError::new(
                    ErrorType::LessThan {
                        lt: Number::String(lt.to_string()),
                        context: Some([("lt", lt)].into_py_dict(py)?.into()),
                    },
                    input,
                ));
            }
        }
        if let Some(ge) = &self.ge {
            if !fraction.ge(ge)? {
                return Err(ValError::new(
                    ErrorType::GreaterThanEqual {
                        ge: Number::String(ge.to_string()),
                        context: Some([("ge", ge)].into_py_dict(py)?.into()),
                    },
                    input,
                ));
            }
        }
        if let Some(gt) = &self.gt {
            if !fraction.gt(gt)? {
                return Err(ValError::new(
                    ErrorType::GreaterThan {
                        gt: Number::String(gt.to_string()),
                        context: Some([("gt", gt)].into_py_dict(py)?.into()),
                    },
                    input,
                ));
            }
        }

        Ok(fraction.into())
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}

pub(crate) fn create_fraction<'py>(arg: &Bound<'py, PyAny>, input: impl ToErrorValue) -> ValResult<Bound<'py, PyAny>> {
    let py = arg.py();
    get_fraction_type(py)
        .call1((arg,))
        .map_err(|e| handle_fraction_new_error(input, e))
}

fn handle_fraction_new_error(input: impl ToErrorValue, error: PyErr) -> ValError {
    Python::attach(|py| {
        if error.matches(py, PyValueError::type_object(py)).unwrap_or(false) {
            ValError::new(ErrorTypeDefaults::FractionParsing, input)
        } else if error.matches(py, PyTypeError::type_object(py)).unwrap_or(false) {
            ValError::new(ErrorTypeDefaults::FractionType, input)
        } else {
            // Let ZeroDivisionError and other exceptions bubble up as InternalErr
            // which will be shown to the user with the original Python error message
            ValError::InternalErr(error)
        }
    })
}
