use std::borrow::Cow;

use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict};

use crate::definitions::DefinitionsBuilder;
use crate::serializers::config::{BytesMode, FromConfig};

use super::{
    infer_json_key, infer_serialize, infer_to_python, BuildSerializer, CombinedSerializer, Extra, SerMode,
    TypeSerializer,
};

#[derive(Debug)]
pub struct BytesSerializer {
    bytes_mode: BytesMode,
}

impl BuildSerializer for BytesSerializer {
    const EXPECTED_TYPE: &'static str = "bytes";

    fn build(
        _schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let bytes_mode = BytesMode::from_config(config)?;
        Ok(Self { bytes_mode }.into())
    }
}

impl_py_gc_traverse!(BytesSerializer {});

impl TypeSerializer for BytesSerializer {
    fn to_python(
        &self,
        value: &Bound<'_, PyAny>,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        let py = value.py();
        match value.downcast::<PyBytes>() {
            Ok(py_bytes) => match extra.mode {
                SerMode::Json => self
                    .bytes_mode
                    .bytes_to_string(py, py_bytes.as_bytes())
                    .map(|s| s.into_py(py)),
                _ => Ok(value.into_py(py)),
            },
            Err(_) => {
                extra.warnings.on_fallback_py(self.get_name(), value, extra)?;
                infer_to_python(value, include, exclude, extra)
            }
        }
    }

    fn json_key<'a>(&self, key: &'a Bound<'_, PyAny>, extra: &Extra) -> PyResult<Cow<'a, str>> {
        match key.downcast::<PyBytes>() {
            Ok(py_bytes) => self.bytes_mode.bytes_to_string(key.py(), py_bytes.as_bytes()),
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
        match value.downcast::<PyBytes>() {
            Ok(py_bytes) => self.bytes_mode.serialize_bytes(py_bytes.as_bytes(), serializer),
            Err(_) => {
                extra.warnings.on_fallback_ser::<S>(self.get_name(), value, extra)?;
                infer_serialize(value, serializer, include, exclude, extra)
            }
        }
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}
