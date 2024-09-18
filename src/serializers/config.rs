use std::borrow::Cow;
use std::str::{from_utf8, FromStr, Utf8Error};

use base64::Engine;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};

use serde::ser::Error;

use crate::build_tools::py_schema_err;
use crate::input::EitherTimedelta;
use crate::tools::SchemaDict;

use super::errors::py_err_se_err;

#[derive(Debug, Clone)]
#[allow(clippy::struct_field_names)]
pub(crate) struct SerializationConfig {
    pub timedelta_mode: TimedeltaMode,
    pub bytes_mode: BytesMode,
    pub inf_nan_mode: InfNanMode,
}

impl SerializationConfig {
    pub fn from_config(config: Option<&Bound<'_, PyDict>>) -> PyResult<Self> {
        let timedelta_mode = TimedeltaMode::from_config(config)?;
        let bytes_mode = BytesMode::from_config(config)?;
        let inf_nan_mode = InfNanMode::from_config(config)?;
        Ok(Self {
            timedelta_mode,
            bytes_mode,
            inf_nan_mode,
        })
    }

    pub fn from_args(timedelta_mode: &str, bytes_mode: &str, inf_nan_mode: &str) -> PyResult<Self> {
        Ok(Self {
            timedelta_mode: TimedeltaMode::from_str(timedelta_mode)?,
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
    SecondsFloat => "seconds_float",
    MillisecondsFloat => "milliseconds_float"
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

impl TimedeltaMode {
    pub fn either_delta_to_json(self, py: Python, either_delta: &EitherTimedelta) -> PyResult<PyObject> {
        match self {
            Self::Iso8601 => {
                let d = either_delta.to_duration()?;
                Ok(d.to_string().into_py(py))
            }
            Self::SecondsFloat => {
                let seconds: f64 = either_delta.total_seconds()?;
                Ok(seconds.into_py(py))
            }
            Self::MillisecondsFloat => {
                let milliseconds: f64 = either_delta.total_milliseconds()?;
                Ok(milliseconds.into_py(py))
            }
        }
    }

    pub fn json_key<'py>(self, either_delta: &EitherTimedelta) -> PyResult<Cow<'py, str>> {
        match self {
            Self::Iso8601 => {
                let d = either_delta.to_duration()?;
                Ok(d.to_string().into())
            }
            Self::SecondsFloat => {
                let seconds: f64 = either_delta.total_seconds()?;
                Ok(seconds.to_string().into())
            }
            Self::MillisecondsFloat => {
                let milliseconds: f64 = either_delta.total_milliseconds()?;
                Ok(milliseconds.to_string().into())
            }
        }
    }

    pub fn timedelta_serialize<S: serde::ser::Serializer>(
        self,
        either_delta: &EitherTimedelta,
        serializer: S,
    ) -> Result<S::Ok, S::Error> {
        match self {
            Self::Iso8601 => {
                let d = either_delta.to_duration().map_err(py_err_se_err)?;
                serializer.serialize_str(&d.to_string())
            }
            Self::SecondsFloat => {
                let seconds: f64 = either_delta.total_seconds().map_err(py_err_se_err)?;
                serializer.serialize_f64(seconds)
            }
            Self::MillisecondsFloat => {
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
    match pyo3::exceptions::PyUnicodeDecodeError::new_utf8_bound(py, data, err) {
        Ok(decode_err) => PyErr::from_value_bound(decode_err.into_any()),
        Err(err) => err,
    }
}

impl FromPyObject<'_> for InfNanMode {
    fn extract_bound(ob: &Bound<'_, PyAny>) -> PyResult<Self> {
        Self::from_str(ob.downcast::<PyString>()?.to_str()?)
    }
}
