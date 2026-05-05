use std::borrow::Cow;
use std::sync::Arc;

use pyo3::prelude::*;
use pyo3::types::{PyDate, PyDateTime, PyDict, PyTime};
use speedate::{Date, DateTime, Time};

use super::{
    BuildSerializer, CombinedSerializer, SerMode, TypeSerializer, infer_json_key, infer_serialize, infer_to_python,
};
use crate::PydanticSerializationUnexpectedValue;
use crate::definitions::DefinitionsBuilder;
use crate::serializers::SerializationState;
use crate::serializers::config::{FromConfig, TemporalMode};

pub(crate) fn datetime_to_seconds(dt: DateTime) -> f64 {
    dt.date.timestamp() as f64 + time_to_seconds(dt.time)
}

pub(crate) fn datetime_to_milliseconds(dt: DateTime) -> f64 {
    dt.date.timestamp_ms() as f64 + time_to_milliseconds(dt.time)
}

pub(crate) fn date_to_seconds(date: Date) -> f64 {
    date.timestamp() as f64
}

pub(crate) fn date_to_milliseconds(date: Date) -> f64 {
    date.timestamp_ms() as f64
}

pub(crate) fn time_to_seconds(time: Time) -> f64 {
    f64::from(time.hour) * 3600.0
        + f64::from(time.minute) * 60.0
        + f64::from(time.second)
        + f64::from(time.microsecond) / 1_000_000.0
}

pub(crate) fn time_to_milliseconds(time: Time) -> f64 {
    f64::from(time.hour) * 3_600_000.0
        + f64::from(time.minute) * 60_000.0
        + f64::from(time.second) * 1_000.0
        + f64::from(time.microsecond) / 1_000.0
}

const RFC2822_DAY_NAMES: [&str; 7] = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const RFC2822_MONTH_NAMES: [&str; 12] = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

/// Format a `Date` as an RFC 2822 (HTTP) date string at midnight UTC,
/// e.g. "Mon, 01 Jan 2024 00:00:00 GMT".
///
/// This mirrors the behaviour of `werkzeug.http.http_date`, which combines a bare
/// `date` with midnight in UTC before formatting.
pub(crate) fn date_to_rfc2822(date: Date) -> String {
    let midnight = Time {
        hour: 0,
        minute: 0,
        second: 0,
        microsecond: 0,
        tz_offset: None,
    };
    datetime_to_rfc2822(DateTime { date, time: midnight })
}

/// Format a `DateTime` as an RFC 2822 date string with `GMT` as the zone label,
/// e.g. "Mon, 01 Jan 2024 12:00:00 GMT".
///
/// This matches the output of Python's `email.utils.format_datetime(dt, usegmt=True)`,
/// which is what `werkzeug.http.http_date` uses for the HTTP `Date` header (the format
/// is RFC 2822 / RFC 5322 §3.3, which RFC 7231 §7.1.1.1 designates as the preferred HTTP
/// date format).
///
/// The datetime is converted to UTC before formatting:
/// - If `tz_offset` is `None` (naive), it is assumed to already be UTC.
/// - If `tz_offset` is `Some`, the offset is subtracted from the timestamp to get UTC.
pub(crate) fn datetime_to_rfc2822(dt: DateTime) -> String {
    // Compute the UTC unix timestamp (seconds since 1970-01-01 UTC).
    // `DateTime::timestamp()` ignores the timezone offset and returns the timestamp
    // as if the date/time were UTC, so we need to subtract the offset to get the
    // true UTC timestamp.
    let local_ts = dt.date.timestamp()
        + i64::from(dt.time.hour) * 3600
        + i64::from(dt.time.minute) * 60
        + i64::from(dt.time.second);
    let tz_offset = i64::from(dt.time.tz_offset.unwrap_or(0));
    let utc_ts = local_ts - tz_offset;

    // Compute date parts from the UTC timestamp using `Date::from_timestamp`-style
    // logic via `DateTime::from_timestamp`. We pass microseconds separately.
    let utc = DateTime::from_timestamp(utc_ts, 0).expect("RFC 2822 timestamp must be in valid range");

    // Day-of-week: 1970-01-01 (UTC, ts=0) was a Thursday (index 3 in our Mon-first array).
    // Normalize the day count to be non-negative before taking modulo to handle pre-1970 dates.
    let days_since_epoch = utc_ts.div_euclid(86_400);
    let weekday_index = (days_since_epoch + 3).rem_euclid(7) as usize;

    format!(
        "{day_name}, {day:02} {month_name} {year:04} {hour:02}:{minute:02}:{second:02} GMT",
        day_name = RFC2822_DAY_NAMES[weekday_index],
        day = utc.date.day,
        month_name = RFC2822_MONTH_NAMES[(utc.date.month as usize).saturating_sub(1)],
        year = utc.date.year,
        hour = utc.time.hour,
        minute = utc.time.minute,
        second = utc.time.second,
    )
}

