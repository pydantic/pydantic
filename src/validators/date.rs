use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDate, PyDict, PyString};
use speedate::{Date, Time};
use strum::EnumMessage;

use crate::build_tools::{is_strict, py_schema_error_type};
use crate::errors::{ErrorType, ErrorTypeDefaults, ValError, ValResult};
use crate::input::{EitherDate, Input};

use crate::tools::SchemaDict;
use crate::validators::datetime::{NowConstraint, NowOp};

use super::Exactness;
use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

#[derive(Debug, Clone)]
pub struct DateValidator {
    strict: bool,
    constraints: Option<DateConstraints>,
}

impl BuildValidator for DateValidator {
    const EXPECTED_TYPE: &'static str = "date";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        Ok(Self {
            strict: is_strict(schema, config)?,
            constraints: DateConstraints::from_py(schema)?,
        }
        .into())
    }
}

impl_py_gc_traverse!(DateValidator {});

impl Validator for DateValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<PyObject> {
        let strict = state.strict_or(self.strict);
        let date = match input.validate_date(strict) {
            Ok(val_match) => val_match.unpack(state),
            // if the error was a parsing error, in lax mode we allow datetimes at midnight
            Err(line_errors @ ValError::LineErrors(..)) if !strict => {
                state.floor_exactness(Exactness::Lax);
                date_from_datetime(input)?.ok_or(line_errors)?
            }
            Err(otherwise) => return Err(otherwise),
        };
        if let Some(constraints) = &self.constraints {
            let raw_date = date.as_raw()?;

            macro_rules! check_constraint {
                ($constraint:ident, $error:ident) => {
                    if let Some(constraint) = &constraints.$constraint {
                        if !raw_date.$constraint(constraint) {
                            return Err(ValError::new(
                                ErrorType::$error {
                                    $constraint: constraint.to_string().into(),
                                    context: None,
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

            if let Some(ref today_constraint) = constraints.today {
                let offset = today_constraint.utc_offset(py)?;
                let today = Date::today(offset).map_err(|e| {
                    py_schema_error_type!("Date::today() error: {}", e.get_documentation().unwrap_or("unknown"))
                })?;
                // `if let Some(c)` to match behaviour of gt/lt/le/ge
                if let Some(c) = raw_date.partial_cmp(&today) {
                    let date_compliant = today_constraint.op.compare(c);
                    if !date_compliant {
                        let error_type = match today_constraint.op {
                            NowOp::Past => ErrorTypeDefaults::DatePast,
                            NowOp::Future => ErrorTypeDefaults::DateFuture,
                        };
                        return Err(ValError::new(error_type, input));
                    }
                }
            }
        }
        Ok(date.try_into_py(py)?)
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}

/// In lax mode, if the input is not a date, we try parsing the input as a datetime, then check it is an
/// "exact date", e.g. has a zero time component.
///
/// Ok(None) means that this is not relevant to dates (the input was not a datetime nor a string)
fn date_from_datetime<'data>(input: &'data impl Input<'data>) -> Result<Option<EitherDate<'data>>, ValError> {
    let either_dt = match input.validate_datetime(false, speedate::MicrosecondsPrecisionOverflowBehavior::Truncate) {
        Ok(val_match) => val_match.into_inner(),
        // if the error was a parsing error, update the error type from DatetimeParsing to DateFromDatetimeParsing
        // and return it
        Err(ValError::LineErrors(mut line_errors)) => {
            if line_errors.iter_mut().fold(false, |has_parsing_error, line_error| {
                if let ErrorType::DatetimeParsing { error, .. } = &mut line_error.error_type {
                    line_error.error_type = ErrorType::DateFromDatetimeParsing {
                        error: std::mem::take(error),
                        context: None,
                    };
                    true
                } else {
                    has_parsing_error
                }
            }) {
                return Err(ValError::LineErrors(line_errors));
            }
            return Ok(None);
        }
        // for any other error, don't return it
        Err(_) => return Ok(None),
    };
    let dt = either_dt.as_raw()?;
    let zero_time = Time {
        hour: 0,
        minute: 0,
        second: 0,
        microsecond: 0,
        tz_offset: dt.time.tz_offset,
    };
    if dt.time == zero_time {
        Ok(Some(EitherDate::Raw(dt.date)))
    } else {
        Err(ValError::new(ErrorTypeDefaults::DateFromDatetimeInexact, input))
    }
}

#[derive(Debug, Clone)]
struct DateConstraints {
    le: Option<Date>,
    lt: Option<Date>,
    ge: Option<Date>,
    gt: Option<Date>,
    today: Option<NowConstraint>,
}

impl DateConstraints {
    fn from_py(schema: &Bound<'_, PyDict>) -> PyResult<Option<Self>> {
        let py = schema.py();
        let c = Self {
            le: convert_pydate(schema, intern!(py, "le"))?,
            lt: convert_pydate(schema, intern!(py, "lt"))?,
            ge: convert_pydate(schema, intern!(py, "ge"))?,
            gt: convert_pydate(schema, intern!(py, "gt"))?,
            today: NowConstraint::from_py(schema)?,
        };
        if c.le.is_some() || c.lt.is_some() || c.ge.is_some() || c.gt.is_some() || c.today.is_some() {
            Ok(Some(c))
        } else {
            Ok(None)
        }
    }
}

fn convert_pydate(schema: &Bound<'_, PyDict>, field: &Bound<'_, PyString>) -> PyResult<Option<Date>> {
    match schema.get_as::<Bound<'_, PyDate>>(field)? {
        Some(date) => Ok(Some(EitherDate::Py(date).as_raw()?)),
        None => Ok(None),
    }
}
