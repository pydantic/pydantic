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
