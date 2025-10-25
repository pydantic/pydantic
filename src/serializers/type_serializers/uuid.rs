use std::borrow::Cow;
use std::sync::Arc;

use pyo3::types::PyDict;
use pyo3::{intern, prelude::*, IntoPyObjectExt};
use uuid::Uuid;

use crate::build_tools::LazyLock;
use crate::definitions::DefinitionsBuilder;
use crate::serializers::SerializationState;

use super::{
    infer_json_key, infer_serialize, infer_to_python, py_err_se_err, BuildSerializer, CombinedSerializer, Extra,
    IsType, ObType, SerMode, TypeSerializer,
};

pub(crate) fn uuid_to_string(py_uuid: &Bound<'_, PyAny>) -> PyResult<String> {
    let py = py_uuid.py();
    let uuid_int_val: u128 = py_uuid.getattr(intern!(py, "int"))?.extract()?;
    let uuid = Uuid::from_u128(uuid_int_val);
    Ok(uuid.to_string())
}

#[derive(Debug)]
pub struct UuidSerializer;

static UUID_SERIALIZER: LazyLock<Arc<CombinedSerializer>> =
    LazyLock::new(|| Arc::new(CombinedSerializer::from(UuidSerializer {})));

impl_py_gc_traverse!(UuidSerializer {});

impl BuildSerializer for UuidSerializer {
    const EXPECTED_TYPE: &'static str = "uuid";

    fn build(
        _schema: &Bound<'_, PyDict>,
        _config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        Ok(UUID_SERIALIZER.clone())
    }
}

impl TypeSerializer for UuidSerializer {
    fn to_python<'py>(
        &self,
        value: &Bound<'py, PyAny>,
        include: Option<&Bound<'py, PyAny>>,
        exclude: Option<&Bound<'py, PyAny>>,
        state: &mut SerializationState<'py>,
        extra: &Extra<'_, 'py>,
    ) -> PyResult<Py<PyAny>> {
        let py = value.py();
        match extra.ob_type_lookup.is_type(value, ObType::Uuid) {
            IsType::Exact | IsType::Subclass => match extra.mode {
                SerMode::Json => uuid_to_string(value)?.into_py_any(py),
                _ => Ok(value.clone().unbind()),
            },
            IsType::False => {
                state.warn_fallback_py(self.get_name(), value, extra)?;
                infer_to_python(value, include, exclude, state, extra)
            }
        }
    }

    fn json_key<'a, 'py>(
        &self,
        key: &'a Bound<'py, PyAny>,
        state: &mut SerializationState<'py>,
        extra: &Extra<'_, 'py>,
    ) -> PyResult<Cow<'a, str>> {
        match extra.ob_type_lookup.is_type(key, ObType::Uuid) {
            IsType::Exact | IsType::Subclass => {
                let str = uuid_to_string(key)?;
                Ok(Cow::Owned(str))
            }
            IsType::False => {
                state.warn_fallback_py(self.get_name(), key, extra)?;
                infer_json_key(key, state, extra)
            }
        }
    }

    fn serde_serialize<'py, S: serde::ser::Serializer>(
        &self,
        value: &Bound<'py, PyAny>,
        serializer: S,
        include: Option<&Bound<'py, PyAny>>,
        exclude: Option<&Bound<'py, PyAny>>,
        state: &mut SerializationState<'py>,
        extra: &Extra<'_, 'py>,
    ) -> Result<S::Ok, S::Error> {
        match extra.ob_type_lookup.is_type(value, ObType::Uuid) {
            IsType::Exact | IsType::Subclass => {
                let s = uuid_to_string(value).map_err(py_err_se_err)?;
                serializer.serialize_str(&s)
            }
            IsType::False => {
                state.warn_fallback_ser::<S>(self.get_name(), value, extra)?;
                infer_serialize(value, serializer, include, exclude, state, extra)
            }
        }
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}
