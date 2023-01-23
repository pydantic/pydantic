use std::borrow::Cow;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_context::BuildContext;
use crate::build_tools::SchemaDict;

use super::{infer_json_key_known, BuildSerializer, CombinedSerializer, Extra, IsType, ObType, TypeSerializer};

#[derive(Debug, Clone)]
pub struct NullableSerializer {
    serializer: Box<CombinedSerializer>,
}

impl BuildSerializer for NullableSerializer {
    const EXPECTED_TYPE: &'static str = "nullable";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let sub_schema = schema.get_as_req::<&PyDict>(intern!(schema.py(), "schema"))?;
        Ok(Self {
            serializer: Box::new(CombinedSerializer::build(sub_schema, config, build_context)?),
        }
        .into())
    }
}

impl TypeSerializer for NullableSerializer {
    fn to_python(
        &self,
        value: &PyAny,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        let py = value.py();
        match extra.ob_type_lookup.is_type(value, ObType::None) {
            IsType::Exact => Ok(py.None().into_py(py)),
            // I don't think subclasses of None can exist
            _ => self.serializer.to_python(value, include, exclude, extra),
        }
    }

    fn json_key<'py>(&self, key: &'py PyAny, extra: &Extra) -> PyResult<Cow<'py, str>> {
        match extra.ob_type_lookup.is_type(key, ObType::None) {
            IsType::Exact => infer_json_key_known(&ObType::None, key, extra),
            _ => self.serializer.json_key(key, extra),
        }
    }

    fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        value: &PyAny,
        serializer: S,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> Result<S::Ok, S::Error> {
        match extra.ob_type_lookup.is_type(value, ObType::None) {
            IsType::Exact => serializer.serialize_none(),
            _ => self
                .serializer
                .serde_serialize(value, serializer, include, exclude, extra),
        }
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }

    fn retry_with_lax_check(&self) -> bool {
        self.serializer.retry_with_lax_check()
    }
}
