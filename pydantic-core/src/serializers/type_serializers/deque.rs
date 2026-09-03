use std::borrow::Cow;
use std::sync::Arc;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use serde::ser::SerializeSeq;

use crate::common::deque::get_deque_type;
use crate::definitions::DefinitionsBuilder;
use crate::serializers::SerializationState;
use crate::tools::SchemaDict;

use super::any::AnySerializer;
use super::{
    BuildSerializer, CombinedSerializer, PydanticSerializer, SchemaFilter, SerMode, TypeSerializer, infer_serialize,
    infer_to_python, py_err_se_err,
};

#[derive(Debug)]
pub struct DequeSerializer {
    item_serializer: Arc<CombinedSerializer>,
    filter: SchemaFilter<usize>,
    name: String,
}

impl BuildSerializer for DequeSerializer {
    const EXPECTED_TYPE: &'static str = "deque";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        let py = schema.py();
        let item_serializer = match schema.get_as(intern!(py, "items_schema"))? {
            Some(items_schema) => CombinedSerializer::build(&items_schema, config, definitions)?,
            None => AnySerializer::build(schema, config, definitions)?,
        };
        let name = format!("{}[{}]", Self::EXPECTED_TYPE, item_serializer.get_name());
        Ok(Arc::new(
            Self {
                item_serializer,
                filter: SchemaFilter::from_schema(schema)?,
                name,
            }
            .into(),
        ))
    }
}

impl_py_gc_traverse!(DequeSerializer { item_serializer });

/// Returns the (length, `maxlen`) of `value` if it is a `collections.deque` instance.
fn as_deque(value: &Bound<'_, PyAny>) -> PyResult<Option<(usize, Option<usize>)>> {
    let py = value.py();
    if value.is_instance(get_deque_type(py)?)? {
        let maxlen: Option<usize> = value.getattr(intern!(py, "maxlen"))?.extract()?;
        Ok(Some((value.len()?, maxlen)))
    } else {
        Ok(None)
    }
}

impl TypeSerializer for DequeSerializer {
    fn to_python<'py>(&self, value: &Bound<'py, PyAny>, state: &mut SerializationState<'py>) -> PyResult<Py<PyAny>> {
        let py = value.py();
        match as_deque(value)? {
            Some((len, maxlen)) => {
                let item_serializer = self.item_serializer.as_ref();

                let mut items = Vec::with_capacity(len);
                for (index, element) in value.try_iter()?.enumerate() {
                    let element = element?;
                    let op_next = self.filter.index_filter(index, state, Some(len))?;
                    if let Some(next_include_exclude) = op_next {
                        let state = &mut state.scoped_include_exclude(next_include_exclude);
                        items.push(item_serializer.to_python(&element, state)?);
                    }
                }
                let items = PyList::new(py, items)?;
                match state.extra.mode {
                    SerMode::Json => Ok(items.into()),
                    _ => {
                        let deque_type = get_deque_type(py)?;
                        let deque = match maxlen {
                            Some(maxlen) => {
                                let kwargs = PyDict::new(py);
                                kwargs.set_item(intern!(py, "maxlen"), maxlen)?;
                                deque_type.call((items,), Some(&kwargs))?
                            }
                            None => deque_type.call1((items,))?,
                        };
                        Ok(deque.unbind())
                    }
                }
            }
            None => {
                state.warn_fallback_py(self.get_name(), value)?;
                infer_to_python(value, state)
            }
        }
    }

    fn json_key<'a, 'py>(
        &self,
        key: &'a Bound<'py, PyAny>,
        state: &mut SerializationState<'py>,
    ) -> PyResult<Cow<'a, str>> {
        self.invalid_as_json_key(key, state, Self::EXPECTED_TYPE)
    }

    fn serde_serialize<'py, S: serde::ser::Serializer>(
        &self,
        value: &Bound<'py, PyAny>,
        serializer: S,
        state: &mut SerializationState<'py>,
    ) -> Result<S::Ok, S::Error> {
        match as_deque(value).map_err(py_err_se_err)? {
            Some((len, _)) => {
                let mut seq = serializer.serialize_seq(Some(len))?;
                let item_serializer = self.item_serializer.as_ref();

                for (index, element) in value.try_iter().map_err(py_err_se_err)?.enumerate() {
                    let element = element.map_err(py_err_se_err)?;
                    let op_next = self
                        .filter
                        .index_filter(index, state, Some(len))
                        .map_err(py_err_se_err)?;
                    if let Some(next_include_exclude) = op_next {
                        let state = &mut state.scoped_include_exclude(next_include_exclude);
                        let item_serialize = PydanticSerializer::new(&element, item_serializer, state);
                        seq.serialize_element(&item_serialize)?;
                    }
                }
                seq.end()
            }
            None => {
                state.warn_fallback_ser::<S>(self.get_name(), value)?;
                infer_serialize(value, serializer, state)
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
