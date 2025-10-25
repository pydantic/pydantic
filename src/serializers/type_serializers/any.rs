use std::{
    borrow::Cow,
    sync::{Arc, OnceLock},
};

use pyo3::prelude::*;
use pyo3::types::PyDict;

use serde::ser::Serializer;

use crate::{definitions::DefinitionsBuilder, serializers::SerializationState};

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
        _definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        Ok(Self::get().clone())
    }
}

impl_py_gc_traverse!(AnySerializer {});

impl TypeSerializer for AnySerializer {
    fn to_python<'py>(
        &self,
        value: &Bound<'py, PyAny>,
        include: Option<&Bound<'py, PyAny>>,
        exclude: Option<&Bound<'py, PyAny>>,
        state: &mut SerializationState<'py>,
        extra: &Extra<'_, 'py>,
    ) -> PyResult<Py<PyAny>> {
        infer_to_python(value, include, exclude, state, extra)
    }

    fn json_key<'a, 'py>(
        &self,
        key: &'a Bound<'py, PyAny>,
        state: &mut SerializationState<'py>,
        extra: &Extra<'_, 'py>,
    ) -> PyResult<Cow<'a, str>> {
        infer_json_key(key, state, extra)
    }

    fn serde_serialize<'py, S: Serializer>(
        &self,
        value: &Bound<'py, PyAny>,
        serializer: S,
        include: Option<&Bound<'py, PyAny>>,
        exclude: Option<&Bound<'py, PyAny>>,
        state: &mut SerializationState<'py>,
        extra: &Extra<'_, 'py>,
    ) -> Result<S::Ok, S::Error> {
        infer_serialize(value, serializer, include, exclude, state, extra)
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}
