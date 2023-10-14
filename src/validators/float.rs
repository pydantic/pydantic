use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::{is_strict, schema_or_config_same};
use crate::errors::{ErrorType, ErrorTypeDefaults, ValError, ValResult};
use crate::input::Input;
use crate::tools::SchemaDict;

use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

pub struct FloatBuilder;

impl BuildValidator for FloatBuilder {
    const EXPECTED_TYPE: &'static str = "float";
    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let use_constrained = schema.get_item(intern!(py, "multiple_of"))?.is_some()
            || schema.get_item(intern!(py, "le"))?.is_some()
            || schema.get_item(intern!(py, "lt"))?.is_some()
            || schema.get_item(intern!(py, "ge"))?.is_some()
            || schema.get_item(intern!(py, "gt"))?.is_some();
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

impl_py_gc_traverse!(FloatValidator {});

impl Validator for FloatValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        let strict = state.strict_or(self.strict);
        let either_float = input.validate_float(strict, state.extra().ultra_strict)?;
        if !self.allow_inf_nan && !either_float.as_f64().is_finite() {
            return Err(ValError::new(ErrorTypeDefaults::FiniteNumber, input));
        }
        Ok(either_float.into_py(py))
    }

    fn different_strict_behavior(&self, _ultra_strict: bool) -> bool {
        true
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }

    fn complete(&self) -> PyResult<()> {
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

impl_py_gc_traverse!(ConstrainedFloatValidator {});

impl Validator for ConstrainedFloatValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        let strict = state.strict_or(self.strict);
        let either_float = input.validate_float(strict, state.extra().ultra_strict)?;
        let float: f64 = either_float.as_f64();
        if !self.allow_inf_nan && !float.is_finite() {
            return Err(ValError::new(ErrorTypeDefaults::FiniteNumber, input));
        }
        if let Some(multiple_of) = self.multiple_of {
            let rem = float % multiple_of;
            let threshold = float / 1e9;
            if rem.abs() > threshold && (rem - multiple_of).abs() > threshold {
                return Err(ValError::new(
                    ErrorType::MultipleOf {
                        multiple_of: multiple_of.into(),
                        context: None,
                    },
                    input,
                ));
            }
        }
        if let Some(le) = self.le {
            if float > le {
                return Err(ValError::new(
                    ErrorType::LessThanEqual {
                        le: le.into(),
                        context: None,
                    },
                    input,
                ));
            }
        }
        if let Some(lt) = self.lt {
            if float >= lt {
                return Err(ValError::new(
                    ErrorType::LessThan {
                        lt: lt.into(),
                        context: None,
                    },
                    input,
                ));
            }
        }
        if let Some(ge) = self.ge {
            if float < ge {
                return Err(ValError::new(
                    ErrorType::GreaterThanEqual {
                        ge: ge.into(),
                        context: None,
                    },
                    input,
                ));
            }
        }
        if let Some(gt) = self.gt {
            if float <= gt {
                return Err(ValError::new(
                    ErrorType::GreaterThan {
                        gt: gt.into(),
                        context: None,
                    },
                    input,
                ));
            }
        }
        Ok(either_float.into_py(py))
    }

    fn different_strict_behavior(&self, _ultra_strict: bool) -> bool {
        true
    }

    fn get_name(&self) -> &str {
        "constrained-float"
    }

    fn complete(&self) -> PyResult<()> {
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
