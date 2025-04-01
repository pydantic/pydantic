use num_bigint::BigInt;
use pyo3::exceptions::PyValueError;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};
use pyo3::IntoPyObjectExt;

use crate::build_tools::is_strict;
use crate::errors::{ErrorType, ValError, ValResult};
use crate::input::{Input, Int};

use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

fn validate_as_int(schema: &Bound<'_, PyDict>, key: &Bound<'_, PyString>) -> PyResult<Option<Int>> {
    match schema.get_item(key)? {
        Some(value) => match value.validate_int(false) {
            Ok(v) => match v.into_inner().as_int() {
                Ok(v) => Ok(Some(v)),
                Err(_) => Err(PyValueError::new_err(format!(
                    "'{key}' must be coercible to an integer"
                ))),
            },
            Err(_) => Err(PyValueError::new_err(format!(
                "'{key}' must be coercible to an integer"
            ))),
        },
        None => Ok(None),
    }
}

#[derive(Debug, Clone)]
pub struct IntValidator {
    strict: bool,
}

impl BuildValidator for IntValidator {
    const EXPECTED_TYPE: &'static str = "int";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let use_constrained = schema.get_item(intern!(py, "multiple_of"))?.is_some()
            || schema.get_item(intern!(py, "le"))?.is_some()
            || schema.get_item(intern!(py, "lt"))?.is_some()
            || schema.get_item(intern!(py, "ge"))?.is_some()
            || schema.get_item(intern!(py, "gt"))?.is_some();
        if use_constrained {
            ConstrainedIntValidator::build(schema, config)
        } else {
            Ok(Self {
                strict: is_strict(schema, config)?,
            }
            .into())
        }
    }
}

impl_py_gc_traverse!(IntValidator {});

impl Validator for IntValidator {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<PyObject> {
        input
            .validate_int(state.strict_or(self.strict))
            .and_then(|val_match| Ok(val_match.unpack(state).into_py_any(py)?))
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}

#[derive(Debug, Clone)]
pub struct ConstrainedIntValidator {
    strict: bool,
    multiple_of: Option<Int>,
    le: Option<Int>,
    lt: Option<Int>,
    ge: Option<Int>,
    gt: Option<Int>,
}

impl ConstrainedIntValidator {
    fn build(schema: &Bound<'_, PyDict>, config: Option<&Bound<'_, PyDict>>) -> PyResult<CombinedValidator> {
        let py = schema.py();
        Ok(Self {
            strict: is_strict(schema, config)?,
            multiple_of: validate_as_int(schema, intern!(py, "multiple_of"))?,
            le: validate_as_int(schema, intern!(py, "le"))?,
            lt: validate_as_int(schema, intern!(py, "lt"))?,
            ge: validate_as_int(schema, intern!(py, "ge"))?,
            gt: validate_as_int(schema, intern!(py, "gt"))?,
        }
        .into())
    }
}

impl_py_gc_traverse!(ConstrainedIntValidator {});

impl Validator for ConstrainedIntValidator {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<PyObject> {
        let either_int = input.validate_int(state.strict_or(self.strict))?.unpack(state);
        let int_value = either_int.as_int()?;

        if let Some(ref multiple_of) = self.multiple_of {
            if &int_value % multiple_of != Int::Big(BigInt::from(0)) {
                return Err(ValError::new(
                    ErrorType::MultipleOf {
                        multiple_of: multiple_of.clone().into(),
                        context: None,
                    },
                    input,
                ));
            }
        }
        if let Some(ref le) = self.le {
            if &int_value > le {
                return Err(ValError::new(
                    ErrorType::LessThanEqual {
                        le: le.clone().into(),
                        context: None,
                    },
                    input,
                ));
            }
        }
        if let Some(ref lt) = self.lt {
            if &int_value >= lt {
                return Err(ValError::new(
                    ErrorType::LessThan {
                        lt: lt.clone().into(),
                        context: None,
                    },
                    input,
                ));
            }
        }
        if let Some(ref ge) = self.ge {
            if &int_value < ge {
                return Err(ValError::new(
                    ErrorType::GreaterThanEqual {
                        ge: ge.clone().into(),
                        context: None,
                    },
                    input,
                ));
            }
        }
        if let Some(ref gt) = self.gt {
            if &int_value <= gt {
                return Err(ValError::new(
                    ErrorType::GreaterThan {
                        gt: gt.clone().into(),
                        context: None,
                    },
                    input,
                ));
            }
        }
        Ok(either_int.into_py_any(py)?)
    }

    fn get_name(&self) -> &'static str {
        "constrained-int"
    }
}
