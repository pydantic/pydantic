use std::borrow::Cow;

use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::common::prebuilt::get_prebuilt;
use crate::SchemaSerializer;

use super::extra::Extra;
use super::shared::{CombinedSerializer, TypeSerializer};

#[derive(Debug)]
pub struct PrebuiltSerializer {
    schema_serializer: Py<SchemaSerializer>,
}

impl PrebuiltSerializer {
    pub fn try_get_from_schema(type_: &str, schema: &Bound<'_, PyDict>) -> PyResult<Option<CombinedSerializer>> {
        get_prebuilt(type_, schema, "__pydantic_serializer__", |py_any| {
            let schema_serializer = py_any.extract::<Py<SchemaSerializer>>()?;
            if matches!(schema_serializer.get().serializer, CombinedSerializer::FunctionWrap(_)) {
                return Ok(None);
            }
            Ok(Some(Self { schema_serializer }.into()))
        })
    }
}

impl_py_gc_traverse!(PrebuiltSerializer { schema_serializer });

impl TypeSerializer for PrebuiltSerializer {
    fn to_python(
        &self,
        value: &Bound<'_, PyAny>,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        self.schema_serializer
            .get()
            .serializer
            .to_python_no_infer(value, include, exclude, extra)
    }

    fn json_key<'a>(&self, key: &'a Bound<'_, PyAny>, extra: &Extra) -> PyResult<Cow<'a, str>> {
        self.schema_serializer.get().serializer.json_key_no_infer(key, extra)
    }

    fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        value: &Bound<'_, PyAny>,
        serializer: S,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> Result<S::Ok, S::Error> {
        self.schema_serializer
            .get()
            .serializer
            .serde_serialize_no_infer(value, serializer, include, exclude, extra)
    }

    fn get_name(&self) -> &str {
        self.schema_serializer.get().serializer.get_name()
    }

    fn retry_with_lax_check(&self) -> bool {
        self.schema_serializer.get().serializer.retry_with_lax_check()
    }
}
