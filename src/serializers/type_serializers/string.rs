use std::borrow::Cow;
use std::sync::Arc;

use pyo3::types::{PyDict, PyString};
use pyo3::{prelude::*, IntoPyObjectExt};

use crate::build_tools::LazyLock;
use crate::definitions::DefinitionsBuilder;
use crate::serializers::SerializationState;

use super::{
    infer_json_key, infer_serialize, infer_to_python, py_err_se_err, BuildSerializer, CombinedSerializer, IsType,
    ObType, SerMode, TypeSerializer,
};

#[derive(Debug)]
pub struct StrSerializer;

static STR_SERIALIZER: LazyLock<Arc<CombinedSerializer>> = LazyLock::new(|| Arc::new(StrSerializer.into()));

impl StrSerializer {
    pub fn get() -> &'static Arc<CombinedSerializer> {
        &STR_SERIALIZER
    }
}

impl BuildSerializer for StrSerializer {
    const EXPECTED_TYPE: &'static str = "str";

    fn build(
        _schema: &Bound<'_, PyDict>,
        _config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        Ok(Self::get().clone())
    }
}

impl_py_gc_traverse!(StrSerializer {});

impl TypeSerializer for StrSerializer {
    fn to_python<'py>(
        &self,
        value: &Bound<'py, PyAny>,
        state: &mut SerializationState<'_, 'py>,
    ) -> PyResult<Py<PyAny>> {
        let py = value.py();
        match state.extra.ob_type_lookup.is_type(value, ObType::Str) {
            IsType::Exact => Ok(value.clone().unbind()),
            IsType::Subclass => match state.extra.mode {
                SerMode::Json => value.downcast::<PyString>()?.to_str()?.into_py_any(py),
                _ => Ok(value.clone().unbind()),
            },
            IsType::False => {
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
        if let Ok(py_str) = key.downcast::<PyString>() {
            // FIXME py cow to avoid the copy
            Ok(Cow::Owned(py_str.to_string_lossy().into_owned()))
        } else {
            state.warn_fallback_py(self.get_name(), key)?;
            infer_json_key(key, state)
        }
    }

    fn serde_serialize<'py, S: serde::ser::Serializer>(
        &self,
        value: &Bound<'py, PyAny>,
        serializer: S,
        state: &mut SerializationState<'_, 'py>,
    ) -> Result<S::Ok, S::Error> {
        match value.downcast::<PyString>() {
            Ok(py_str) => serialize_py_str(py_str, serializer),
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

pub fn serialize_py_str<S: serde::ser::Serializer>(
    py_str: &Bound<'_, PyString>,
    serializer: S,
) -> Result<S::Ok, S::Error> {
    let s = py_str.to_str().map_err(py_err_se_err)?;
    serializer.serialize_str(s)
}
