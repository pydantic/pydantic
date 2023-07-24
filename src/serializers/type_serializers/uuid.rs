use std::borrow::Cow;

use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::definitions::DefinitionsBuilder;

use super::{
    infer_json_key, infer_serialize, infer_to_python, py_err_se_err, BuildSerializer, CombinedSerializer, Extra,
    IsType, ObType, SerMode, TypeSerializer,
};

pub(crate) fn uuid_to_string(py_uuid: &PyAny) -> PyResult<String> {
    Ok(py_uuid.str()?.to_string())
}

#[derive(Debug, Clone)]
pub struct UuidSerializer;

impl_py_gc_traverse!(UuidSerializer {});

impl BuildSerializer for UuidSerializer {
    const EXPECTED_TYPE: &'static str = "uuid";

    fn build(
        _schema: &PyDict,
        _config: Option<&PyDict>,
        _definitions: &mut DefinitionsBuilder<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        Ok(Self {}.into())
    }
}

impl TypeSerializer for UuidSerializer {
    fn to_python(
        &self,
        value: &PyAny,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        let py = value.py();
        match extra.ob_type_lookup.is_type(value, ObType::Uuid) {
            IsType::Exact | IsType::Subclass => match extra.mode {
                SerMode::Json => Ok(uuid_to_string(value)?.into_py(py)),
                _ => Ok(value.into_py(py)),
            },
            IsType::False => {
                extra.warnings.on_fallback_py(self.get_name(), value, extra)?;
                infer_to_python(value, include, exclude, extra)
            }
        }
    }

    fn json_key<'py>(&self, key: &'py PyAny, extra: &Extra) -> PyResult<Cow<'py, str>> {
        match extra.ob_type_lookup.is_type(key, ObType::Uuid) {
            IsType::Exact | IsType::Subclass => {
                let str = uuid_to_string(key)?;
                Ok(Cow::Owned(str))
            }
            IsType::False => {
                extra.warnings.on_fallback_py(self.get_name(), key, extra)?;
                infer_json_key(key, extra)
            }
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
        match extra.ob_type_lookup.is_type(value, ObType::Uuid) {
            IsType::Exact | IsType::Subclass => {
                let s = uuid_to_string(value).map_err(py_err_se_err)?;
                serializer.serialize_str(&s)
            }
            IsType::False => {
                extra.warnings.on_fallback_ser::<S>(self.get_name(), value, extra)?;
                infer_serialize(value, serializer, include, exclude, extra)
            }
        }
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}
