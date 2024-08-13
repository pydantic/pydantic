use std::{
    borrow::Cow,
    sync::{Arc, OnceLock},
};

use pyo3::prelude::*;
use pyo3::types::PyDict;

use serde::ser::Serializer;

use crate::definitions::DefinitionsBuilder;

use super::{
    infer_json_key, infer_serialize, infer_to_python, BuildSerializer, CombinedSerializer, Extra, TypeSerializer,
};

#[derive(Debug, Clone, Default)]
pub struct AnySerializer;

impl AnySerializer {
    pub fn get() -> &'static Arc<CombinedSerializer> {
        static ANY_SERIALIZER: OnceLock<Arc<CombinedSerializer>> = OnceLock::new();
        ANY_SERIALIZER.get_or_init(|| Arc::new(Self.into()))
    }
}

impl BuildSerializer for AnySerializer {
    const EXPECTED_TYPE: &'static str = "any";

    fn build(
        _schema: &Bound<'_, PyDict>,
        _config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        Ok(Self {}.into())
    }
}

impl_py_gc_traverse!(AnySerializer {});

impl TypeSerializer for AnySerializer {
    fn to_python(
        &self,
        value: &Bound<'_, PyAny>,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        infer_to_python(value, include, exclude, extra)
    }

    fn json_key<'a>(&self, key: &'a Bound<'_, PyAny>, extra: &Extra) -> PyResult<Cow<'a, str>> {
        infer_json_key(key, extra)
    }

    fn serde_serialize<S: Serializer>(
        &self,
        value: &Bound<'_, PyAny>,
        serializer: S,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> Result<S::Ok, S::Error> {
        infer_serialize(value, serializer, include, exclude, extra)
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}
