use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::{is_strict, schema_or_config_same};
use crate::errors::{ErrorType, ValError, ValResult};
use crate::input::Input;
use crate::recursion_guard::RecursionGuard;
use crate::tools::SchemaDict;

use super::{BuildValidator, CombinedValidator, Definitions, DefinitionsBuilder, Extra, Validator};

pub struct FloatBuilder;

impl BuildValidator for FloatBuilder {
    const EXPECTED_TYPE: &'static str = "float";
    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let use_constrained = schema.get_item(intern!(py, "multiple_of")).is_some()
            || schema.get_item(intern!(py, "le")).is_some()
            || schema.get_item(intern!(py, "lt")).is_some()
            || schema.get_item(intern!(py, "ge")).is_some()
            || schema.get_item(intern!(py, "gt")).is_some();
        if use_constrained {
            ConstrainedFloatValidator::build(schema, config, definitions)
        } else {
            Ok(FloatValidator {
                strict: is_strict(schema, config)?,
                allow_inf_nan: schema_or_config_same(schema, config, intern!(py, "allow_inf_nan"))?.unwrap_or(true),
            }
            .into())
        }
    }
}

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
        _definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        Ok(Self {
            strict: is_strict(schema, config)?,
            allow_inf_nan: schema_or_config_same(schema, config, intern!(py, "allow_inf_nan"))?.unwrap_or(true),
        }
        .into())
    }
}

impl Validator for FloatValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        _definitions: &'data Definitions<CombinedValidator>,
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let either_float = input.validate_float(extra.strict.unwrap_or(self.strict), extra.ultra_strict)?;
        let float: f64 = either_float.try_into()?;
        if !self.allow_inf_nan && !float.is_finite() {
            return Err(ValError::new(ErrorType::FiniteNumber, input));
        }
        Ok(float.into_py(py))
    }

    fn different_strict_behavior(
        &self,
        _definitions: Option<&DefinitionsBuilder<CombinedValidator>>,
        _ultra_strict: bool,
    ) -> bool {
        true
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }

    fn complete(&mut self, _definitions: &DefinitionsBuilder<CombinedValidator>) -> PyResult<()> {
        Ok(())
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
        _definitions: &'data Definitions<CombinedValidator>,
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let either_float = input.validate_float(extra.strict.unwrap_or(self.strict), extra.ultra_strict)?;
        let float: f64 = either_float.try_into()?;
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

    fn different_strict_behavior(
        &self,
        _definitions: Option<&DefinitionsBuilder<CombinedValidator>>,
        _ultra_strict: bool,
    ) -> bool {
        true
    }

    fn get_name(&self) -> &str {
        "constrained-float"
    }

    fn complete(&mut self, _definitions: &DefinitionsBuilder<CombinedValidator>) -> PyResult<()> {
        Ok(())
    }
}

impl BuildValidator for ConstrainedFloatValidator {
    const EXPECTED_TYPE: &'static str = "float";
    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        _definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
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
