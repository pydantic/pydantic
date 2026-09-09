// When the 'missing-sentinel' core schema has no inner 'schema', this serializer is only defined
// so that building a schema serializer containing it doesn't crash. In practice, the serializer
// isn't used for model-like classes, as the 'fields' serializer takes care of omitting the fields
// from the output (the serializer can still be used if the 'missing-sentinel' core schema is used
// standalone (e.g. with a Pydantic type adapter), but this isn't something we explicitly support).

use std::borrow::Cow;
use std::sync::Arc;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use serde::ser::Error;

use crate::PydanticSerializationUnexpectedValue;
use crate::common::missing_sentinel::get_missing_sentinel_object;
use crate::definitions::DefinitionsBuilder;
use crate::serializers::SerializationState;
use crate::tools::SchemaDict;

use super::{BuildSerializer, CombinedSerializer, TypeSerializer};

#[derive(Debug)]
pub struct MissingSentinelSerializer {
    /// The serializer of the inner schema (if any). If not set, only the `MISSING` sentinel can be serialized.
    serializer: Option<Arc<CombinedSerializer>>,
}

impl BuildSerializer for MissingSentinelSerializer {
    const EXPECTED_TYPE: &'static str = "missing-sentinel";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        let serializer = match schema.get_as::<Bound<'_, PyDict>>(intern!(schema.py(), "schema"))? {
            Some(inner_schema) => Some(CombinedSerializer::build(&inner_schema, config, definitions)?),
            None => None,
        };
        Ok(CombinedSerializer::MissingSentinel(Self { serializer }).into())
    }
}

impl_py_gc_traverse!(MissingSentinelSerializer { serializer });

impl TypeSerializer for MissingSentinelSerializer {
    fn to_python<'py>(&self, value: &Bound<'py, PyAny>, state: &mut SerializationState<'py>) -> PyResult<Py<PyAny>> {
        let missing_sentinel = get_missing_sentinel_object(value.py());

        if value.is(missing_sentinel) {
            return Ok(missing_sentinel.to_owned().into());
        }

        match &self.serializer {
            Some(serializer) => serializer.to_python(value, state),
            None => Err(PydanticSerializationUnexpectedValue::new_from_msg(Some(
                "Expected 'MISSING' sentinel".to_string(),
            ))
            .to_py_err()),
        }
    }

    fn json_key<'a, 'py>(
        &self,
        key: &'a Bound<'py, PyAny>,
        state: &mut SerializationState<'py>,
    ) -> PyResult<Cow<'a, str>> {
        let missing_sentinel = get_missing_sentinel_object(key.py());

        match &self.serializer {
            Some(serializer) if !key.is(missing_sentinel) => serializer.json_key(key, state),
            _ => self.invalid_as_json_key(key, state, Self::EXPECTED_TYPE),
        }
    }

    fn serde_serialize<'py, S: serde::ser::Serializer>(
        &self,
        value: &Bound<'py, PyAny>,
        serializer: S,
        state: &mut SerializationState<'py>,
    ) -> Result<S::Ok, S::Error> {
        let missing_sentinel = get_missing_sentinel_object(value.py());

        match &self.serializer {
            Some(inner_serializer) if !value.is(missing_sentinel) => {
                inner_serializer.serde_serialize(value, serializer, state)
            }
            _ => Err(Error::custom("'MISSING' can't be serialized to JSON".to_string())),
        }
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }

    fn retry_with_lax_check(&self) -> bool {
        self.serializer.as_ref().is_some_and(|s| s.retry_with_lax_check())
    }
}
