use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDate, PyDateTime, PyDelta, PyTime, PyTzInfo};
use speedate::{Date, DateTime, Time};
use strum::EnumMessage;

use super::Input;
use crate::errors::{ErrorKind, ValError, ValResult};

pub enum EitherDate<'a> {
    Raw(Date),
    Py(&'a PyDate),
}

impl<'a> From<Date> for EitherDate<'a> {
    fn from(date: Date) -> Self {
        Self::Raw(date)
    }
}

impl<'a> From<&'a PyDate> for EitherDate<'a> {
    fn from(date: &'a PyDate) -> Self {
        Self::Py(date)
    }
}

macro_rules! pydate_as_date {
    ($py_date:expr) => {
        speedate::Date {
            year: $py_date.getattr(pyo3::intern!($py_date.py(), "year"))?.extract()?,
            month: $py_date.getattr(pyo3::intern!($py_date.py(), "month"))?.extract()?,
            day: $py_date.getattr(pyo3::intern!($py_date.py(), "day"))?.extract()?,
        }
    };
}
pub(crate) use pydate_as_date;

impl<'a> EitherDate<'a> {
    pub fn as_raw(&self) -> PyResult<Date> {
        match self {
            Self::Raw(date) => Ok(date.clone()),
            Self::Py(py_date) => Ok(pydate_as_date!(py_date)),
        }
    }

    pub fn try_into_py(self, py: Python<'_>) -> PyResult<PyObject> {
        let date = match self {
            Self::Py(date) => Ok(date),
            Self::Raw(date) => PyDate::new(py, date.year as i32, date.month, date.day),
        }?;
        Ok(date.into_py(py))
    }
}

pub enum EitherTime<'a> {
    Raw(Time),
    Py(&'a PyTime),
}

impl<'a> From<Time> for EitherTime<'a> {
    fn from(time: Time) -> Self {
        Self::Raw(time)
    }
}

impl<'a> From<&'a PyTime> for EitherTime<'a> {
    fn from(time: &'a PyTime) -> Self {
        Self::Py(time)
    }
}

macro_rules! pytime_as_time {
    ($py_time:expr) => {
        speedate::Time {
            hour: $py_time.getattr(pyo3::intern!($py_time.py(), "hour"))?.extract()?,
            minute: $py_time.getattr(pyo3::intern!($py_time.py(), "minute"))?.extract()?,
            second: $py_time.getattr(pyo3::intern!($py_time.py(), "second"))?.extract()?,
            microsecond: $py_time
                .getattr(pyo3::intern!($py_time.py(), "microsecond"))?
                .extract()?,
        }
    };
}
pub(crate) use pytime_as_time;

impl<'a> EitherTime<'a> {
    pub fn as_raw(&self) -> PyResult<Time> {
        match self {
            Self::Raw(time) => Ok(time.clone()),
            Self::Py(py_time) => Ok(pytime_as_time!(py_time)),
        }
    }

    pub fn try_into_py(self, py: Python<'_>) -> PyResult<PyObject> {
        let time = match self {
            Self::Py(time) => Ok(time),
            Self::Raw(time) => PyTime::new(py, time.hour, time.minute, time.second, time.microsecond, None),
        }?;
        Ok(time.into_py(py))
    }
}

pub enum EitherDateTime<'a> {
    Raw(DateTime),
    Py(&'a PyDateTime),
}

impl<'a> From<DateTime> for EitherDateTime<'a> {
    fn from(dt: DateTime) -> Self {
        Self::Raw(dt)
    }
}

impl<'a> From<&'a PyDateTime> for EitherDateTime<'a> {
    fn from(dt: &'a PyDateTime) -> Self {
        Self::Py(dt)
    }
}

pub fn pydatetime_as_datetime(py_dt: &PyDateTime) -> PyResult<DateTime> {
    let py = py_dt.py();

    let mut offset: Option<i32> = None;
    let tzinfo = py_dt.getattr(intern!(py, "tzinfo"))?;
    if !tzinfo.is_none() {
        let offset_delta = tzinfo.getattr(intern!(py, "utcoffset"))?.call1((py_dt.as_ref(),))?;
        // as per the docs, utcoffset() can return None
        if !offset_delta.is_none() {
            let offset_seconds: f64 = offset_delta.getattr(intern!(py, "total_seconds"))?.call0()?.extract()?;
            offset = Some(offset_seconds.round() as i32);
        }
    }

    Ok(DateTime {
        date: pydate_as_date!(py_dt),
        time: pytime_as_time!(py_dt),
        offset,
    })
}

impl<'a> EitherDateTime<'a> {
    pub fn as_raw(&self) -> PyResult<DateTime> {
        match self {
            Self::Raw(dt) => Ok(dt.clone()),
            Self::Py(py_dt) => pydatetime_as_datetime(py_dt),
        }
    }

    pub fn try_into_py(self, py: Python<'a>) -> PyResult<PyObject> {
        let dt = match self {
            Self::Raw(datetime) => {
                let tz: Option<PyObject> = match datetime.offset {
                    Some(offset) => {
                        let tz_info = TzInfo::new(offset);
                        Some(Py::new(py, tz_info)?.to_object(py))
                    }
                    None => None,
                };
                PyDateTime::new(
                    py,
                    datetime.date.year as i32,
                    datetime.date.month,
                    datetime.date.day,
                    datetime.time.hour,
                    datetime.time.minute,
                    datetime.time.second,
                    datetime.time.microsecond,
                    tz.as_ref(),
                )?
            }
            Self::Py(dt) => dt,
        };
        Ok(dt.into_py(py))
    }
}

