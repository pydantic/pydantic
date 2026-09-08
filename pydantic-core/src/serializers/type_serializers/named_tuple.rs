use std::borrow::Cow;
use std::sync::Arc;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyTuple, PyType};

use serde::ser::SerializeSeq;

use crate::PydanticSerializationUnexpectedValue;
use crate::build_tools::py_schema_error_type;
use crate::definitions::DefinitionsBuilder;
use crate::serializers::SerializationState;
use crate::serializers::extra::IncludeExclude;
use crate::serializers::extra::SerCheck;
use crate::tools::SchemaDict;

use super::tuple::KeyBuilder;
use super::{
    BuildSerializer, CombinedSerializer, PydanticSerializer, SchemaFilter, SerMode, TypeSerializer, infer_json_key,
    infer_serialize, infer_to_python, py_err_se_err,
};

#[derive(Debug)]
pub struct NamedTupleSerializer {
    class: Py<PyType>,
    serializers: Vec<Arc<CombinedSerializer>>,
    filter: SchemaFilter<usize>,
    name: String,
}

impl BuildSerializer for NamedTupleSerializer {
    const EXPECTED_TYPE: &'static str = "named-tuple";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        let py = schema.py();

        let class = schema.get_as_req::<Bound<'_, PyType>>(intern!(py, "cls"))?;
        let name = match schema.get_as::<String>(intern!(py, "cls_name"))? {
            Some(name) => name,
            None => class.getattr(intern!(py, "__name__"))?.extract()?,
        };

        let fields_list: Bound<'_, PyList> = schema.get_as_req(intern!(py, "fields"))?;
        let mut serializers: Vec<Arc<CombinedSerializer>> = Vec::with_capacity(fields_list.len());

        for field in fields_list {
            let field = field.cast::<PyDict>()?;
            let field_name: String = field.get_as_req(intern!(py, "name"))?;
            let field_schema = field.get_as_req(intern!(py, "schema"))?;
            let serializer = CombinedSerializer::build(&field_schema, config, definitions)
                .map_err(|e| py_schema_error_type!("Field `{field_name}`:\n  {e}"))?;
            serializers.push(serializer);
        }

        Ok(CombinedSerializer::NamedTuple(Self {
            class: class.into(),
            serializers,
            filter: SchemaFilter::from_schema(schema)?,
            name,
        })
        .into())
    }
}

impl_py_gc_traverse!(NamedTupleSerializer { class, serializers });