fn downcast_date_reject_datetime<'a, 'py>(py_date: &'a Bound<'py, PyAny>) -> PyResult<&'a Bound<'py, PyDate>> {
    if let Ok(py_date) = py_date.cast::<PyDate>() {
        // because `datetime` is a subclass of `date` we have to check that the value is not a
        // `datetime` to avoid lossy serialization
        if !py_date.is_instance_of::<PyDateTime>() {
            return Ok(py_date);
        }
    }

    Err(PydanticSerializationUnexpectedValue::new_from_msg(None).to_py_err())
}

macro_rules! build_temporal_serializer {
    (
        $Struct:ident,
        $expected_type:literal,
        $downcast:path,
        $to_json:ident,
        $json_key_fn:ident,
        $serialize_fn:ident
    ) => {
        #[derive(Debug)]
        pub struct $Struct {
            temporal_mode: TemporalMode,
        }

        impl BuildSerializer for $Struct {
            const EXPECTED_TYPE: &'static str = $expected_type;

            fn build(
                _schema: &Bound<'_, PyDict>,
                config: Option<&Bound<'_, PyDict>>,
                _definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
            ) -> PyResult<Arc<CombinedSerializer>> {
                let temporal_mode = TemporalMode::from_config(config)?;
                Ok(Arc::new(Self { temporal_mode }.into()))
            }
        }

        impl_py_gc_traverse!($Struct {});

        impl TypeSerializer for $Struct {
            fn to_python<'py>(
                &self,
                value: &Bound<'py, PyAny>,
                state: &mut SerializationState<'py>,
            ) -> PyResult<Py<PyAny>> {
                match $downcast(value) {
                    Ok(py_value) => match state.extra.mode {
                        SerMode::Json => Ok(self.temporal_mode.$to_json(value.py(), py_value)?),
                        _ => Ok(value.clone().unbind()),
                    },
                    _ => {
                        state.warn_fallback_py(self.get_name(), value)?;
                        infer_to_python(value, state)
                    }
                }
            }

            fn json_key<'a, 'py>(
                &self,
                key: &'a Bound<'py, PyAny>,
                state: &mut SerializationState<'py>,
            ) -> PyResult<Cow<'a, str>> {
                match $downcast(key) {
                    Ok(py_value) => Ok(self.temporal_mode.$json_key_fn(py_value)?),
                    Err(_) => {
                        state.warn_fallback_py(self.get_name(), key)?;
                        infer_json_key(key, state)
                    }
                }
            }

            fn serde_serialize<'py, S: serde::ser::Serializer>(
                &self,
                value: &Bound<'py, PyAny>,
                serializer: S,
                state: &mut SerializationState<'py>,
            ) -> Result<S::Ok, S::Error> {
                match $downcast(value) {
                    Ok(py_value) => self.temporal_mode.$serialize_fn(py_value, serializer),
                    Err(_) => {
                        state.warn_fallback_ser::<S>(self.get_name(), value)?;
                        infer_serialize(value, serializer, state)
                    }
                }
            }

            fn get_name(&self) -> &str {
                Self::EXPECTED_TYPE
            }
        }
    };
}

build_temporal_serializer!(
    DatetimeSerializer,
    "datetime",
    Bound::cast::<PyDateTime>,
    datetime_to_json,
    datetime_json_key,
    datetime_serialize
);

build_temporal_serializer!(
    DateSerializer,
    "date",
    downcast_date_reject_datetime,
    date_to_json,
    date_json_key,
    date_serialize
);

build_temporal_serializer!(
    TimeSerializer,
    "time",
    Bound::cast::<PyTime>,
    time_to_json,
    time_json_key,
    time_serialize
);
