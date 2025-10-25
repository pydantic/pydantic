use std::borrow::Cow;
use std::str::from_utf8;
use std::sync::Arc;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use pyo3::types::PyString;
use serde::ser::Error;

use crate::definitions::DefinitionsBuilder;
use crate::serializers::SerializationState;
use crate::tools::SchemaDict;

use super::any::AnySerializer;
use super::{
    infer_json_key, py_err_se_err, to_json_bytes, utf8_py_error, BuildSerializer, CombinedSerializer, Extra,
    TypeSerializer,
};

#[derive(Debug)]
pub struct JsonSerializer {
    serializer: Arc<CombinedSerializer>,
}

impl BuildSerializer for JsonSerializer {
    const EXPECTED_TYPE: &'static str = "json";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        let py = schema.py();

        let serializer = match schema.get_as(intern!(py, "schema"))? {
            Some(items_schema) => CombinedSerializer::build(&items_schema, config, definitions)?,
            None => AnySerializer::build(schema, config, definitions)?,
        };
        Ok(Arc::new(Self { serializer }.into()))
    }
}

impl_py_gc_traverse!(JsonSerializer { serializer });

impl TypeSerializer for JsonSerializer {
    fn to_python<'py>(
        &self,
        value: &Bound<'py, PyAny>,
        state: &mut SerializationState<'py>,
        extra: &Extra<'_, 'py>,
    ) -> PyResult<Py<PyAny>> {
        if extra.round_trip {
            let bytes = to_json_bytes(value, &self.serializer, state, extra, None, false, 0)?;
            let py = value.py();
            let s = from_utf8(&bytes).map_err(|e| utf8_py_error(py, e, &bytes))?;
            Ok(PyString::new(py, s).into())
        } else {
            self.serializer.to_python(value, state, extra)
        }
    }

    fn json_key<'a, 'py>(
        &self,
        key: &'a Bound<'py, PyAny>,
        state: &mut SerializationState<'py>,
        extra: &Extra<'_, 'py>,
    ) -> PyResult<Cow<'a, str>> {
        if extra.round_trip {
            let bytes = to_json_bytes(key, &self.serializer, state, extra, None, false, 0)?;
            let py = key.py();
            let s = from_utf8(&bytes).map_err(|e| utf8_py_error(py, e, &bytes))?;
            Ok(Cow::Owned(s.to_string()))
        } else {
            infer_json_key(key, state, extra)
        }
    }

    fn serde_serialize<'py, S: serde::ser::Serializer>(
        &self,
        value: &Bound<'py, PyAny>,
        serializer: S,
        state: &mut SerializationState<'py>,
        extra: &Extra<'_, 'py>,
    ) -> Result<S::Ok, S::Error> {
        if extra.round_trip {
            let bytes = to_json_bytes(value, &self.serializer, state, extra, None, false, 0).map_err(py_err_se_err)?;
            match from_utf8(&bytes) {
                Ok(s) => serializer.serialize_str(s),
                Err(e) => Err(Error::custom(e.to_string())),
            }
        } else {
            self.serializer.serde_serialize(value, serializer, state, extra)
        }
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}
