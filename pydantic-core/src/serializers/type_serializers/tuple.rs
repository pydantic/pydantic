use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyTuple};
use std::borrow::Cow;
use std::iter;
use std::sync::Arc;

use serde::ser::SerializeSeq;

use crate::definitions::DefinitionsBuilder;
use crate::serializers::extra::SerCheck;
use crate::serializers::type_serializers::any::AnySerializer;
use crate::serializers::SerializationState;
use crate::tools::SchemaDict;
use crate::PydanticSerializationUnexpectedValue;

use super::{
    infer_json_key, infer_serialize, infer_to_python, py_err_se_err, BuildSerializer, CombinedSerializer,
    PydanticSerializer, SchemaFilter, SerMode, TypeSerializer,
};

#[derive(Debug)]
pub struct TupleSerializer {
    serializers: Vec<Arc<CombinedSerializer>>,
    variadic_item_index: Option<usize>,
    filter: SchemaFilter<usize>,
    name: String,
}

impl BuildSerializer for TupleSerializer {
    const EXPECTED_TYPE: &'static str = "tuple";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        let py = schema.py();
        let items: Bound<'_, PyList> = schema.get_as_req(intern!(py, "items_schema"))?;
        let serializers: Vec<Arc<CombinedSerializer>> = items
            .iter()
            .map(|item| CombinedSerializer::build(item.downcast()?, config, definitions))
            .collect::<PyResult<_>>()?;

        let mut serializer_names = serializers.iter().map(|v| v.get_name()).collect::<Vec<_>>();
        let variadic_item_index: Option<usize> = schema.get_as(intern!(py, "variadic_item_index"))?;
        if let Some(variadic_item_index) = variadic_item_index {
            serializer_names.insert(variadic_item_index + 1, "...");
        }
        let name = format!("tuple[{}]", serializer_names.join(", "));

        Ok(CombinedSerializer::Tuple(Self {
            serializers,
            variadic_item_index,
            filter: SchemaFilter::from_schema(schema)?,
            name,
        })
        .into())
    }
}

impl_py_gc_traverse!(TupleSerializer { serializers });

