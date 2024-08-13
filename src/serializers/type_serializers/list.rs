use std::borrow::Cow;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use serde::ser::SerializeSeq;

use crate::definitions::DefinitionsBuilder;
use crate::tools::SchemaDict;

use super::any::AnySerializer;
use super::{
    infer_serialize, infer_to_python, py_err_se_err, BuildSerializer, CombinedSerializer, Extra, PydanticSerializer,
    SchemaFilter, TypeSerializer,
};

#[derive(Debug)]
pub struct ListSerializer {
    item_serializer: Box<CombinedSerializer>,
    filter: SchemaFilter<usize>,
    name: String,
}

impl BuildSerializer for ListSerializer {
    const EXPECTED_TYPE: &'static str = "list";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let py = schema.py();
        let item_serializer = match schema.get_as(intern!(py, "items_schema"))? {
            Some(items_schema) => CombinedSerializer::build(&items_schema, config, definitions)?,
            None => AnySerializer::build(schema, config, definitions)?,
        };
        let name = format!("{}[{}]", Self::EXPECTED_TYPE, item_serializer.get_name());
        Ok(Self {
            item_serializer: Box::new(item_serializer),
            filter: SchemaFilter::from_schema(schema)?,
            name,
        }
        .into())
    }
}

impl_py_gc_traverse!(ListSerializer { item_serializer });

impl TypeSerializer for ListSerializer {
    fn to_python(
        &self,
        value: &Bound<'_, PyAny>,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        match value.downcast::<PyList>() {
            Ok(py_list) => {
                let py = value.py();
                let item_serializer = self.item_serializer.as_ref();

                let mut items = Vec::with_capacity(py_list.len());
                for (index, element) in py_list.iter().enumerate() {
                    let op_next = self.filter.index_filter(index, include, exclude, value.len().ok())?;
                    if let Some((next_include, next_exclude)) = op_next {
                        items.push(item_serializer.to_python(
                            &element,
                            next_include.as_ref(),
                            next_exclude.as_ref(),
                            extra,
                        )?);
                    }
                }
                Ok(items.into_py(py))
            }
            Err(_) => {
                extra.warnings.on_fallback_py(self.get_name(), value, extra)?;
                infer_to_python(value, include, exclude, extra)
            }
        }
    }

    fn json_key<'a>(&self, key: &'a Bound<'_, PyAny>, extra: &Extra) -> PyResult<Cow<'a, str>> {
        self._invalid_as_json_key(key, extra, Self::EXPECTED_TYPE)
    }

    fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        value: &Bound<'_, PyAny>,
        serializer: S,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> Result<S::Ok, S::Error> {
        match value.downcast::<PyList>() {
            Ok(py_list) => {
                let mut seq = serializer.serialize_seq(Some(py_list.len()))?;
                let item_serializer = self.item_serializer.as_ref();

                for (index, element) in py_list.iter().enumerate() {
                    let op_next = self
                        .filter
                        .index_filter(index, include, exclude, Some(py_list.len()))
                        .map_err(py_err_se_err)?;
                    if let Some((next_include, next_exclude)) = op_next {
                        let item_serialize = PydanticSerializer::new(
                            &element,
                            item_serializer,
                            next_include.as_ref(),
                            next_exclude.as_ref(),
                            extra,
                        );
                        seq.serialize_element(&item_serialize)?;
                    }
                }
                seq.end()
            }
            Err(_) => {
                extra.warnings.on_fallback_ser::<S>(self.get_name(), value, extra)?;
                infer_serialize(value, serializer, include, exclude, extra)
            }
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn retry_with_lax_check(&self) -> bool {
        self.item_serializer.retry_with_lax_check()
    }
}
