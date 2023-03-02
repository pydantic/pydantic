use std::borrow::Cow;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use crate::build_context::{BuildContext, ThingOrId};
use crate::build_tools::SchemaDict;

use super::{py_err_se_err, BuildSerializer, CombinedSerializer, Extra, TypeSerializer};

#[derive(Debug, Clone)]
pub struct DefinitionsBuilder;

impl BuildSerializer for DefinitionsBuilder {
    const EXPECTED_TYPE: &'static str = "definitions";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let py = schema.py();

        let definitions: &PyList = schema.get_as_req(intern!(py, "definitions"))?;

        for def_schema in definitions {
            CombinedSerializer::build(def_schema.downcast()?, config, build_context)?;
            // no need to store the serializer here, it has already been stored in build_context if necessary
        }

        let inner_schema: &PyDict = schema.get_as_req(intern!(py, "schema"))?;
        CombinedSerializer::build(inner_schema, config, build_context)
    }
}

#[derive(Debug, Clone)]
pub struct DefinitionRefSerializer {
    serializer_id: usize,
}

impl DefinitionRefSerializer {
    pub fn from_id(serializer_id: usize) -> CombinedSerializer {
        Self { serializer_id }.into()
    }
}

impl BuildSerializer for DefinitionRefSerializer {
    const EXPECTED_TYPE: &'static str = "definition-ref";

    fn build(
        schema: &PyDict,
        _config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let schema_ref: String = schema.get_as_req(intern!(schema.py(), "schema_ref"))?;

        match build_context.find(&schema_ref)? {
            ThingOrId::Thing(serializer) => Ok(serializer),
            ThingOrId::Id(serializer_id) => Ok(Self { serializer_id }.into()),
        }
    }
}

impl TypeSerializer for DefinitionRefSerializer {
    fn to_python(
        &self,
        value: &PyAny,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        let value_id = extra.rec_guard.add(value)?;
        let comb_serializer = unsafe { extra.slots.get_unchecked(self.serializer_id) };
        let r = comb_serializer.to_python(value, include, exclude, extra);
        extra.rec_guard.pop(value_id);
        r
    }

    fn json_key<'py>(&self, key: &'py PyAny, extra: &Extra) -> PyResult<Cow<'py, str>> {
        self._invalid_as_json_key(key, extra, Self::EXPECTED_TYPE)
    }

    fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        value: &PyAny,
        serializer: S,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> Result<S::Ok, S::Error> {
        let value_id = extra.rec_guard.add(value).map_err(py_err_se_err)?;
        let comb_serializer = unsafe { extra.slots.get_unchecked(self.serializer_id) };
        let r = comb_serializer.serde_serialize(value, serializer, include, exclude, extra);
        extra.rec_guard.pop(value_id);
        r
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}
