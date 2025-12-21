use std::borrow::Cow;
use std::str::{FromStr, Utf8Error, from_utf8};

use base64::Engine;
use pyo3::prelude::*;
use pyo3::types::{PyDate, PyDateTime, PyDict, PyString, PyTime};
use pyo3::{IntoPyObjectExt, intern};

use serde::ser::Error;

use crate::build_tools::py_schema_err;
use crate::input::{EitherTimedelta, pydate_as_date, pydatetime_as_datetime, pytime_as_time};
use crate::serializers::type_serializers::datetime_etc::{
    date_to_milliseconds, date_to_seconds, datetime_to_milliseconds, datetime_to_seconds, time_to_milliseconds,
    time_to_seconds,
};
use crate::tools::SchemaDict;

use super::errors::py_err_se_err;

#[derive(Debug, Clone, Copy)]
#[allow(clippy::struct_field_names)]
pub(crate) struct SerializationConfig {
    pub temporal_mode: TemporalMode,
    pub bytes_mode: BytesMode,
    pub inf_nan_mode: InfNanMode,
}

impl Default for SerializationConfig {
    fn default() -> Self {
        Self {
            temporal_mode: TemporalMode::default(),
            bytes_mode: BytesMode::default(),
            inf_nan_mode: InfNanMode::Constants,
        }
    }
}

impl SerializationConfig {
    pub fn from_config(config: Option<&Bound<'_, PyDict>>) -> PyResult<Self> {
        let temporal_set = config
            .and_then(|cfg| cfg.contains(intern!(cfg.py(), "ser_json_temporal")).ok())
            .unwrap_or(false);
        let temporal_mode = if temporal_set {
            TemporalMode::from_config(config)?
        } else {
            TimedeltaMode::from_config(config)?.into()
        };
        let bytes_mode = BytesMode::from_config(config)?;
        let inf_nan_mode = InfNanMode::from_config(config)?;
        Ok(Self {
            temporal_mode,
            bytes_mode,
            inf_nan_mode,
        })
    }

    pub fn from_args(
        timedelta_mode: &str,
        temporal_mode: &str,
        bytes_mode: &str,
        inf_nan_mode: &str,
    ) -> PyResult<Self> {
        let resolved_temporal_mode = if temporal_mode != "iso8601" {
            TemporalMode::from_str(temporal_mode)?
        } else {
            TimedeltaMode::from_str(timedelta_mode)?.into()
        };
        Ok(Self {
            temporal_mode: resolved_temporal_mode,
            bytes_mode: BytesMode::from_str(bytes_mode)?,
            inf_nan_mode: InfNanMode::from_str(inf_nan_mode)?,
        })
    }
}

pub trait FromConfig {
    fn from_config(config: Option<&Bound<'_, PyDict>>) -> PyResult<Self>
    where
        Self: Sized;
}

macro_rules! serialization_mode {
    ($name:ident, $config_key:expr, $($variant:ident => $value:expr),* $(,)?) => {
        #[derive(Default, Debug, Clone, Copy, PartialEq, Eq)]
        pub enum $name {
            #[default]
            $($variant,)*
        }

        impl FromStr for $name {
            type Err = PyErr;

            fn from_str(s: &str) -> Result<Self, Self::Err> {
                match s {
                    $($value => Ok(Self::$variant),)*
                    s => py_schema_err!(
                        concat!("Invalid ", stringify!($name), " serialization mode: `{}`, expected ", $($value, " or "),*),
                        s
                    ),
                }
            }
        }

        impl FromConfig for $name {
            fn from_config(config: Option<&Bound<'_, PyDict>>) -> PyResult<Self> {
                let Some(config_dict) = config else {
                    return Ok(Self::default());
                };
                let raw_mode = config_dict.get_as::<Bound<'_, PyString>>(intern!(config_dict.py(), $config_key))?;
                raw_mode.map_or_else(|| Ok(Self::default()), |raw| Self::from_str(raw.to_str()?))
            }
        }

    };
}

serialization_mode! {
    TimedeltaMode,
    "ser_json_timedelta",
    Iso8601 => "iso8601",
    Float => "float",
}

serialization_mode! {
    TemporalMode,
    "ser_json_temporal",
    Iso8601 => "iso8601",
    Seconds => "seconds",
    Milliseconds => "milliseconds"
}

serialization_mode! {
    BytesMode,
    "ser_json_bytes",
    Utf8 => "utf8",
    Base64 => "base64",
    Hex => "hex",
}

serialization_mode! {
    InfNanMode,
    "ser_json_inf_nan",
    Null => "null",
    Constants => "constants",
    Strings => "strings",
}

impl TimedeltaMode {}

impl From<TimedeltaMode> for TemporalMode {
    fn from(value: TimedeltaMode) -> Self {
        match value {
            TimedeltaMode::Iso8601 => TemporalMode::Iso8601,
            TimedeltaMode::Float => TemporalMode::Seconds,
        }
    }
}

impl TemporalMode {
    pub fn datetime_to_json(self, py: Python, datetime: &Bound<'_, PyDateTime>) -> PyResult<Py<PyAny>> {
        let dt = pydatetime_as_datetime(datetime)?;
        match self {
            Self::Iso8601 => dt.to_string().into_py_any(py),
            Self::Seconds => datetime_to_seconds(dt).into_py_any(py),
            Self::Milliseconds => datetime_to_milliseconds(dt).into_py_any(py),
        }
    }

