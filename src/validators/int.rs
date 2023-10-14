use num_bigint::BigInt;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::is_strict;
use crate::errors::{ErrorType, ValError, ValResult};
use crate::input::{Input, Int};
use crate::tools::SchemaDict;

use super::ValidationState;
use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, Validator};

#[derive(Debug, Clone)]
pub struct IntValidator {
    strict: bool,
}

impl BuildValidator for IntValidator {
    const EXPECTED_TYPE: &'static str = "int";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
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
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        let either_int = input.validate_int(state.strict_or(self.strict))?;
        Ok(either_int.into_py(py))
    }

    fn different_strict_behavior(&self, ultra_strict: bool) -> bool {
        !ultra_strict
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }

    fn complete(&self) -> PyResult<()> {
        Ok(())
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

impl_py_gc_traverse!(ConstrainedIntValidator {});

impl Validator for ConstrainedIntValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        let either_int = input.validate_int(state.strict_or(self.strict))?;
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
        Ok(either_int.into_py(py))
    }

    fn different_strict_behavior(&self, ultra_strict: bool) -> bool {
        !ultra_strict
    }

    fn get_name(&self) -> &str {
        "constrained-int"
    }

    fn complete(&self) -> PyResult<()> {
        Ok(())
    }
}

impl ConstrainedIntValidator {
    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<CombinedValidator> {
        let py = schema.py();
        Ok(Self {
            strict: is_strict(schema, config)?,
            multiple_of: schema.get_as(intern!(py, "multiple_of"))?,
            le: schema.get_as(intern!(py, "le"))?,
            lt: schema.get_as(intern!(py, "lt"))?,
            ge: schema.get_as(intern!(py, "ge"))?,
            gt: schema.get_as(intern!(py, "gt"))?,
        }
        .into())
    }
}
