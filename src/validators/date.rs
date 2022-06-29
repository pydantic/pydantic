use pyo3::prelude::*;
use pyo3::types::PyDict;
use speedate::{Date, Time};

use crate::build_tools::{is_strict, SchemaDict, SchemaError};
use crate::errors::{as_internal, context, err_val_error, ErrorKind, ValError, ValResult};
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
        let has_constraints = schema.get_item("le").is_some()
            || schema.get_item("lt").is_some()
            || schema.get_item("ge").is_some()
            || schema.get_item("gt").is_some();

        Ok(Self {
            strict: is_strict(schema, config)?,
            constraints: match has_constraints {
                true => Some(DateConstraints {
                    le: convert_pydate(schema, "le")?,
                    lt: convert_pydate(schema, "lt")?,
                    ge: convert_pydate(schema, "ge")?,
                    gt: convert_pydate(schema, "gt")?,
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
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let date = match self.strict {
            true => input.strict_date()?,
            false => {
                match input.lax_date() {
                    Ok(date) => date,
                    // if the date error was an internal error, return that immediately
                    Err(ValError::InternalErr(internal_err)) => return Err(ValError::InternalErr(internal_err)),
                    // otherwise, try creating a date from a datetime input
                    Err(date_err) => date_from_datetime(input, date_err)?,
                }
            }
        };
        self.validation_comparison(py, input, date)
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        self.validation_comparison(py, input, input.strict_date()?)
    }

    fn get_name(&self, _py: Python) -> String {
        Self::EXPECTED_TYPE.to_string()
    }
}

impl DateValidator {
    fn validation_comparison<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        date: EitherDate<'data>,
    ) -> ValResult<'data, PyObject> {
        if let Some(constraints) = &self.constraints {
            let raw_date = date.as_raw().map_err(as_internal)?;

            macro_rules! check_constraint {
                ($constraint:ident, $error:path, $key:literal) => {
                    if let Some(constraint) = &constraints.$constraint {
                        if !raw_date.$constraint(constraint) {
                            return err_val_error!(
                                input_value = input.as_error_value(),
                                kind = $error,
                                context = context!($key => constraint.to_string())
                            );
                        }
                    }
                };
            }

            check_constraint!(le, ErrorKind::LessThanEqual, "le");
            check_constraint!(lt, ErrorKind::LessThan, "lt");
            check_constraint!(ge, ErrorKind::GreaterThanEqual, "ge");
            check_constraint!(gt, ErrorKind::GreaterThan, "gt");
        }
        date.try_into_py(py).map_err(as_internal)
    }
}

/// In lax mode, if the input is not a date, we try parsing the input as a datetime, then check it is an
/// "exact date", e.g. has a zero time component.
fn date_from_datetime<'data>(
    input: &'data impl Input<'data>,
    date_err: ValError<'data>,
) -> ValResult<'data, EitherDate<'data>> {
    let either_dt = match input.lax_datetime() {
        Ok(dt) => dt,
        Err(dt_err) => {
            return match dt_err {
                ValError::LineErrors(mut line_errors) => {
                    // if we got a errors while parsing the datetime,
                    // convert DateTimeParsing -> DateFromDatetimeParsing but keep the rest of the error unchanged
                    for line_error in line_errors.iter_mut() {
                        match line_error.kind {
                            ErrorKind::DateTimeParsing => {
                                line_error.kind = ErrorKind::DateFromDatetimeParsing;
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
    let dt = either_dt.as_raw().map_err(as_internal)?;
    let zero_time = Time {
        hour: 0,
        minute: 0,
        second: 0,
        microsecond: 0,
    };
    if dt.time == zero_time && dt.offset.is_none() {
        Ok(EitherDate::Raw(dt.date))
    } else {
        err_val_error!(
            input_value = input.as_error_value(),
            kind = ErrorKind::DateFromDatetimeInexact
        )
    }
}

fn convert_pydate(schema: &PyDict, field: &str) -> PyResult<Option<Date>> {
    match schema.get_as::<&PyAny>(field)? {
        Some(obj) => {
            let prefix = format!(r#"Invalid "{}" constraint for date"#, field);
            let date = obj
                .lax_date()
                .map_err(|e| SchemaError::from_val_error(obj.py(), &prefix, e))?;
            Ok(Some(date.as_raw()?))
        }
        None => Ok(None),
    }
}
