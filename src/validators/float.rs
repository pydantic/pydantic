use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::{is_strict, SchemaDict};
use crate::errors::{ErrorKind, ValError, ValResult};
use crate::input::Input;
use crate::recursion_guard::RecursionGuard;

use super::{BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct FloatValidator;

impl BuildValidator for FloatValidator {
    const EXPECTED_TYPE: &'static str = "float";

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
            ConstrainedFloatValidator::build(schema, config)
        } else if is_strict(schema, config)? {
            StrictFloatValidator::build()
        } else {
            Ok(Self.into())
        }
    }
}

impl Validator for FloatValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        Ok(input.lax_float()?.into_py(py))
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        Ok(input.strict_float()?.into_py(py))
    }

    fn get_name(&self, _py: Python) -> String {
        Self::EXPECTED_TYPE.to_string()
    }
}

#[derive(Debug, Clone)]
pub struct StrictFloatValidator;

impl StrictFloatValidator {
    pub fn build() -> PyResult<CombinedValidator> {
        Ok(Self.into())
    }
}

impl Validator for StrictFloatValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        Ok(input.strict_float()?.into_py(py))
    }

    fn get_name(&self, _py: Python) -> String {
        "strict-float".to_string()
    }
}

#[derive(Debug, Clone)]
pub struct ConstrainedFloatValidator {
    strict: bool,
    multiple_of: Option<f64>,
    le: Option<f64>,
    lt: Option<f64>,
    ge: Option<f64>,
    gt: Option<f64>,
}

impl Validator for ConstrainedFloatValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let float = match self.strict {
            true => input.strict_float()?,
            false => input.lax_float()?,
        };
        self._validation_logic(py, input, float)
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        self._validation_logic(py, input, input.strict_float()?)
    }

    fn get_name(&self, _py: Python) -> String {
        "constrained-float".to_string()
    }
}

impl ConstrainedFloatValidator {
    pub fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<CombinedValidator> {
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

    fn _validation_logic<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        float: f64,
    ) -> ValResult<'data, PyObject> {
        if let Some(multiple_of) = self.multiple_of {
            if float % multiple_of != 0.0 {
                return Err(ValError::new(ErrorKind::FloatMultipleOf { multiple_of }, input));
            }
        }
        if let Some(le) = self.le {
            if float > le {
                return Err(ValError::new(ErrorKind::FloatLessThanEqual { le }, input));
            }
        }
        if let Some(lt) = self.lt {
            if float >= lt {
                return Err(ValError::new(ErrorKind::FloatLessThan { lt }, input));
            }
        }
        if let Some(ge) = self.ge {
            if float < ge {
                return Err(ValError::new(ErrorKind::FloatGreaterThanEqual { ge }, input));
            }
        }
        if let Some(gt) = self.gt {
            if float <= gt {
                return Err(ValError::new(ErrorKind::FloatGreaterThan { gt }, input));
            }
        }
        Ok(float.into_py(py))
    }
}
