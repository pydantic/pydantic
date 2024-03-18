use pyo3::intern;
use pyo3::prelude::*;
use pyo3::sync::GILOnceCell;
use pyo3::types::{PyDict, PyString};
use speedate::{DateTime, Time};
use std::cmp::Ordering;
use strum::EnumMessage;

use crate::build_tools::{is_strict, py_schema_error_type};
use crate::build_tools::{py_schema_err, schema_or_config_same};
use crate::errors::ToErrorValue;
use crate::errors::{py_err_string, ErrorType, ErrorTypeDefaults, ValError, ValResult};
use crate::input::{EitherDateTime, Input};

use crate::tools::SchemaDict;

use super::Exactness;
use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

#[derive(Debug, Clone)]
pub struct DateTimeValidator {
    strict: bool,
    constraints: Option<DateTimeConstraints>,
    microseconds_precision: speedate::MicrosecondsPrecisionOverflowBehavior,
}

pub(crate) fn extract_microseconds_precision(
    schema: &Bound<'_, PyDict>,
    config: Option<&Bound<'_, PyDict>>,
) -> PyResult<speedate::MicrosecondsPrecisionOverflowBehavior> {
    schema_or_config_same(schema, config, intern!(schema.py(), "microseconds_precision"))?
        .map_or(
            Ok(speedate::MicrosecondsPrecisionOverflowBehavior::Truncate),
            |v: &PyString| {
                speedate::MicrosecondsPrecisionOverflowBehavior::try_from(v.extract::<String>().unwrap().as_str())
            },
        )
        .map_err(|_| {
            py_schema_error_type!("Invalid `microseconds_precision`, must be one of \"truncate\" or \"error\"")
        })
}

impl BuildValidator for DateTimeValidator {
    const EXPECTED_TYPE: &'static str = "datetime";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        Ok(Self {
            strict: is_strict(schema, config)?,
            constraints: DateTimeConstraints::from_py(schema)?,
            microseconds_precision: extract_microseconds_precision(schema, config)?,
        }
        .into())
    }
}

impl_py_gc_traverse!(DateTimeValidator {});

