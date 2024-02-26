use std::borrow::Cow;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use crate::definitions::DefinitionsBuilder;
use crate::definitions::{DefinitionRef, RecursionSafeCache};

use crate::tools::SchemaDict;

use super::{py_err_se_err, BuildSerializer, CombinedSerializer, Extra, TypeSerializer};

#[derive(Debug, Clone)]
pub struct DefinitionsSerializerBuilder;

impl BuildSerializer for DefinitionsSerializerBuilder {
    const EXPECTED_TYPE: &'static str = "definitions";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let py = schema.py();

        let schema_definitions: &PyList = schema.get_as_req(intern!(py, "definitions"))?;

        for schema_definition in schema_definitions {
            let reference = schema_definition
                .extract::<&PyDict>()?
                .get_as_req::<String>(intern!(py, "ref"))?;
            let serializer = CombinedSerializer::build(schema_definition.downcast()?, config, definitions)?;
            definitions.add_definition(reference, serializer)?;
        }

        let inner_schema: &PyDict = schema.get_as_req(intern!(py, "schema"))?;
        CombinedSerializer::build(inner_schema, config, definitions)
    }
}

pub struct DefinitionRefSerializer {
    definition: DefinitionRef<CombinedSerializer>,
    retry_with_lax_check: RecursionSafeCache<bool>,
}

// TODO(DH): Remove the need to clone serializers
impl Clone for DefinitionRefSerializer {
    fn clone(&self) -> Self {
        Self {
            definition: self.definition.clone(),
            retry_with_lax_check: RecursionSafeCache::new(),
        }
    }
}

impl std::fmt::Debug for DefinitionRefSerializer {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("DefinitionRefSerializer")
            .field("definition", &self.definition)
            .field("retry_with_lax_check", &self.retry_with_lax_check())
            .finish()
    }
}

impl BuildSerializer for DefinitionRefSerializer {
    const EXPECTED_TYPE: &'static str = "definition-ref";

    fn build(
        schema: &PyDict,
        _config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let schema_ref = schema.get_as_req(intern!(schema.py(), "schema_ref"))?;
        let definition = definitions.get_definition(schema_ref);
        Ok(Self {
            definition,
            retry_with_lax_check: RecursionSafeCache::new(),
        }
        .into())
    }
}

impl_py_gc_traverse!(DefinitionRefSerializer {});

impl TypeSerializer for DefinitionRefSerializer {
    fn to_python(
        &self,
        value: &PyAny,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        mut extra: &Extra,
    ) -> PyResult<PyObject> {
        self.definition.read(|comb_serializer| {
            let comb_serializer = comb_serializer.unwrap();
            let mut guard = extra.recursion_guard(value, self.definition.id())?;
            comb_serializer.to_python(value, include, exclude, guard.state())
        })
    }

    fn json_key<'py>(&self, key: &'py PyAny, extra: &Extra) -> PyResult<Cow<'py, str>> {
        self.definition.read(|s| s.unwrap().json_key(key, extra))
    }

    fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        value: &PyAny,
        serializer: S,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        mut extra: &Extra,
    ) -> Result<S::Ok, S::Error> {
        self.definition.read(|comb_serializer| {
            let comb_serializer = comb_serializer.unwrap();
            let mut guard = extra
                .recursion_guard(value, self.definition.id())
                .map_err(py_err_se_err)?;
            comb_serializer.serde_serialize(value, serializer, include, exclude, guard.state())
        })
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }

    fn retry_with_lax_check(&self) -> bool {
        *self
            .retry_with_lax_check
            .get_or_init(|| self.definition.read(|s| s.unwrap().retry_with_lax_check()), &false)
    }
}
