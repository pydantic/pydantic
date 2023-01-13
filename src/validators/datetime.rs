use pyo3::intern;
use pyo3::once_cell::GILOnceCell;
use pyo3::prelude::*;
use pyo3::types::{PyDateTime, PyDict, PyString};
use speedate::DateTime;
use std::cmp::Ordering;
use strum::EnumMessage;

use crate::build_tools::{is_strict, py_err, py_error_type, SchemaDict};
use crate::errors::{py_err_string, ErrorType, ValError, ValResult};
use crate::input::{EitherDateTime, Input};
use crate::recursion_guard::RecursionGuard;

use super::{BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct DateTimeValidator {
    strict: bool,
    constraints: Option<DateTimeConstraints>,
}

impl BuildValidator for DateTimeValidator {
    const EXPECTED_TYPE: &'static str = "datetime";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        _build_context: &mut BuildContext<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        Ok(Self {
            strict: is_strict(schema, config)?,
            constraints: DateTimeConstraints::from_py(schema)?,
        }
        .into())
    }
}

impl Validator for DateTimeValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let datetime = input.validate_datetime(extra.strict.unwrap_or(self.strict))?;
        if let Some(constraints) = &self.constraints {
            // if we get an error from as_speedate, it's probably because the input datetime was invalid
            // specifically had an invalid tzinfo, hence here we return a validation error
            let speedate_dt = match datetime.as_raw() {
                Ok(dt) => dt,
                Err(err) => {
                    let error = py_err_string(py, err);
                    return Err(ValError::new(ErrorType::DatetimeObjectInvalid { error }, input));
                }
            };
            macro_rules! check_constraint {
                ($constraint:ident, $error:ident) => {
                    if let Some(constraint) = &constraints.$constraint {
                        if !speedate_dt.$constraint(constraint) {
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

            if let Some(ref now_constraint) = constraints.now {
                let offset = now_constraint.utc_offset(py)?;
                let now = DateTime::now(offset).map_err(|e| {
                    py_error_type!("DateTime::now() error: {}", e.get_documentation().unwrap_or("unknown"))
                })?;
                // `if let Some(c)` to match behaviour of gt/lt/le/ge
                if let Some(c) = speedate_dt.partial_cmp(&now) {
                    let dt_compliant = now_constraint.op.compare(c);
                    if !dt_compliant {
                        let error_type = match now_constraint.op {
                            NowOp::Past => ErrorType::DatetimePast,
                            NowOp::Future => ErrorType::DatetimeFuture,
                        };
                        return Err(ValError::new(error_type, input));
                    }
                }
            }

            match (&constraints.tz, speedate_dt.offset) {
                (Some(TZConstraint::Aware), None) => return Err(ValError::new(ErrorType::DatetimeAware, input)),
                (Some(TZConstraint::Naive), Some(_)) => return Err(ValError::new(ErrorType::DatetimeNaive, input)),
                _ => (),
            }
        }
        Ok(datetime.try_into_py(py)?)
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
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
    fn from_py(schema: &PyDict) -> PyResult<Option<Self>> {
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

fn py_datetime_as_datetime(schema: &PyDict, field: &PyString) -> PyResult<Option<DateTime>> {
    match schema.get_as::<&PyDateTime>(field)? {
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
            _ => py_err!("Invalid now_op {:?}", s),
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
    Ok(py.import("time")?.getattr("localtime")?.into_py(py))
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
            localtime
                .as_ref(py)
                .call0()?
                .getattr(intern!(py, "tm_gmtoff"))?
                .extract()
        }
    }

    pub fn from_py(schema: &PyDict) -> PyResult<Option<Self>> {
        let py = schema.py();
        match schema.get_as(intern!(py, "now_op"))? {
            Some(op) => Ok(Some(Self {
                op: NowOp::from_str(op)?,
                utc_offset: schema.get_as(intern!(py, "now_utc_offset"))?,
            })),
            None => Ok(None),
        }
    }
}

#[derive(Debug, Clone)]
pub enum TZConstraint {
    Aware,
    Naive,
}

impl TZConstraint {
    pub fn from_str(s: &str) -> PyResult<Self> {
        match s {
            "aware" => Ok(TZConstraint::Aware),
            "naive" => Ok(TZConstraint::Naive),
            _ => py_err!("Invalid tz_constraint {:?}", s),
        }
    }

    pub fn from_py(schema: &PyDict) -> PyResult<Option<Self>> {
        let py = schema.py();
        match schema.get_as(intern!(py, "tz_constraint"))? {
            Some(kind) => Ok(Some(Self::from_str(kind)?)),
            None => Ok(None),
        }
    }
}
