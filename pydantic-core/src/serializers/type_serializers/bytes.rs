use std::borrow::Cow;
use std::sync::Arc;

use pyo3::types::{PyBytes, PyDict};
use pyo3::{prelude::*, IntoPyObjectExt};

use crate::build_tools::LazyLock;
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

static BYTES_SERIALIZER_UTF8: LazyLock<Arc<CombinedSerializer>> = LazyLock::new(|| {
    Arc::new(
        BytesSerializer {
            bytes_mode: BytesMode::Utf8,
        }
        .into(),
    )
});

static BYTES_SERIALIZER_BASE64: LazyLock<Arc<CombinedSerializer>> = LazyLock::new(|| {
    Arc::new(
        BytesSerializer {
            bytes_mode: BytesMode::Base64,
        }
        .into(),
    )
});

static BYTES_SERIALIZER_HEX: LazyLock<Arc<CombinedSerializer>> = LazyLock::new(|| {
    Arc::new(
        BytesSerializer {
            bytes_mode: BytesMode::Hex,
        }
        .into(),
    )
});

impl BuildSerializer for BytesSerializer {
    const EXPECTED_TYPE: &'static str = "bytes";

    fn build(
        _schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        let bytes_mode = BytesMode::from_config(config)?;
        match bytes_mode {
            BytesMode::Utf8 => Ok(BYTES_SERIALIZER_UTF8.clone()),
            BytesMode::Base64 => Ok(BYTES_SERIALIZER_BASE64.clone()),
            BytesMode::Hex => Ok(BYTES_SERIALIZER_HEX.clone()),
        }
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
    ) -> PyResult<Py<PyAny>> {
        let py = value.py();
        match value.downcast::<PyBytes>() {
            Ok(py_bytes) => match extra.mode {
                SerMode::Json => self
                    .bytes_mode
                    .bytes_to_string(py, py_bytes.as_bytes())?
                    .into_py_any(py),
                _ => Ok(value.clone().unbind()),
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
