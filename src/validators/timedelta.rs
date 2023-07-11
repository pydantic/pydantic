use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDelta, PyDict};
use speedate::Duration;

use crate::build_tools::is_strict;
use crate::errors::{ErrorType, ValError, ValResult};
use crate::input::{duration_as_pytimedelta, pytimedelta_as_duration, Input};
use crate::recursion_guard::RecursionGuard;
use crate::tools::SchemaDict;

use super::datetime::extract_microseconds_precision;
use super::{BuildValidator, CombinedValidator, Definitions, DefinitionsBuilder, Extra, Validator};

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

impl BuildValidator for TimeDeltaValidator {
    const EXPECTED_TYPE: &'static str = "timedelta";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        _definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py: Python<'_> = schema.py();
        let constraints = TimedeltaConstraints {
            le: schema
                .get_as::<&PyDelta>(intern!(py, "le"))?
                .map(pytimedelta_as_duration),
            lt: schema
                .get_as::<&PyDelta>(intern!(py, "lt"))?
                .map(pytimedelta_as_duration),
            ge: schema
                .get_as::<&PyDelta>(intern!(py, "ge"))?
                .map(pytimedelta_as_duration),
            gt: schema
                .get_as::<&PyDelta>(intern!(py, "gt"))?
                .map(pytimedelta_as_duration),
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

impl Validator for TimeDeltaValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        _definitions: &'data Definitions<CombinedValidator>,
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let timedelta = input.validate_timedelta(extra.strict.unwrap_or(self.strict), self.microseconds_precision)?;
        let py_timedelta = timedelta.try_into_py(py)?;
        if let Some(constraints) = &self.constraints {
            let raw_timedelta = timedelta.as_raw();

            macro_rules! check_constraint {
                ($constraint:ident, $error:ident) => {
                    if let Some(constraint) = &constraints.$constraint {
                        if !raw_timedelta.$constraint(constraint) {
                            return Err(ValError::new(
                                ErrorType::$error {
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
