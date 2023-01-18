use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use serde::ser::SerializeSeq;

use crate::build_context::BuildContext;
use crate::build_tools::SchemaDict;

use super::any::{fallback_serialize, fallback_to_python, AnySerializer};
use super::{
    py_err_se_err, BuildSerializer, CombinedSerializer, Extra, PydanticSerializer, SchemaFilter, TypeSerializer,
};

#[derive(Debug, Clone)]
pub struct ListSerializer {
    item_serializer: Box<CombinedSerializer>,
    filter: SchemaFilter<usize>,
}

impl BuildSerializer for ListSerializer {
    const EXPECTED_TYPE: &'static str = "list";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let py = schema.py();
        let item_serializer = match schema.get_as::<&PyDict>(intern!(py, "items_schema"))? {
            Some(items_schema) => CombinedSerializer::build(items_schema, config, build_context)?,
            None => AnySerializer::build(schema, config, build_context)?,
        };
        Ok(Self {
            item_serializer: Box::new(item_serializer),
            filter: SchemaFilter::from_schema(schema)?,
        }
        .into())
    }
}

impl TypeSerializer for ListSerializer {
    fn to_python(
        &self,
        value: &PyAny,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        match value.downcast::<PyList>() {
            Ok(py_list) => {
                let py = value.py();
                let item_serializer = self.item_serializer.as_ref();

                let mut items = Vec::with_capacity(py_list.len());
                for (index, element) in py_list.iter().enumerate() {
                    let op_next = self.filter.value_filter(index, include, exclude)?;
                    if let Some((next_include, next_exclude)) = op_next {
                        items.push(item_serializer.to_python(element, next_include, next_exclude, extra)?);
                    }
                }
                Ok(items.into_py(py))
            }
            Err(_) => {
                extra.warnings.fallback_filtering(Self::EXPECTED_TYPE, value);
                fallback_to_python(value, include, exclude, extra)
            }
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
        match value.downcast::<PyList>() {
            Ok(py_list) => {
                let mut seq = serializer.serialize_seq(Some(py_list.len()))?;
                let item_serializer = self.item_serializer.as_ref();

                for (index, element) in py_list.iter().enumerate() {
                    let op_next = self
                        .filter
                        .value_filter(index, include, exclude)
                        .map_err(py_err_se_err)?;
                    if let Some((next_include, next_exclude)) = op_next {
                        let item_serialize =
                            PydanticSerializer::new(element, item_serializer, next_include, next_exclude, extra);
                        seq.serialize_element(&item_serialize)?;
                    }
                }
                seq.end()
            }
            Err(_) => {
                extra.warnings.fallback_filtering(Self::EXPECTED_TYPE, value);
                fallback_serialize(value, serializer, include, exclude, extra)
            }
        }
    }
}
