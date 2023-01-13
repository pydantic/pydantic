use std::borrow::Cow;

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};

use crate::build_context::BuildContext;

use super::any::{fallback_json_key, fallback_serialize, fallback_to_python};
use super::{py_err_se_err, BuildSerializer, CombinedSerializer, Extra, IsType, ObType, SerMode, TypeSerializer};

#[derive(Debug, Clone)]
pub struct StrSerializer;

impl BuildSerializer for StrSerializer {
    const EXPECTED_TYPE: &'static str = "str";

    fn build(
        _schema: &PyDict,
        _config: Option<&PyDict>,
        _build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        Ok(Self {}.into())
    }
}

impl TypeSerializer for StrSerializer {
    fn to_python(
        &self,
        value: &PyAny,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        let py = value.py();
        match extra.ob_type_lookup.is_type(value, ObType::Str) {
            IsType::Exact => Ok(value.into_py(py)),
            IsType::Subclass => match extra.mode {
                SerMode::Json => Ok(value.extract::<&str>()?.into_py(py)),
                _ => Ok(value.into_py(py)),
            },
            IsType::False => {
                extra.warnings.fallback_slow(Self::EXPECTED_TYPE, value);
                fallback_to_python(value, include, exclude, extra)
            }
        }
    }

    fn json_key<'py>(&self, key: &'py PyAny, extra: &Extra) -> PyResult<Cow<'py, str>> {
        if let Ok(py_str) = key.cast_as::<PyString>() {
            Ok(py_str.to_string_lossy())
        } else {
            extra.warnings.fallback_slow(Self::EXPECTED_TYPE, key);
            fallback_json_key(key, extra)
        }
    }

    fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        value: &PyAny,
        serializer: S,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> Result<S::Ok, S::Error> {
        match value.cast_as::<PyString>() {
            Ok(py_str) => serialize_py_str(py_str, serializer),
            Err(_) => {
                extra.warnings.fallback_slow(Self::EXPECTED_TYPE, value);
                fallback_serialize(value, serializer, include, exclude, extra)
            }
        }
    }
}

pub fn serialize_py_str<S: serde::ser::Serializer>(py_str: &PyString, serializer: S) -> Result<S::Ok, S::Error> {
    let s = py_str.to_str().map_err(py_err_se_err)?;
    serializer.serialize_str(s)
}
