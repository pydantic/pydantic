use std::borrow::Cow;
use std::sync::Arc;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use super::{BuildSerializer, CombinedSerializer, Extra, TypeSerializer};
use crate::definitions::DefinitionsBuilder;
use crate::serializers::SerializationState;
use crate::tools::SchemaDict;

#[derive(Debug)]
pub struct JsonOrPythonSerializer {
    json: Arc<CombinedSerializer>,
    python: Arc<CombinedSerializer>,
    name: String,
}

impl BuildSerializer for JsonOrPythonSerializer {
    const EXPECTED_TYPE: &'static str = "json-or-python";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        let py = schema.py();
        let json_schema = schema.get_as_req(intern!(py, "json_schema"))?;
        let python_schema = schema.get_as_req(intern!(py, "python_schema"))?;

        let json = CombinedSerializer::build(&json_schema, config, definitions)?;
        let python = CombinedSerializer::build(&python_schema, config, definitions)?;

        let name = format!(
            "{}[json={}, python={}]",
            Self::EXPECTED_TYPE,
            json.get_name(),
            python.get_name(),
        );
        Ok(Arc::new(Self { json, python, name }.into()))
    }
}

impl_py_gc_traverse!(JsonOrPythonSerializer { json, python });

impl TypeSerializer for JsonOrPythonSerializer {
    fn to_python<'py>(
        &self,
        value: &Bound<'py, PyAny>,
        include: Option<&Bound<'py, PyAny>>,
        exclude: Option<&Bound<'py, PyAny>>,
        state: &mut SerializationState<'py>,
        extra: &Extra<'_, 'py>,
    ) -> PyResult<Py<PyAny>> {
        self.python.to_python(value, include, exclude, state, extra)
    }

    fn json_key<'a, 'py>(
        &self,
        key: &'a Bound<'py, PyAny>,
        state: &mut SerializationState<'py>,
        extra: &Extra<'_, 'py>,
    ) -> PyResult<Cow<'a, str>> {
        self.json.json_key(key, state, extra)
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
        self.json
            .serde_serialize(value, serializer, include, exclude, state, extra)
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}
