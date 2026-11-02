use std::borrow::Cow;
use std::sync::Arc;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::definitions::DefinitionsBuilder;
use crate::serializers::SerializationState;
use crate::tools::SchemaDict;

use super::{BuildSerializer, CombinedSerializer, ObType, TypeSerializer, infer_json_key_known};

#[derive(Debug)]
pub struct NullableSerializer {
    serializer: Arc<CombinedSerializer>,
}

impl BuildSerializer for NullableSerializer {
    const EXPECTED_TYPE: &'static str = "nullable";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        let sub_schema = schema.get_as_req(intern!(schema.py(), "schema"))?;
        Ok(CombinedSerializer::Nullable(Self {
            serializer: CombinedSerializer::build(&sub_schema, config, definitions)?,
        })
        .into())
    }
}

impl_py_gc_traverse!(NullableSerializer { serializer });

impl TypeSerializer for NullableSerializer {
    fn to_python<'py>(&self, value: &Bound<'py, PyAny>, state: &mut SerializationState<'py>) -> PyResult<Py<PyAny>> {
        if value.is_none() {
            Ok(value.py().None())
        } else {
            self.serializer.to_python(value, state)
        }
    }

    fn json_key<'a, 'py>(
        &self,
        key: &'a Bound<'py, PyAny>,
        state: &mut SerializationState<'py>,
    ) -> PyResult<Cow<'a, str>> {
        if key.is_none() {
            infer_json_key_known(ObType::None, key, state)
        } else {
            self.serializer.json_key(key, state)
        }
    }

    fn serde_serialize<'py, S: serde::ser::Serializer>(
        &self,
        value: &Bound<'py, PyAny>,
        serializer: S,
        state: &mut SerializationState<'py>,
    ) -> Result<S::Ok, S::Error> {
        if value.is_none() {
            serializer.serialize_none()
        } else {
            self.serializer.serde_serialize(value, serializer, state)
        }
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }

    fn retry_with_lax_check(&self) -> bool {
        self.serializer.retry_with_lax_check()
    }
}