impl TypeSerializer for TupleSerializer {
    fn to_python<'py>(
        &self,
        value: &Bound<'py, PyAny>,
        state: &mut SerializationState<'_, 'py>,
    ) -> PyResult<Py<PyAny>> {
        match value.downcast::<PyTuple>() {
            Ok(py_tuple) => {
                let py = value.py();

                let n_items = py_tuple.len();
                let mut items = Vec::with_capacity(n_items);

                self.for_each_tuple_item_and_serializer(py_tuple, state, |entry| {
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
            Err(_) => {
                state.warn_fallback_py(&self.name, value)?;
                infer_to_python(value, state)
            }
        }
    }

    fn json_key<'a, 'py>(
        &self,
        key: &'a Bound<'py, PyAny>,
        state: &mut SerializationState<'_, 'py>,
    ) -> PyResult<Cow<'a, str>> {
        match key.downcast::<PyTuple>() {
            Ok(py_tuple) => {
                let mut key_builder = KeyBuilder::new();

                let state = &mut state.scoped_include_exclude(None, None);
                self.for_each_tuple_item_and_serializer(py_tuple, state, |entry| {
                    entry
                        .serializer
                        .json_key(&entry.item, entry.state)
                        .map(|key| key_builder.push(&key))
                })??;

                Ok(Cow::Owned(key_builder.finish()))
            }
            Err(_) => {
                state.warn_fallback_py(&self.name, key)?;
                infer_json_key(key, state)
            }
        }
    }

    fn serde_serialize<'py, S: serde::ser::Serializer>(
        &self,
        value: &Bound<'py, PyAny>,
        serializer: S,
        state: &mut SerializationState<'_, 'py>,
    ) -> Result<S::Ok, S::Error> {
        match value.downcast::<PyTuple>() {
            Ok(py_tuple) => {
                let py_tuple = py_tuple.downcast::<PyTuple>().map_err(py_err_se_err)?;

                let n_items = py_tuple.len();
                let mut seq = serializer.serialize_seq(Some(n_items))?;

                self.for_each_tuple_item_and_serializer(py_tuple, state, |entry| {
                    seq.serialize_element(&PydanticSerializer::new(&entry.item, entry.serializer, entry.state))
                })
                .map_err(py_err_se_err)??;

                seq.end()
            }
            Err(_) => {
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

struct TupleSerializerEntry<'a, 'b, 'py> {
    item: Bound<'py, PyAny>,
    serializer: &'a CombinedSerializer,
    state: &'a mut SerializationState<'b, 'py>,
}

impl TupleSerializer {
    /// Try to serialize each item in the tuple with the corresponding serializer.
    ///
    /// If the tuple doesn't match the length of the serializer, in strict mode, an error is returned.
    ///
    /// The error type E is the type of the error returned by the closure, which is why there are two
    /// levels of `Result`.
    fn for_each_tuple_item_and_serializer<'py, E>(
        &self,
        tuple: &Bound<'py, PyTuple>,
        state: &mut SerializationState<'_, 'py>,
        mut f: impl for<'a, 'b> FnMut(TupleSerializerEntry<'a, 'b, 'py>) -> Result<(), E>,
    ) -> PyResult<Result<(), E>> {
        let n_items = tuple.len();
        let mut py_tuple_iter = tuple.iter();

        macro_rules! use_serializers {
            ($serializers_iter:expr) => {
                for (index, serializer) in $serializers_iter.enumerate() {
                    let Some(element) = py_tuple_iter.next() else {
                        break;
                    };
                    let op_next = self.filter.index_filter(index, state, Some(n_items))?;
                    if let Some((next_include, next_exclude)) = op_next {
                        let state = &mut state.scoped_include_exclude(next_include, next_exclude);
                        if let Err(e) = f(TupleSerializerEntry {
                            item: element,
                            serializer,
                            state,
                        }) {
                            return Ok(Err(e));
                        };
                    }
                }
            };
        }

        if let Some(variadic_item_index) = self.variadic_item_index {
            // Need `saturating_sub` to handle items with too few elements without panicking
            let n_variadic_items = (n_items + 1).saturating_sub(self.serializers.len());
            let serializers_iter = self.serializers[..variadic_item_index]
                .iter()
                .chain(iter::repeat(&self.serializers[variadic_item_index]).take(n_variadic_items))
                .chain(self.serializers[variadic_item_index + 1..].iter());
            use_serializers!(serializers_iter);
        } else if state.check == SerCheck::Strict && n_items != self.serializers.len() {
            return Err(PydanticSerializationUnexpectedValue::new_from_msg(Some(format!(
                "Expected {} items, but got {}",
                self.serializers.len(),
                n_items
            )))
            .to_py_err());
        } else {
            use_serializers!(self.serializers.iter());
            let mut warned = false;
            for (i, element) in py_tuple_iter.enumerate() {
                if !warned {
                    state
                        .warnings
                        .register_warning(PydanticSerializationUnexpectedValue::new_from_msg(Some(
                            "Unexpected extra items present in tuple".to_string(),
                        )));
                    warned = true;
                }
                let op_next = self
                    .filter
                    .index_filter(i + self.serializers.len(), state, Some(n_items))?;
                if let Some((next_include, next_exclude)) = op_next {
                    let state = &mut state.scoped_include_exclude(next_include, next_exclude);
                    if let Err(e) = f(TupleSerializerEntry {
                        item: element,
                        serializer: &CombinedSerializer::Any(AnySerializer),
                        state,
                    }) {
                        return Ok(Err(e));
                    }
                }
            }
        }
        Ok(Ok(()))
    }
}

pub(crate) struct KeyBuilder {
    key: String,
    first: bool,
}

impl KeyBuilder {
    pub fn new() -> Self {
        Self {
            key: String::with_capacity(31),
            first: true,
        }
    }

    pub fn push(&mut self, key: &str) {
        if self.first {
            self.first = false;
        } else {
            self.key.push(',');
        }
        self.key.push_str(key);
    }

    pub fn finish(self) -> String {
        self.key
    }
}
