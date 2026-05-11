use std::borrow::Cow;
use std::sync::Arc;

use pyo3::intern;
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

/// Format a Python `datetime` as an RFC 2822 date string with `GMT` as the zone label,
/// e.g. `"Mon, 01 Jan 2024 12:00:00 GMT"`.
///
/// Delegates to Python's [`email.utils.format_datetime(dt, usegmt=True)`](https://docs.python.org/3/library/email.utils.html#email.utils.format_datetime).
/// The datetime is normalised to UTC first:
/// - naive datetimes are assumed to be UTC and have their `tzinfo` set to UTC,
/// - aware datetimes are converted to UTC via `astimezone()`.
pub(crate) fn datetime_to_rfc2822<'py>(py: Python<'py>, datetime: &Bound<'py, PyDateTime>) -> PyResult<String> {
    let datetime_module = py.import(intern!(py, "datetime"))?;
    let timezone_utc = datetime_module
        .getattr(intern!(py, "timezone"))?
        .getattr(intern!(py, "utc"))?;

    let utc_datetime = if datetime.getattr(intern!(py, "tzinfo"))?.is_none() {
        // Naive datetime: assume it represents UTC, attach `tzinfo=timezone.utc`.
        let replace_kwargs = PyDict::new(py);
        replace_kwargs.set_item(intern!(py, "tzinfo"), &timezone_utc)?;
        datetime.call_method(intern!(py, "replace"), (), Some(&replace_kwargs))?
    } else {
        // Aware datetime: convert to UTC.
        datetime.call_method1(intern!(py, "astimezone"), (&timezone_utc,))?
    };

    let format_kwargs = PyDict::new(py);
    format_kwargs.set_item(intern!(py, "usegmt"), true)?;
    py.import(intern!(py, "email.utils"))?
        .call_method(intern!(py, "format_datetime"), (utc_datetime,), Some(&format_kwargs))?
        .extract()
}

/// Format a Python `date` as an RFC 2822 date string at midnight UTC,
/// e.g. `"Mon, 01 Jan 2024 00:00:00 GMT"`.
///
/// Combines the bare `date` with midnight in UTC and then delegates to Python's
/// [`email.utils.format_datetime(dt, usegmt=True)`](https://docs.python.org/3/library/email.utils.html#email.utils.format_datetime).
pub(crate) fn date_to_rfc2822<'py>(py: Python<'py>, date: &Bound<'py, PyDate>) -> PyResult<String> {
    let datetime_module = py.import(intern!(py, "datetime"))?;
    let datetime_cls = datetime_module.getattr(intern!(py, "datetime"))?;
    let midnight = datetime_module.getattr(intern!(py, "time"))?.call0()?;
    let timezone_utc = datetime_module
        .getattr(intern!(py, "timezone"))?
        .getattr(intern!(py, "utc"))?;

    let combine_kwargs = PyDict::new(py);
    combine_kwargs.set_item(intern!(py, "tzinfo"), &timezone_utc)?;
    let utc_datetime = datetime_cls.call_method(intern!(py, "combine"), (date, midnight), Some(&combine_kwargs))?;

    let kwargs = PyDict::new(py);
    kwargs.set_item(intern!(py, "usegmt"), true)?;
    py.import(intern!(py, "email.utils"))?
        .call_method(intern!(py, "format_datetime"), (utc_datetime,), Some(&kwargs))?
        .extract()
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
