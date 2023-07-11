use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString, PyTime};

use speedate::Time;

use crate::build_tools::is_strict;
use crate::errors::{ErrorType, ValError, ValResult};
use crate::input::{EitherTime, Input};
use crate::recursion_guard::RecursionGuard;
use crate::tools::SchemaDict;

use super::datetime::extract_microseconds_precision;
use super::datetime::TZConstraint;
use super::{BuildValidator, CombinedValidator, Definitions, DefinitionsBuilder, Extra, Validator};

#[derive(Debug, Clone)]
pub struct TimeValidator {
    strict: bool,
    constraints: Option<TimeConstraints>,
    microseconds_precision: speedate::MicrosecondsPrecisionOverflowBehavior,
}

impl BuildValidator for TimeValidator {
    const EXPECTED_TYPE: &'static str = "time";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        _definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let s = Self {
            strict: is_strict(schema, config)?,
            constraints: TimeConstraints::from_py(schema)?,
            microseconds_precision: extract_microseconds_precision(schema, config)?,
        };
        Ok(s.into())
    }
}

impl Validator for TimeValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        _definitions: &'data Definitions<CombinedValidator>,
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let time = input.validate_time(extra.strict.unwrap_or(self.strict), self.microseconds_precision)?;
        if let Some(constraints) = &self.constraints {
            let raw_time = time.as_raw()?;

            macro_rules! check_constraint {
                ($constraint:ident, $error:ident) => {
                    if let Some(constraint) = &constraints.$constraint {
                        if !raw_time.$constraint(constraint) {
                            return Err(ValError::new(
                                ErrorType::$error {
                                    $constraint: constraint.to_string().into(),
                                },
                                input,
                            ));
                        }
                    }
                };
            }

            check_constraint!(le, LessThanEqual);
            check_constraint!(lt, LessThan);
            check_constraint!(ge, GreaterThanEqual);
            check_constraint!(gt, GreaterThan);

            if let Some(ref tz_constraint) = constraints.tz {
                tz_constraint.tz_check(raw_time.tz_offset, input)?;
            }
        }
        Ok(time.try_into_py(py)?)
    }

    fn different_strict_behavior(
        &self,
        _definitions: Option<&DefinitionsBuilder<CombinedValidator>>,
        ultra_strict: bool,
    ) -> bool {
        !ultra_strict
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }

    fn complete(&mut self, _definitions: &DefinitionsBuilder<CombinedValidator>) -> PyResult<()> {
        Ok(())
    }
}

fn convert_pytime(schema: &PyDict, field: &PyString) -> PyResult<Option<Time>> {
    match schema.get_as::<&PyTime>(field)? {
        Some(date) => Ok(Some(EitherTime::Py(date).as_raw()?)),
        None => Ok(None),
    }
}

#[derive(Debug, Clone)]
struct TimeConstraints {
    le: Option<Time>,
    lt: Option<Time>,
    ge: Option<Time>,
    gt: Option<Time>,
    tz: Option<TZConstraint>,
}

impl TimeConstraints {
    fn from_py(schema: &PyDict) -> PyResult<Option<Self>> {
        let py = schema.py();
        let c = Self {
            le: convert_pytime(schema, intern!(py, "le"))?,
            lt: convert_pytime(schema, intern!(py, "lt"))?,
            ge: convert_pytime(schema, intern!(py, "ge"))?,
            gt: convert_pytime(schema, intern!(py, "gt"))?,
            tz: TZConstraint::from_py(schema)?,
        };
        if c.le.is_some() || c.lt.is_some() || c.ge.is_some() || c.gt.is_some() || c.tz.is_some() {
            Ok(Some(c))
        } else {
            Ok(None)
        }
    }
}