    pub fn date_to_json(self, py: Python, date: &Bound<'_, PyDate>) -> PyResult<Py<PyAny>> {
        let date = pydate_as_date(date)?;
        match self {
            Self::Iso8601 => date.to_string().into_py_any(py),
            Self::Seconds => date_to_seconds(date).into_py_any(py),
            Self::Milliseconds => date_to_milliseconds(date).into_py_any(py),
        }
    }

    pub fn time_to_json(self, py: Python, time: &Bound<'_, PyTime>) -> PyResult<Py<PyAny>> {
        let time = pytime_as_time(time)?;
        match self {
            Self::Iso8601 => time.to_string().into_py_any(py),
            Self::Seconds => time_to_seconds(time).into_py_any(py),
            Self::Milliseconds => time_to_milliseconds(time).into_py_any(py),
        }
    }

    pub fn timedelta_to_json(self, py: Python, either_delta: EitherTimedelta) -> PyResult<Py<PyAny>> {
        match self {
            Self::Iso8601 => {
                let d = either_delta.to_duration()?;
                d.to_string().into_py_any(py)
            }
            Self::Seconds => {
                let seconds: f64 = either_delta.total_seconds()?;
                seconds.into_py_any(py)
            }
            Self::Milliseconds => {
                let milliseconds: f64 = either_delta.total_milliseconds()?;
                milliseconds.into_py_any(py)
            }
        }
    }

