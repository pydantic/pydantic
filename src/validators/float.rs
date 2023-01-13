use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::{is_strict, schema_or_config_same, SchemaDict};
use crate::errors::{ErrorType, ValError, ValResult};
use crate::input::Input;
use crate::recursion_guard::RecursionGuard;

use super::{BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct FloatValidator {
    strict: bool,
    allow_inf_nan: bool,
}

impl BuildValidator for FloatValidator {
    const EXPECTED_TYPE: &'static str = "float";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        _build_context: &mut BuildContext<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let use_constrained = schema.get_item(intern!(py, "multiple_of")).is_some()
            || schema.get_item(intern!(py, "le")).is_some()
            || schema.get_item(intern!(py, "lt")).is_some()
            || schema.get_item(intern!(py, "ge")).is_some()
            || schema.get_item(intern!(py, "gt")).is_some();
        if use_constrained {
            ConstrainedFloatValidator::build(schema, config)
        } else {
            Ok(Self {
                strict: is_strict(schema, config)?,
                allow_inf_nan: schema_or_config_same(schema, config, intern!(py, "allow_inf_nan"))?.unwrap_or(true),
            }
            .into())
        }
    }
}

impl Validator for FloatValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let float = input.validate_float(extra.strict.unwrap_or(self.strict))?;
        if !self.allow_inf_nan && !float.is_finite() {
            return Err(ValError::new(ErrorType::FiniteNumber, input));
        }
        Ok(float.into_py(py))
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}

#[derive(Debug, Clone)]
pub struct ConstrainedFloatValidator {
    strict: bool,
    allow_inf_nan: bool,
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
        extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let float = input.validate_float(extra.strict.unwrap_or(self.strict))?;
        if !self.allow_inf_nan && !float.is_finite() {
            return Err(ValError::new(ErrorType::FiniteNumber, input));
        }
        if let Some(multiple_of) = self.multiple_of {
            let rem = float % multiple_of;
            let threshold = float / 1e9;
            if rem.abs() > threshold && (rem - multiple_of).abs() > threshold {
                return Err(ValError::new(
                    ErrorType::MultipleOf {
                        multiple_of: multiple_of.into(),
                    },
                    input,
                ));
            }
        }
        if let Some(le) = self.le {
            if float > le {
                return Err(ValError::new(ErrorType::LessThanEqual { le: le.into() }, input));
            }
        }
        if let Some(lt) = self.lt {
            if float >= lt {
                return Err(ValError::new(ErrorType::LessThan { lt: lt.into() }, input));
            }
        }
        if let Some(ge) = self.ge {
            if float < ge {
                return Err(ValError::new(ErrorType::GreaterThanEqual { ge: ge.into() }, input));
            }
        }
        if let Some(gt) = self.gt {
            if float <= gt {
                return Err(ValError::new(ErrorType::GreaterThan { gt: gt.into() }, input));
            }
        }
        Ok(float.into_py(py))
    }
    fn get_name(&self) -> &str {
        "constrained-float"
    }
}

impl ConstrainedFloatValidator {
    pub fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<CombinedValidator> {
        let py = schema.py();
        Ok(Self {
            strict: is_strict(schema, config)?,
            allow_inf_nan: schema_or_config_same(schema, config, intern!(py, "allow_inf_nan"))?.unwrap_or(true),
            multiple_of: schema.get_as(intern!(py, "multiple_of"))?,
            le: schema.get_as(intern!(py, "le"))?,
            lt: schema.get_as(intern!(py, "lt"))?,
            ge: schema.get_as(intern!(py, "ge"))?,
            gt: schema.get_as(intern!(py, "gt"))?,
        }
        .into())
    }
}
