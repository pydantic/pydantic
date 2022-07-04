use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::{is_strict, SchemaDict};
use crate::errors::{ErrorKind, ValError, ValResult};
use crate::input::Input;
use crate::recursion_guard::RecursionGuard;

use super::{BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct IntValidator;

impl BuildValidator for IntValidator {
    const EXPECTED_TYPE: &'static str = "int";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        _build_context: &mut BuildContext,
    ) -> PyResult<CombinedValidator> {
        let use_constrained = schema.get_item("multiple_of").is_some()
            || schema.get_item("le").is_some()
            || schema.get_item("lt").is_some()
            || schema.get_item("ge").is_some()
            || schema.get_item("gt").is_some();
        if use_constrained {
            ConstrainedIntValidator::build(schema, config)
        } else if is_strict(schema, config)? {
            StrictIntValidator::build()
        } else {
            Ok(Self.into())
        }
    }
}

impl Validator for IntValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        Ok(input.lax_int()?.into_py(py))
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        Ok(input.strict_int()?.into_py(py))
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}

#[derive(Debug, Clone)]
pub struct StrictIntValidator;

impl StrictIntValidator {
    fn build() -> PyResult<CombinedValidator> {
        Ok(Self.into())
    }
}

impl Validator for StrictIntValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        Ok(input.strict_int()?.into_py(py))
    }

    fn get_name(&self) -> &str {
        "strict-int"
    }
}

#[derive(Debug, Clone)]
pub struct ConstrainedIntValidator {
    strict: bool,
    multiple_of: Option<i64>,
    le: Option<i64>,
    lt: Option<i64>,
    ge: Option<i64>,
    gt: Option<i64>,
}

impl Validator for ConstrainedIntValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let int = match self.strict {
            true => input.strict_int()?,
            false => input.lax_int()?,
        };
        self._validation_logic(py, input, int)
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        self._validation_logic(py, input, input.strict_int()?)
    }

    fn get_name(&self) -> &str {
        "constrained-int"
    }
}

impl ConstrainedIntValidator {
    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<CombinedValidator> {
        Ok(Self {
            strict: is_strict(schema, config)?,
            multiple_of: schema.get_as("multiple_of")?,
            le: schema.get_as("le")?,
            lt: schema.get_as("lt")?,
            ge: schema.get_as("ge")?,
            gt: schema.get_as("gt")?,
        }
        .into())
    }

    fn _validation_logic<'a>(&self, py: Python<'a>, input: &'a impl Input<'a>, int: i64) -> ValResult<'a, PyObject> {
        if let Some(multiple_of) = self.multiple_of {
            if int % multiple_of != 0 {
                return Err(ValError::new(ErrorKind::IntMultipleOf { multiple_of }, input));
            }
        }
        if let Some(le) = self.le {
            if int > le {
                return Err(ValError::new(ErrorKind::IntLessThanEqual { le }, input));
            }
        }
        if let Some(lt) = self.lt {
            if int >= lt {
                return Err(ValError::new(ErrorKind::IntLessThan { lt }, input));
            }
        }
        if let Some(ge) = self.ge {
            if int < ge {
                return Err(ValError::new(ErrorKind::IntGreaterThanEqual { ge }, input));
            }
        }
        if let Some(gt) = self.gt {
            if int <= gt {
                return Err(ValError::new(ErrorKind::IntGreaterThan { gt }, input));
            }
        }
        Ok(int.into_py(py))
    }
}
