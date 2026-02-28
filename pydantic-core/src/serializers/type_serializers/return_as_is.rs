use std::{borrow::Cow, sync::Arc};

use pyo3::prelude::*;
use pyo3::types::PyDict;

use super::{BuildSerializer, CombinedSerializer, TypeSerializer, infer_json_key, infer_serialize};
use crate::build_tools::LazyLock;
use crate::definitions::DefinitionsBuilder;

use serde::ser::Serializer;

use crate::serializers::SerializationState;

#[derive(Debug)]
pub struct ReturnAsIsSerializer {}

static RETURN_AS_IS_SERIALIZER: LazyLock<Arc<CombinedSerializer>> =
    LazyLock::new(|| Arc::new(ReturnAsIsSerializer {}.into()));

impl BuildSerializer for ReturnAsIsSerializer {
    const EXPECTED_TYPE: &'static str = "return-as-is";

    fn build(
        _schema: &Bound<'_, PyDict>,
        _config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        Ok(RETURN_AS_IS_SERIALIZER.clone())
    }
}

impl_py_gc_traverse!(ReturnAsIsSerializer {});

impl TypeSerializer for ReturnAsIsSerializer {
    fn to_python(&self, value: &Bound<'_, PyAny>, _state: &mut SerializationState<'_>) -> PyResult<Py<PyAny>> {
        // Returns the exact same Python object reference.
        Ok(value.to_owned().into())
    }

    fn json_key<'a, 'py>(
        &self,
        key: &'a Bound<'py, PyAny>,
        state: &mut SerializationState<'py>,
    ) -> PyResult<Cow<'a, str>> {
        infer_json_key(key, state)
    }

    fn serde_serialize<'py, S: Serializer>(
        &self,
        value: &Bound<'py, PyAny>,
        serializer: S,
        state: &mut SerializationState<'py>,
    ) -> Result<S::Ok, S::Error> {
        infer_serialize(value, serializer, state)
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}