pub fn bytes_as_date<'a>(input: &'a impl Input<'a>, bytes: &[u8]) -> ValResult<'a, EitherDate<'a>> {
    match Date::parse_bytes(bytes) {
        Ok(date) => Ok(date.into()),
        Err(err) => Err(ValError::new(
            ErrorKind::DateParsing {
                error: err.get_documentation().unwrap_or_default(),
            },
            input,
        )),
    }
}

pub fn bytes_as_time<'a>(input: &'a impl Input<'a>, bytes: &[u8]) -> ValResult<'a, EitherTime<'a>> {
    match Time::parse_bytes(bytes) {
        Ok(date) => Ok(date.into()),
        Err(err) => Err(ValError::new(
            ErrorKind::TimeParsing {
                error: err.get_documentation().unwrap_or_default(),
            },
            input,
        )),
    }
}

pub fn bytes_as_datetime<'a, 'b>(input: &'a impl Input<'a>, bytes: &'b [u8]) -> ValResult<'a, EitherDateTime<'a>> {
    match DateTime::parse_bytes(bytes) {
        Ok(dt) => Ok(dt.into()),
        Err(err) => Err(ValError::new(
            ErrorKind::DateTimeParsing {
                error: err.get_documentation().unwrap_or_default(),
            },
            input,
        )),
    }
}

pub fn int_as_datetime<'a>(
    input: &'a impl Input<'a>,
    timestamp: i64,
    timestamp_microseconds: u32,
) -> ValResult<EitherDateTime> {
    match DateTime::from_timestamp(timestamp, timestamp_microseconds) {
        Ok(dt) => Ok(dt.into()),
        Err(err) => Err(ValError::new(
            ErrorKind::DateTimeParsing {
                error: err.get_documentation().unwrap_or_default(),
            },
            input,
        )),
    }
}

pub fn float_as_datetime<'a>(input: &'a impl Input<'a>, timestamp: f64) -> ValResult<EitherDateTime> {
    let microseconds = timestamp.fract().abs() * 1_000_000.0;
    // checking for extra digits in microseconds is unreliable with large floats,
    // so we just round to the nearest microsecond
    int_as_datetime(input, timestamp.floor() as i64, microseconds.round() as u32)
}

pub fn date_as_datetime(date: &PyDate) -> PyResult<EitherDateTime> {
    let py = date.py();
    let dt = PyDateTime::new(
        py,
        date.getattr(intern!(py, "year"))?.extract()?,
        date.getattr(intern!(py, "month"))?.extract()?,
        date.getattr(intern!(py, "day"))?.extract()?,
        0,
        0,
        0,
        0,
        None,
    )?;
    Ok(dt.into())
}

const MAX_U32: i64 = u32::MAX as i64;

pub fn int_as_time<'a>(
    input: &'a impl Input<'a>,
    timestamp: i64,
    timestamp_microseconds: u32,
) -> ValResult<EitherTime> {
    let time_timestamp: u32 = match timestamp {
        t if t < 0_i64 => {
            return Err(ValError::new(
                ErrorKind::TimeParsing {
                    error: "time in seconds must be positive",
                },
                input,
            ));
        }
        // continue and use the speedate error for >86400
        t if t > MAX_U32 => u32::MAX,
        // ok
        t => t as u32,
    };
    match Time::from_timestamp(time_timestamp, timestamp_microseconds) {
        Ok(dt) => Ok(dt.into()),
        Err(err) => Err(ValError::new(
            ErrorKind::TimeParsing {
                error: err.get_documentation().unwrap_or_default(),
            },
            input,
        )),
    }
}

pub fn float_as_time<'a>(input: &'a impl Input<'a>, timestamp: f64) -> ValResult<EitherTime> {
    let microseconds = timestamp.fract().abs() * 1_000_000.0;
    // round for same reason as above
    int_as_time(input, timestamp.floor() as i64, microseconds.round() as u32)
}

#[pyclass(module = "pydantic_core._pydantic_core", extends = PyTzInfo)]
#[derive(Debug, Clone)]
struct TzInfo {
    seconds: i32,
}

#[pymethods]
impl TzInfo {
    #[new]
    fn new(seconds: i32) -> Self {
        Self { seconds }
    }

    fn utcoffset<'p>(&self, py: Python<'p>, _dt: &PyDateTime) -> PyResult<&'p PyDelta> {
        PyDelta::new(py, 0, self.seconds, 0, true)
    }

    fn tzname(&self, _dt: &PyDateTime) -> String {
        self.__str__()
    }

    fn dst(&self, _dt: &PyDateTime) -> Option<&PyDelta> {
        None
    }

    fn __repr__(&self) -> String {
        format!("TzInfo({})", self.__str__())
    }

    fn __str__(&self) -> String {
        if self.seconds == 0 {
            "UTC".to_string()
        } else {
            let mins = self.seconds / 60;
            format!("{:+03}:{:02}", mins / 60, (mins % 60).abs())
        }
    }
}