impl TypeSerializer for NamedTupleSerializer {
    fn to_python<'py>(&self, value: &Bound<'py, PyAny>, state: &mut SerializationState<'py>) -> PyResult<Py<PyAny>> {
        match self.tuple_value(value, state)? {
            Some(py_tuple) => {
                let py = value.py();

                let mut items = Vec::with_capacity(py_tuple.len());

                self.for_each_item_and_serializer(&py_tuple, state, |entry| {
                    entry
                        .serializer
                        .to_python(&entry.item, entry.state)
                        .map(|item| items.push(item))
                })??;

                match state.extra.mode {
                    SerMode::Json => Ok(PyList::new(py, items)?.into()),
                    _ => Ok(PyTuple::new(py, items)?.into()),
                }
            }
            None => {
                state.warn_fallback_py(&self.name, value)?;
                infer_to_python(value, state)
            }
        }
    }

    fn json_key<'a, 'py>(
        &self,
        key: &'a Bound<'py, PyAny>,
        state: &mut SerializationState<'py>,
    ) -> PyResult<Cow<'a, str>> {
        match self.tuple_value(key, state)? {
            Some(py_tuple) => {
                let mut key_builder = KeyBuilder::new();

                let state = &mut state.scoped_include_exclude(IncludeExclude::empty());
                self.for_each_item_and_serializer(&py_tuple, state, |entry| {
                    entry
                        .serializer
                        .json_key(&entry.item, entry.state)
                        .map(|key| key_builder.push(&key))
                })??;

                Ok(Cow::Owned(key_builder.finish()))
            }
            None => {
                state.warn_fallback_py(&self.name, key)?;
                infer_json_key(key, state)
            }
        }
    }

    fn serde_serialize<'py, S: serde::ser::Serializer>(
        &self,
        value: &Bound<'py, PyAny>,
        serializer: S,
        state: &mut SerializationState<'py>,
    ) -> Result<S::Ok, S::Error> {
        match self.tuple_value(value, state).map_err(py_err_se_err)? {
            Some(py_tuple) => {
                let mut seq = serializer.serialize_seq(Some(py_tuple.len()))?;

                self.for_each_item_and_serializer(&py_tuple, state, |entry| {
                    seq.serialize_element(&PydanticSerializer::new(&entry.item, entry.serializer, entry.state))
                })
                .map_err(py_err_se_err)??;

                seq.end()
            }
            None => {
                state.warn_fallback_ser::<S>(&self.name, value)?;
                infer_serialize(value, serializer, state)
            }
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn retry_with_lax_check(&self) -> bool {
        true
    }
}

struct NamedTupleSerializerEntry<'a, 'py> {
    item: Bound<'py, PyAny>,
    serializer: &'a CombinedSerializer,
    state: &'a mut SerializationState<'py>,
}

impl NamedTupleSerializer {
    /// Extract the value as a tuple, if possible.
    ///
    /// In strict check mode (e.g. when serializing a union), the value is required to be an
    /// instance of the named tuple class, so that the nominal class is preserved. In lax check
    /// mode, any tuple is accepted.
    fn tuple_value<'py>(
        &self,
        value: &Bound<'py, PyAny>,
        state: &SerializationState<'py>,
    ) -> PyResult<Option<Bound<'py, PyTuple>>> {
        if state.check == SerCheck::Strict && !value.is_instance(self.class.bind(value.py()))? {
            return Ok(None);
        }
        Ok(value.cast::<PyTuple>().ok().map(Bound::to_owned))
    }

    /// Try to serialize each item in the tuple with the corresponding field serializer.
    ///
    /// If the tuple doesn't match the number of fields, in strict check mode, an error is
    /// returned; otherwise a warning is emitted and extra items are dropped.
    fn for_each_item_and_serializer<'py, E>(
        &self,
        tuple: &Bound<'py, PyTuple>,
        state: &mut SerializationState<'py>,
        mut f: impl for<'a> FnMut(NamedTupleSerializerEntry<'a, 'py>) -> Result<(), E>,
    ) -> PyResult<Result<(), E>> {
        let n_items = tuple.len();

        if state.check != SerCheck::None && n_items != self.serializers.len() {
            return Err(PydanticSerializationUnexpectedValue::new_from_msg(Some(format!(
                "Expected {} items, but got {}",
                self.serializers.len(),
                n_items
            )))
            .to_py_err());
        }

        let mut py_tuple_iter = tuple.iter();

        for (index, serializer) in self.serializers.iter().enumerate() {
            let Some(element) = py_tuple_iter.next() else {
                state
                    .warnings
                    .register_warning(PydanticSerializationUnexpectedValue::new_from_msg(Some(
                        "Unexpected too few items present in named tuple".to_string(),
                    )));
                break;
            };
            if let Some(next_include_exclude) = self.filter.index_filter(index, state, Some(n_items))? {
                let state = &mut state.scoped_include_exclude(next_include_exclude);
                if let Err(e) = f(NamedTupleSerializerEntry {
                    item: element,
                    serializer,
                    state,
                }) {
                    return Ok(Err(e));
                }
            }
        }

        if py_tuple_iter.next().is_some() {
            state
                .warnings
                .register_warning(PydanticSerializationUnexpectedValue::new_from_msg(Some(
                    "Unexpected extra items present in named tuple".to_string(),
                )));
        }

        Ok(Ok(()))
    }
}
