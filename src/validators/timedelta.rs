use pyo3::prelude::*;
use pyo3::types::PyDict;
use speedate::Duration;

use crate::build_tools::is_strict;
use crate::errors::{ErrorType, ValError, ValResult};
use crate::input::{duration_as_pytimedelta, EitherTimedelta, Input};

use super::datetime::extract_microseconds_precision;
use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

#[derive(Debug, Clone)]
pub struct TimeDeltaValidator {
    strict: bool,
    constraints: Option<TimedeltaConstraints>,
    microseconds_precision: speedate::MicrosecondsPrecisionOverflowBehavior,
}

#[derive(Debug, Clone)]
struct TimedeltaConstraints {
    le: Option<Duration>,
    lt: Option<Duration>,
    ge: Option<Duration>,
    gt: Option<Duration>,
}

fn get_constraint(schema: &PyDict, key: &str) -> PyResult<Option<Duration>> {
    match schema.get_item(key) {
        Some(value) => {
            let either_timedelta = EitherTimedelta::try_from(value)?;
            Ok(Some(either_timedelta.to_duration()?))
        }
        None => Ok(None),
    }
}

impl BuildValidator for TimeDeltaValidator {
    const EXPECTED_TYPE: &'static str = "timedelta";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        _definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let constraints = TimedeltaConstraints {
            le: get_constraint(schema, "le")?,
            lt: get_constraint(schema, "lt")?,
            ge: get_constraint(schema, "ge")?,
            gt: get_constraint(schema, "gt")?,
        };

        Ok(Self {
            strict: is_strict(schema, config)?,
            constraints: (constraints.le.is_some()
                || constraints.lt.is_some()
                || constraints.ge.is_some()
                || constraints.gt.is_some())
            .then_some(constraints),
            microseconds_precision: extract_microseconds_precision(schema, config)?,
        }
        .into())
    }
}

impl_py_gc_traverse!(TimeDeltaValidator {});

impl Validator for TimeDeltaValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        let timedelta = input.validate_timedelta(state.strict_or(self.strict), self.microseconds_precision)?;
        let py_timedelta = timedelta.try_into_py(py)?;
        if let Some(constraints) = &self.constraints {
            let raw_timedelta = timedelta.to_duration()?;

            macro_rules! check_constraint {
                ($constraint:ident, $error:ident) => {
                    if let Some(constraint) = &constraints.$constraint {
                        if !raw_timedelta.$constraint(constraint) {
                            return Err(ValError::new(
                                ErrorType::$error {
                                    context: None,
                                    $constraint: duration_as_pytimedelta(py, constraint)?
                                        .repr()?
                                        .to_string()
                                        .into(),
                                },
                                py_timedelta.as_ref(),
                            ));
                        }
                    }
                };
            }

            check_constraint!(le, LessThanEqual);
            check_constraint!(lt, LessThan);
            check_constraint!(ge, GreaterThanEqual);
            check_constraint!(gt, GreaterThan);
        }
        Ok(py_timedelta.into())
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
