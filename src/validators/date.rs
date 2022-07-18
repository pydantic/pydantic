use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDate, PyDict, PyString};
use speedate::{Date, Time};

use crate::build_tools::{is_strict, SchemaDict};
use crate::errors::{ErrorKind, ValError, ValResult};
use crate::input::{EitherDate, Input};
use crate::recursion_guard::RecursionGuard;

use super::{BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct DateValidator {
    strict: bool,
    constraints: Option<DateConstraints>,
}

#[derive(Debug, Clone)]
struct DateConstraints {
    le: Option<Date>,
    lt: Option<Date>,
    ge: Option<Date>,
    gt: Option<Date>,
}

impl BuildValidator for DateValidator {
    const EXPECTED_TYPE: &'static str = "date";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        _build_context: &mut BuildContext,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let has_constraints = schema.get_item(intern!(py, "le")).is_some()
            || schema.get_item(intern!(py, "lt")).is_some()
            || schema.get_item(intern!(py, "ge")).is_some()
            || schema.get_item(intern!(py, "gt")).is_some();

        Ok(Self {
            strict: is_strict(schema, config)?,
            constraints: match has_constraints {
                true => Some(DateConstraints {
                    le: convert_pydate(schema, intern!(py, "le"))?,
                    lt: convert_pydate(schema, intern!(py, "lt"))?,
                    ge: convert_pydate(schema, intern!(py, "ge"))?,
                    gt: convert_pydate(schema, intern!(py, "gt"))?,
                }),
                false => None,
            },
        }
        .into())
    }
}

impl Validator for DateValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let date = match input.validate_date(extra.strict.unwrap_or(self.strict)) {
            Ok(date) => date,
            // if the date error was an internal error, return that immediately
            Err(ValError::InternalErr(internal_err)) => return Err(ValError::InternalErr(internal_err)),
            Err(date_err) => match self.strict {
                // if we're in strict mode, we doing try coercing from a date
                true => return Err(date_err),
                // otherwise, try creating a date from a datetime input
                false => date_from_datetime(input, date_err),
            }?,
        };
        if let Some(constraints) = &self.constraints {
            let raw_date = date.as_raw()?;

            macro_rules! check_constraint {
                ($constraint:ident, $error:ident) => {
                    if let Some(constraint) = &constraints.$constraint {
                        if !raw_date.$constraint(constraint) {
                            return Err(ValError::new(
                                ErrorKind::$error {
                                    $constraint: constraint.to_string(),
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
        }
        Ok(date.try_into_py(py)?)
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}

/// In lax mode, if the input is not a date, we try parsing the input as a datetime, then check it is an
/// "exact date", e.g. has a zero time component.
fn date_from_datetime<'data>(
    input: &'data impl Input<'data>,
    date_err: ValError<'data>,
) -> ValResult<'data, EitherDate<'data>> {
    let either_dt = match input.validate_datetime(false) {
        Ok(dt) => dt,
        Err(dt_err) => {
            return match dt_err {
                ValError::LineErrors(mut line_errors) => {
                    // if we got a errors while parsing the datetime,
                    // convert DateTimeParsing -> DateFromDatetimeParsing but keep the rest of the error unchanged
                    for line_error in line_errors.iter_mut() {
                        match line_error.kind {
                            ErrorKind::DateTimeParsing { ref error } => {
                                line_error.kind = ErrorKind::DateFromDatetimeParsing {
                                    error: error.to_string(),
                                };
                            }
                            _ => {
                                return Err(date_err);
                            }
                        }
                    }
                    Err(ValError::LineErrors(line_errors))
                }
                ValError::InternalErr(internal_err) => Err(ValError::InternalErr(internal_err)),
            };
        }
    };
    let dt = either_dt.as_raw()?;
    let zero_time = Time {
        hour: 0,
        minute: 0,
        second: 0,
        microsecond: 0,
    };
    if dt.time == zero_time && dt.offset.is_none() {
        Ok(EitherDate::Raw(dt.date))
    } else {
        Err(ValError::new(ErrorKind::DateFromDatetimeInexact, input))
    }
}

fn convert_pydate(schema: &PyDict, field: &PyString) -> PyResult<Option<Date>> {
    match schema.get_as::<&PyDate>(field)? {
        Some(date) => Ok(Some(EitherDate::Py(date).as_raw()?)),
        None => Ok(None),
    }
}
