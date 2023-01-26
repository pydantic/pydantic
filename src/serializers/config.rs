use std::borrow::Cow;
use std::str::{from_utf8, Utf8Error};

use pyo3::prelude::*;
use pyo3::types::{PyDelta, PyDict};
use pyo3::{intern, PyNativeType};

use serde::ser::Error;

use crate::build_tools::{py_err, SchemaDict};
use crate::input::pytimedelta_as_duration;

use super::errors::py_err_se_err;

#[derive(Debug, Clone)]
pub(crate) struct SerializationConfig {
    pub timedelta_mode: TimedeltaMode,
    pub bytes_mode: BytesMode,
}

impl SerializationConfig {
    pub fn from_config(config: Option<&PyDict>) -> PyResult<Self> {
        let timedelta_mode = TimedeltaMode::from_config(config)?;
        let bytes_mode = BytesMode::from_config(config)?;
        Ok(Self {
            timedelta_mode,
            bytes_mode,
        })
    }

    pub fn from_args(timedelta_mode: Option<&str>, bytes_mode: Option<&str>) -> PyResult<Self> {
        let timedelta_mode = TimedeltaMode::from_str(timedelta_mode)?;
        let bytes_mode = BytesMode::from_str(bytes_mode)?;
        Ok(Self {
            timedelta_mode,
            bytes_mode,
        })
    }
}

#[derive(Debug, Clone)]
pub(crate) enum TimedeltaMode {
    Iso8601,
    Float,
}

impl TimedeltaMode {
    pub fn from_config(config: Option<&PyDict>) -> PyResult<Self> {
        let raw_mode: Option<&str> = match config {
            Some(c) => c.get_as::<&str>(intern!(c.py(), "ser_json_timedelta"))?,
            None => None,
        };
        Self::from_str(raw_mode)
    }

    pub fn from_str(s: Option<&str>) -> PyResult<Self> {
        match s {
            Some("iso8601") => Ok(Self::Iso8601),
            Some("float") => Ok(Self::Float),
            Some(s) => py_err!(
                "Invalid timedelta serialization mode: `{}`, expected `iso8601` or `float`",
                s
            ),
            None => Ok(Self::Iso8601),
        }
    }

    fn total_seconds(py_timedelta: &PyDelta) -> PyResult<&PyAny> {
        py_timedelta.call_method0(intern!(py_timedelta.py(), "total_seconds"))
    }

    pub fn timedelta_to_json(&self, py_timedelta: &PyDelta) -> PyResult<PyObject> {
        let py = py_timedelta.py();
        match self {
            Self::Iso8601 => {
                let d = pytimedelta_as_duration(py_timedelta);
                Ok(d.to_string().into_py(py))
            }
            Self::Float => {
                let seconds = Self::total_seconds(py_timedelta)?;
                Ok(seconds.into_py(py))
            }
        }
    }

    pub fn json_key<'py>(&self, py_timedelta: &PyDelta) -> PyResult<Cow<'py, str>> {
        match self {
            Self::Iso8601 => {
                let d = pytimedelta_as_duration(py_timedelta);
                Ok(d.to_string().into())
            }
            Self::Float => {
                let seconds: f64 = Self::total_seconds(py_timedelta)?.extract()?;
                Ok(seconds.to_string().into())
            }
        }
    }

    pub fn timedelta_serialize<S: serde::ser::Serializer>(
        &self,
        py_timedelta: &PyDelta,
        serializer: S,
    ) -> Result<S::Ok, S::Error> {
        match self {
            Self::Iso8601 => {
                let d = pytimedelta_as_duration(py_timedelta);
                serializer.serialize_str(&d.to_string())
            }
            Self::Float => {
                let seconds = Self::total_seconds(py_timedelta).map_err(py_err_se_err)?;
                let seconds: f64 = seconds.extract().map_err(py_err_se_err)?;
                serializer.serialize_f64(seconds)
            }
        }
    }
}

#[derive(Debug, Clone)]
pub(crate) struct BytesMode {
    base64_config: Option<base64::Config>,
}

impl BytesMode {
    pub fn from_config(config: Option<&PyDict>) -> PyResult<Self> {
        let raw_mode: Option<&str> = match config {
            Some(c) => c.get_as::<&str>(intern!(c.py(), "ser_json_bytes"))?,
            None => None,
        };
        Self::from_str(raw_mode)
    }

    pub fn from_str(s: Option<&str>) -> PyResult<Self> {
        let base64_config = match s {
            Some("utf8") => None,
            Some("base64") => Some(base64::Config::new(base64::CharacterSet::UrlSafe, true)),
            Some(s) => return py_err!("Invalid bytes serialization mode: `{}`, expected `utf8` or `base64`", s),
            None => None,
        };
        Ok(Self { base64_config })
    }

    pub fn bytes_to_string<'py>(&self, py: Python, bytes: &'py [u8]) -> PyResult<Cow<'py, str>> {
        if let Some(config) = self.base64_config {
            Ok(Cow::Owned(base64::encode_config(bytes, config)))
        } else {
            from_utf8(bytes)
                .map_err(|err| utf8_py_error(py, err, bytes))
                .map(Cow::Borrowed)
        }
    }

    pub fn serialize_bytes<S: serde::ser::Serializer>(&self, bytes: &[u8], serializer: S) -> Result<S::Ok, S::Error> {
        if let Some(config) = self.base64_config {
            serializer.serialize_str(&base64::encode_config(bytes, config))
        } else {
            match from_utf8(bytes) {
                Ok(s) => serializer.serialize_str(s),
                Err(e) => Err(Error::custom(e.to_string())),
            }
        }
    }
}

pub fn utf8_py_error(py: Python, err: Utf8Error, data: &[u8]) -> PyErr {
    match pyo3::exceptions::PyUnicodeDecodeError::new_utf8(py, data, err) {
        Ok(decode_err) => PyErr::from_value(decode_err),
        Err(err) => err,
    }
}
