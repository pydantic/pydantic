use std::borrow::Cow;
use std::sync::Arc;

use pyo3::types::{PyDict, PyString};
use pyo3::{prelude::*, IntoPyObjectExt};

use crate::build_tools::LazyLock;
use crate::definitions::DefinitionsBuilder;

use super::{
    infer_json_key, infer_serialize, infer_to_python, py_err_se_err, BuildSerializer, CombinedSerializer, Extra,
    IsType, ObType, SerMode, TypeSerializer,
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
    fn to_python(
        &self,
        value: &Bound<'_, PyAny>,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> PyResult<Py<PyAny>> {
        let py = value.py();
        match extra.ob_type_lookup.is_type(value, ObType::Str) {
            IsType::Exact => Ok(value.clone().unbind()),
            IsType::Subclass => match extra.mode {
                SerMode::Json => value.downcast::<PyString>()?.to_str()?.into_py_any(py),
                _ => Ok(value.clone().unbind()),
            },
            IsType::False => {
                extra.warnings.on_fallback_py(self.get_name(), value, extra)?;
                infer_to_python(value, include, exclude, extra)
            }
        }
    }

    fn json_key<'a>(&self, key: &'a Bound<'_, PyAny>, extra: &Extra) -> PyResult<Cow<'a, str>> {
        if let Ok(py_str) = key.downcast::<PyString>() {
            // FIXME py cow to avoid the copy
            Ok(Cow::Owned(py_str.to_string_lossy().into_owned()))
        } else {
            extra.warnings.on_fallback_py(self.get_name(), key, extra)?;
            infer_json_key(key, extra)
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
        match value.downcast::<PyString>() {
            Ok(py_str) => serialize_py_str(py_str, serializer),
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

pub fn serialize_py_str<S: serde::ser::Serializer>(
    py_str: &Bound<'_, PyString>,
    serializer: S,
) -> Result<S::Ok, S::Error> {
    let s = py_str.to_str().map_err(py_err_se_err)?;
    serializer.serialize_str(s)
}