    pub fn datetime_json_key<'py>(self, datetime: &Bound<'_, PyDateTime>) -> PyResult<Cow<'py, str>> {
        let dt = pydatetime_as_datetime(datetime)?;
        match self {
            Self::Iso8601 => Ok(dt.to_string().into()),
            Self::Seconds => Ok(datetime_to_seconds(dt).to_string().into()),
            Self::Milliseconds => Ok(datetime_to_milliseconds(dt).to_string().into()),
        }
    }

    pub fn date_json_key<'py>(self, date: &Bound<'_, PyDate>) -> PyResult<Cow<'py, str>> {
        let date = pydate_as_date(date)?;
        match self {
            Self::Iso8601 => Ok(date.to_string().into()),
            Self::Seconds => Ok(date_to_seconds(date).to_string().into()),
            Self::Milliseconds => Ok(date_to_milliseconds(date).to_string().into()),
        }
    }

    pub fn time_json_key<'py>(self, time: &Bound<'_, PyTime>) -> PyResult<Cow<'py, str>> {
        let time = pytime_as_time(time)?;
        match self {
            Self::Iso8601 => Ok(time.to_string().into()),
            Self::Seconds => Ok(time_to_seconds(time).to_string().into()),
            Self::Milliseconds => Ok(time_to_milliseconds(time).to_string().into()),
        }
    }

    pub fn timedelta_json_key<'py>(self, either_delta: &EitherTimedelta) -> PyResult<Cow<'py, str>> {
        match self {
            Self::Iso8601 => {
                let d = either_delta.to_duration()?;
                Ok(d.to_string().into())
            }
            Self::Seconds => {
                let seconds: f64 = either_delta.total_seconds()?;
                Ok(seconds.to_string().into())
            }
            Self::Milliseconds => {
                let milliseconds: f64 = either_delta.total_milliseconds()?;
                Ok(milliseconds.to_string().into())
            }
        }
    }

    pub fn datetime_serialize<S: serde::ser::Serializer>(
        self,
        datetime: &Bound<'_, PyDateTime>,
        serializer: S,
    ) -> Result<S::Ok, S::Error> {
        let dt = pydatetime_as_datetime(datetime).map_err(py_err_se_err)?;
        match self {
            Self::Iso8601 => serializer.collect_str(&dt),
            Self::Seconds => serializer.serialize_f64(datetime_to_seconds(dt)),
            Self::Milliseconds => serializer.serialize_f64(datetime_to_milliseconds(dt)),
        }
    }

    pub fn date_serialize<S: serde::ser::Serializer>(
        self,
        date: &Bound<'_, PyDate>,
        serializer: S,
    ) -> Result<S::Ok, S::Error> {
        let date = pydate_as_date(date).map_err(py_err_se_err)?;
        match self {
            Self::Iso8601 => serializer.collect_str(&date),
            Self::Seconds => serializer.serialize_f64(date_to_seconds(date)),
            Self::Milliseconds => serializer.serialize_f64(date_to_milliseconds(date)),
        }
    }

    pub fn time_serialize<S: serde::ser::Serializer>(
        self,
        time: &Bound<'_, PyTime>,
        serializer: S,
    ) -> Result<S::Ok, S::Error> {
        let time = pytime_as_time(time).map_err(py_err_se_err)?;
        match self {
            Self::Iso8601 => serializer.collect_str(&time),
            Self::Seconds => serializer.serialize_f64(time_to_seconds(time)),
            Self::Milliseconds => serializer.serialize_f64(time_to_milliseconds(time)),
        }
    }

    pub fn timedelta_serialize<S: serde::ser::Serializer>(
        self,
        either_delta: EitherTimedelta,
        serializer: S,
    ) -> Result<S::Ok, S::Error> {
        match self {
            Self::Iso8601 => {
                let d = either_delta.to_duration().map_err(py_err_se_err)?;
                serializer.collect_str(&d)
            }
            Self::Seconds => {
                let seconds: f64 = either_delta.total_seconds().map_err(py_err_se_err)?;
                serializer.serialize_f64(seconds)
            }
            Self::Milliseconds => {
                let milliseconds: f64 = either_delta.total_milliseconds().map_err(py_err_se_err)?;
                serializer.serialize_f64(milliseconds)
            }
        }
    }
}

impl BytesMode {
    pub fn bytes_to_string<'a>(self, py: Python, bytes: &'a [u8]) -> PyResult<Cow<'a, str>> {
        match self {
            Self::Utf8 => from_utf8(bytes)
                .map_err(|err| utf8_py_error(py, err, bytes))
                .map(Cow::Borrowed),
            Self::Base64 => Ok(Cow::Owned(base64::engine::general_purpose::URL_SAFE.encode(bytes))),
            Self::Hex => Ok(Cow::Owned(
                bytes.iter().fold(String::new(), |acc, b| acc + &format!("{b:02x}")),
            )),
        }
    }

    pub fn serialize_bytes<S: serde::ser::Serializer>(self, bytes: &[u8], serializer: S) -> Result<S::Ok, S::Error> {
        match self {
            Self::Utf8 => match from_utf8(bytes) {
                Ok(s) => serializer.serialize_str(s),
                Err(e) => Err(Error::custom(e.to_string())),
            },
            Self::Base64 => serializer.serialize_str(&base64::engine::general_purpose::URL_SAFE.encode(bytes)),
            Self::Hex => serializer.serialize_str(hex::encode(bytes).as_str()),
        }
    }
}

pub fn utf8_py_error(py: Python, err: Utf8Error, data: &[u8]) -> PyErr {
    match pyo3::exceptions::PyUnicodeDecodeError::new_utf8(py, data, err) {
        Ok(decode_err) => PyErr::from_value(decode_err.into_any()),
        Err(err) => err,
    }
}

impl FromPyObject<'_, '_> for InfNanMode {
    type Error = PyErr;
    fn extract(ob: Borrowed<'_, '_, PyAny>) -> PyResult<Self> {
        Self::from_str(ob.cast::<PyString>()?.to_str()?)
    }
}
