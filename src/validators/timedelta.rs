use pyo3::exceptions::PyValueError;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDelta, PyDeltaAccess, PyDict, PyString};
use speedate::{Duration, MicrosecondsPrecisionOverflowBehavior};

use crate::build_tools::is_strict;
use crate::errors::{ErrorType, ValError, ValResult};
use crate::input::{duration_as_pytimedelta, Input};

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

fn get_constraint(schema: &Bound<'_, PyDict>, key: &Bound<'_, PyString>) -> PyResult<Option<Duration>> {
    match schema.get_item(key)? {
        Some(value) => match value.validate_timedelta(false, MicrosecondsPrecisionOverflowBehavior::default()) {
            Ok(v) => Ok(Some(v.into_inner().to_duration()?)),
            Err(_) => Err(PyValueError::new_err(format!(
                "'{key}' must be coercible to a timedelta instance"
            ))),
        },
        None => Ok(None),
    }
}

impl BuildValidator for TimeDeltaValidator {
    const EXPECTED_TYPE: &'static str = "timedelta";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let constraints = TimedeltaConstraints {
            le: get_constraint(schema, intern!(py, "le"))?,
            lt: get_constraint(schema, intern!(py, "lt"))?,
            ge: get_constraint(schema, intern!(py, "ge"))?,
            gt: get_constraint(schema, intern!(py, "gt"))?,
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
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<PyObject> {
        let timedelta = input
            .validate_timedelta(state.strict_or(self.strict), self.microseconds_precision)?
            .unpack(state);
        let py_timedelta = timedelta.clone().into_pyobject(py)?;
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
                                py_timedelta.as_any(),
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

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}
fn pydelta_to_human_readable(py_delta: Bound<'_, PyDelta>) -> String {
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
