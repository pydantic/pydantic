use pyo3::prelude::*;
use pyo3::types::{PyDelta, PyDeltaAccess, PyDict};
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
                                    $constraint: pydelta_to_human_readable(duration_as_pytimedelta(py, constraint)?)
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
fn pydelta_to_human_readable(py_delta: &PyDelta) -> String {
    let total_seconds = py_delta.get_seconds();
    let hours = total_seconds / 3600;
    let minutes = (total_seconds % 3600) / 60;
    let seconds = total_seconds % 60;
    let microseconds = py_delta.get_microseconds();
    let days = py_delta.get_days();

    let mut formatted_duration = Vec::new();

    if days != 0 {
        formatted_duration.push(format!("{} day{}", days, if days != 1 { "s" } else { "" }));
    }

    if hours != 0 {
        formatted_duration.push(format!("{} hour{}", hours, if hours != 1 { "s" } else { "" }));
    }

    if minutes != 0 {
        formatted_duration.push(format!("{} minute{}", minutes, if minutes != 1 { "s" } else { "" }));
    }

    if seconds != 0 {
        formatted_duration.push(format!("{} second{}", seconds, if seconds != 1 { "s" } else { "" }));
    }

    if microseconds != 0 {
        formatted_duration.push(format!(
            "{} microsecond{}",
            microseconds,
            if microseconds != 1 { "s" } else { "" }
        ));
    }

    if formatted_duration.is_empty() {
        formatted_duration.push("0 seconds".to_string());
    }

    formatted_duration.join(" and ")
}
