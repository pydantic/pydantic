use std::borrow::Cow;
use std::sync::Arc;

use pyo3::types::{PyBytes, PyDict};
use pyo3::{IntoPyObjectExt, prelude::*};

use crate::build_tools::LazyLock;
use crate::definitions::DefinitionsBuilder;
use crate::serializers::SerializationState;
use crate::serializers::config::{BytesMode, FromConfig};

use super::{
    BuildSerializer, CombinedSerializer, SerMode, TypeSerializer, infer_json_key, infer_serialize, infer_to_python,
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
    fn to_python<'py>(
        &self,
        value: &Bound<'py, PyAny>,
        state: &mut SerializationState<'_, 'py>,
    ) -> PyResult<Py<PyAny>> {
        let py = value.py();
        match value.cast::<PyBytes>() {
            Ok(py_bytes) => match state.extra.mode {
                SerMode::Json => self
                    .bytes_mode
                    .bytes_to_string(py, py_bytes.as_bytes())?
                    .into_py_any(py),
                _ => Ok(value.clone().unbind()),
            },
            Err(_) => {
                state.warn_fallback_py(self.get_name(), value)?;
                infer_to_python(value, state)
            }
        }
    }

    fn json_key<'a, 'py>(
        &self,
        key: &'a Bound<'py, PyAny>,
        state: &mut SerializationState<'_, 'py>,
    ) -> PyResult<Cow<'a, str>> {
        match key.cast::<PyBytes>() {
            Ok(py_bytes) => self.bytes_mode.bytes_to_string(key.py(), py_bytes.as_bytes()),
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
        state: &mut SerializationState<'_, 'py>,
    ) -> Result<S::Ok, S::Error> {
        match value.cast::<PyBytes>() {
            Ok(py_bytes) => self.bytes_mode.serialize_bytes(py_bytes.as_bytes(), serializer),
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