impl Validator for DateTimeValidator {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<PyObject> {
        let strict = state.strict_or(self.strict);
        let datetime = match input.validate_datetime(strict, self.microseconds_precision) {
            Ok(val_match) => val_match.unpack(state),
            // if the error was a parsing error, in lax mode we allow dates and add the time 00:00:00
            Err(line_errors @ ValError::LineErrors(..)) if !strict => {
                state.floor_exactness(Exactness::Lax);
                datetime_from_date(input)?.ok_or(line_errors)?
            }
            Err(otherwise) => return Err(otherwise),
        };
        if let Some(constraints) = &self.constraints {
            // if we get an error from as_speedate, it's probably because the input datetime was invalid
            // specifically had an invalid tzinfo, hence here we return a validation error
            let speedate_dt = match datetime.as_raw() {
                Ok(dt) => dt,
                Err(err) => {
                    let error = py_err_string(py, err);
                    return Err(ValError::new(
                        ErrorType::DatetimeObjectInvalid { error, context: None },
                        input,
                    ));
                }
            };
            macro_rules! check_constraint {
                ($constraint:ident, $error:ident) => {
                    if let Some(constraint) = &constraints.$constraint {
                        if !speedate_dt.$constraint(constraint) {
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

            if let Some(ref now_constraint) = constraints.now {
                let offset = now_constraint.utc_offset(py)?;
                let now = DateTime::now(offset).map_err(|e| {
                    py_schema_error_type!("DateTime::now() error: {}", e.get_documentation().unwrap_or("unknown"))
                })?;
                // `if let Some(c)` to match behaviour of gt/lt/le/ge
                if let Some(c) = speedate_dt.partial_cmp(&now) {
                    let dt_compliant = now_constraint.op.compare(c);
                    if !dt_compliant {
                        let error_type = match now_constraint.op {
                            NowOp::Past => ErrorTypeDefaults::DatetimePast,
                            NowOp::Future => ErrorTypeDefaults::DatetimeFuture,
                        };
                        return Err(ValError::new(error_type, input));
                    }
                }
            }

            if let Some(ref tz_constraint) = constraints.tz {
                tz_constraint.tz_check(speedate_dt.time.tz_offset, input)?;
            }
        }
        Ok(datetime.try_into_py(py)?)
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}

/// In lax mode, if the input is not a datetime, we try parsing the input as a date and add the "00:00:00" time.
/// Ok(None) means that this is not relevant to datetimes (the input was not a date nor a string)
fn datetime_from_date<'py>(input: &(impl Input<'py> + ?Sized)) -> Result<Option<EitherDateTime<'py>>, ValError> {
    let either_date = match input.validate_date(false) {
        Ok(val_match) => val_match.into_inner(),
        // if the error was a parsing error, update the error type from DateParsing to DatetimeFromDateParsing
        Err(ValError::LineErrors(mut line_errors)) => {
            if line_errors.iter_mut().fold(false, |has_parsing_error, line_error| {
                if let ErrorType::DateParsing { error, .. } = &mut line_error.error_type {
                    line_error.error_type = ErrorType::DatetimeFromDateParsing {
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

    let zero_time = Time {
        hour: 0,
        minute: 0,
        second: 0,
        microsecond: 0,
        tz_offset: None,
    };

    let datetime = DateTime {
        date: either_date.as_raw()?,
        time: zero_time,
    };
    Ok(Some(EitherDateTime::Raw(datetime)))
}

#[derive(Debug, Clone)]
struct DateTimeConstraints {
    le: Option<DateTime>,
    lt: Option<DateTime>,
    ge: Option<DateTime>,
    gt: Option<DateTime>,
    now: Option<NowConstraint>,
    tz: Option<TZConstraint>,
}

impl DateTimeConstraints {
    fn from_py(schema: &Bound<'_, PyDict>) -> PyResult<Option<Self>> {
        let py = schema.py();
        let c = Self {
            le: py_datetime_as_datetime(schema, intern!(py, "le"))?,
            lt: py_datetime_as_datetime(schema, intern!(py, "lt"))?,
            ge: py_datetime_as_datetime(schema, intern!(py, "ge"))?,
            gt: py_datetime_as_datetime(schema, intern!(py, "gt"))?,
            now: NowConstraint::from_py(schema)?,
            tz: TZConstraint::from_py(schema)?,
        };
        if c.le.is_some() || c.lt.is_some() || c.ge.is_some() || c.gt.is_some() || c.now.is_some() || c.tz.is_some() {
            Ok(Some(c))
        } else {
            Ok(None)
        }
    }
}

fn py_datetime_as_datetime(schema: &Bound<'_, PyDict>, field: &Bound<'_, PyString>) -> PyResult<Option<DateTime>> {
    match schema.get_as(field)? {
        Some(dt) => Ok(Some(EitherDateTime::Py(dt).as_raw()?)),
        None => Ok(None),
    }
}

#[derive(Debug, Clone)]
pub enum NowOp {
    Past,
    Future,
}

impl NowOp {
    pub fn compare(&self, ordering: Ordering) -> bool {
        match ordering {
            Ordering::Less => matches!(self, Self::Past),
            Ordering::Equal => false,
            Ordering::Greater => matches!(self, Self::Future),
        }
    }

    pub fn from_str(s: &str) -> PyResult<Self> {
        match s {
            "past" => Ok(NowOp::Past),
            "future" => Ok(NowOp::Future),
            _ => py_schema_err!("Invalid now_op {:?}", s),
        }
    }
}

#[derive(Debug, Clone)]
pub struct NowConstraint {
    pub op: NowOp,
    utc_offset: Option<i32>,
}

static TIME_LOCALTIME: GILOnceCell<PyObject> = GILOnceCell::new();

fn get_localtime(py: Python) -> PyResult<PyObject> {
    Ok(py.import_bound("time")?.getattr("localtime")?.into_py(py))
}

impl NowConstraint {
    /// Get the UTC offset in seconds either from the utc_offset field or by calling `time.localtime().tm_gmtoff`.
    /// Note: although the attribute is called "gmtoff", it is actually the offset in the UTC direction,
    /// hence no need to negate it.
    pub fn utc_offset(&self, py: Python) -> PyResult<i32> {
        if let Some(utc_offset) = self.utc_offset {
            Ok(utc_offset)
        } else {
            let localtime = TIME_LOCALTIME.get_or_init(py, || get_localtime(py).unwrap());
            localtime.bind(py).call0()?.getattr(intern!(py, "tm_gmtoff"))?.extract()
        }
    }

    pub fn from_py(schema: &Bound<'_, PyDict>) -> PyResult<Option<Self>> {
        let py = schema.py();
        match schema.get_as::<Bound<'_, PyString>>(intern!(py, "now_op"))? {
            Some(op) => Ok(Some(Self {
                op: NowOp::from_str(op.to_str()?)?,
                utc_offset: schema.get_as(intern!(py, "now_utc_offset"))?,
            })),
            None => Ok(None),
        }
    }
}

#[derive(Debug, Clone)]
pub(super) enum TZConstraint {
    Naive,
    Aware(Option<i32>),
}

impl TZConstraint {
    pub(super) fn from_str(s: &str) -> PyResult<Self> {
        match s {
            "naive" => Ok(TZConstraint::Naive),
            "aware" => Ok(TZConstraint::Aware(None)),
            _ => py_schema_err!("Invalid tz_constraint {:?}", s),
        }
    }

    pub(super) fn from_py(schema: &Bound<'_, PyDict>) -> PyResult<Option<Self>> {
        let py = schema.py();
        let tz_constraint = match schema.get_item(intern!(py, "tz_constraint"))? {
            Some(c) => c,
            None => return Ok(None),
        };
        if let Ok(s) = tz_constraint.downcast::<PyString>() {
            let s = s.to_str()?;
            Ok(Some(Self::from_str(s)?))
        } else {
            let tz: i32 = tz_constraint.extract()?;
            Ok(Some(TZConstraint::Aware(Some(tz))))
        }
    }

    pub(super) fn tz_check(&self, tz_offset: Option<i32>, input: impl ToErrorValue) -> ValResult<()> {
        match (self, tz_offset) {
            (TZConstraint::Aware(_), None) => return Err(ValError::new(ErrorTypeDefaults::TimezoneAware, input)),
            (TZConstraint::Aware(Some(tz_expected)), Some(tz_actual)) => {
                let tz_expected = *tz_expected;
                if tz_expected != tz_actual {
                    return Err(ValError::new(
                        ErrorType::TimezoneOffset {
                            tz_expected,
                            tz_actual,
                            context: None,
                        },
                        input,
                    ));
                }
            }
            (TZConstraint::Naive, Some(_)) => return Err(ValError::new(ErrorTypeDefaults::TimezoneNaive, input)),
            _ => (),
        }
        Ok(())
    }
}
