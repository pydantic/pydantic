use std::borrow::Cow;

use pyo3::prelude::*;
use pyo3::types::{PyDate, PyDateTime, PyDict, PyTime};

use super::{
    infer_json_key, infer_serialize, infer_to_python, BuildSerializer, CombinedSerializer, Extra, SerMode,
    TypeSerializer,
};
use crate::definitions::DefinitionsBuilder;
use crate::input::{pydate_as_date, pydatetime_as_datetime, pytime_as_time};
use crate::serializers::config::{FromConfig, TemporalMode};
use crate::PydanticSerializationUnexpectedValue;

pub(crate) fn datetime_to_string(py_dt: &Bound<'_, PyDateTime>) -> PyResult<String> {
    pydatetime_as_datetime(py_dt).map(|dt| dt.to_string())
}

pub(crate) fn datetime_to_seconds(py_dt: &Bound<'_, PyDateTime>) -> PyResult<f64> {
    pydatetime_as_datetime(py_dt).map(|dt| {
        dt.date.timestamp() as f64
            + f64::from(dt.time.hour) * 3600.0
            + f64::from(dt.time.minute) * 60.0
            + f64::from(dt.time.second)
            + f64::from(dt.time.microsecond) / 1_000_000.0
    })
}

pub(crate) fn datetime_to_milliseconds(py_dt: &Bound<'_, PyDateTime>) -> PyResult<f64> {
    pydatetime_as_datetime(py_dt).map(|dt| {
        dt.date.timestamp_ms() as f64
            + f64::from(dt.time.hour) * 3_600_000.0
            + f64::from(dt.time.minute) * 60_000.0
            + f64::from(dt.time.second) * 1_000.0
            + f64::from(dt.time.microsecond) / 1_000.0
    })
}

pub(crate) fn date_to_seconds(py_date: &Bound<'_, PyDate>) -> PyResult<f64> {
    pydate_as_date(py_date).map(|dt| dt.timestamp() as f64)
}
pub(crate) fn date_to_milliseconds(py_date: &Bound<'_, PyDate>) -> PyResult<f64> {
    pydate_as_date(py_date).map(|dt| dt.timestamp_ms() as f64)
}

pub(crate) fn date_to_string(py_date: &Bound<'_, PyDate>) -> PyResult<String> {
    pydate_as_date(py_date).map(|dt| dt.to_string())
}

pub(crate) fn time_to_string(py_time: &Bound<'_, PyTime>) -> PyResult<String> {
    pytime_as_time(py_time, None).map(|dt| dt.to_string())
}

pub(crate) fn time_to_seconds(py_time: &Bound<'_, PyTime>) -> PyResult<f64> {
    pytime_as_time(py_time, None).map(|t| {
        f64::from(t.hour) * 3600.0
            + f64::from(t.minute) * 60.0
            + f64::from(t.second)
            + f64::from(t.microsecond) / 1_000_000.0
    })
}

pub(crate) fn time_to_milliseconds(py_time: &Bound<'_, PyTime>) -> PyResult<f64> {
    pytime_as_time(py_time, None).map(|t| {
        f64::from(t.hour) * 3_600_000.0
            + f64::from(t.minute) * 60_000.0
            + f64::from(t.second) * 1_000.0
            + f64::from(t.microsecond) / 1_000.0
    })
}

fn downcast_date_reject_datetime<'a, 'py>(py_date: &'a Bound<'py, PyAny>) -> PyResult<&'a Bound<'py, PyDate>> {
    if let Ok(py_date) = py_date.downcast::<PyDate>() {
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
                _definitions: &mut DefinitionsBuilder<CombinedSerializer>,
            ) -> PyResult<CombinedSerializer> {
                let temporal_mode = TemporalMode::from_config(config)?;
                Ok(Self { temporal_mode }.into())
            }
        }

        impl_py_gc_traverse!($Struct {});

        impl TypeSerializer for $Struct {
            fn to_python(
                &self,
                value: &Bound<'_, PyAny>,
                include: Option<&Bound<'_, PyAny>>,
                exclude: Option<&Bound<'_, PyAny>>,
                extra: &Extra,
            ) -> PyResult<PyObject> {
                match extra.mode {
                    SerMode::Json => match $downcast(value) {
                        Ok(py_value) => Ok(self.temporal_mode.$to_json(value.py(), py_value)?),
                        Err(_) => {
                            extra.warnings.on_fallback_py(self.get_name(), value, extra)?;
                            infer_to_python(value, include, exclude, extra)
                        }
                    },
                    _ => infer_to_python(value, include, exclude, extra),
                }
            }

            fn json_key<'a>(&self, key: &'a Bound<'_, PyAny>, extra: &Extra) -> PyResult<Cow<'a, str>> {
                match $downcast(key) {
                    Ok(py_value) => Ok(self.temporal_mode.$json_key_fn(py_value)?),
                    Err(_) => {
                        extra.warnings.on_fallback_py(self.get_name(), key, extra)?;
                        infer_json_key(key, extra)
                    }
                }
            }

            fn serde_serialize<S: serde::ser::Serializer>(
                &self,
                value: &Bound<'_, PyAny>,
                serializer: S,
                include: Option<&Bound<'_, PyAny>>,
                exclude: Option<&Bound<'_, PyAny>>,
                extra: &Extra,
            ) -> Result<S::Ok, S::Error> {
                match $downcast(value) {
                    Ok(py_value) => self.temporal_mode.$serialize_fn(py_value, serializer),
                    Err(_) => {
                        extra
                            .warnings
                            .on_fallback_ser::<S>(self.get_name(), value, extra)?;
                        infer_serialize(value, serializer, include, exclude, extra)
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
    PyAnyMethods::downcast::<PyDateTime>,
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
    PyAnyMethods::downcast::<PyTime>,
    time_to_json,
    time_json_key,
    time_serialize
);
