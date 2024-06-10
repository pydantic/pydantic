use std::borrow::Cow;
use std::str::{from_utf8, FromStr, Utf8Error};

use base64::Engine;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDelta, PyDict, PyString};

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
        pub(crate) enum $name {
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
                raw_mode.map_or_else(|| Ok(Self::default()), |raw| Self::from_str(&raw.to_cow()?))
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
    fn total_seconds<'py>(py_timedelta: &Bound<'py, PyDelta>) -> PyResult<Bound<'py, PyAny>> {
        py_timedelta.call_method0(intern!(py_timedelta.py(), "total_seconds"))
    }

    pub fn either_delta_to_json(self, py: Python, either_delta: &EitherTimedelta) -> PyResult<PyObject> {
        match self {
            Self::Iso8601 => {
                let d = either_delta.to_duration()?;
                Ok(d.to_string().into_py(py))
            }
            Self::Float => {
                // convert to int via a py timedelta not duration since we know this this case the input would have
                // been a py timedelta
                let py_timedelta = either_delta.try_into_py(py)?;
                let seconds = Self::total_seconds(&py_timedelta)?;
                Ok(seconds.into_py(py))
            }
        }
    }

    pub fn json_key<'py>(self, py: Python, either_delta: &EitherTimedelta) -> PyResult<Cow<'py, str>> {
        match self {
            Self::Iso8601 => {
                let d = either_delta.to_duration()?;
                Ok(d.to_string().into())
            }
            Self::Float => {
                let py_timedelta = either_delta.try_into_py(py)?;
                let seconds: f64 = Self::total_seconds(&py_timedelta)?.extract()?;
                Ok(seconds.to_string().into())
            }
        }
    }

    pub fn timedelta_serialize<S: serde::ser::Serializer>(
        self,
        py: Python,
        either_delta: &EitherTimedelta,
        serializer: S,
    ) -> Result<S::Ok, S::Error> {
        match self {
            Self::Iso8601 => {
                let d = either_delta.to_duration().map_err(py_err_se_err)?;
                serializer.serialize_str(&d.to_string())
            }
            Self::Float => {
                let py_timedelta = either_delta.try_into_py(py).map_err(py_err_se_err)?;
                let seconds = Self::total_seconds(&py_timedelta).map_err(py_err_se_err)?;
                let seconds: f64 = seconds.extract().map_err(py_err_se_err)?;
                serializer.serialize_f64(seconds)
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
            Self::Hex => {
                serializer.serialize_str(&bytes.iter().fold(String::new(), |acc, b| acc + &format!("{b:02x}")))
            }
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
