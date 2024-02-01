use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyTuple};
use std::borrow::Cow;
use std::iter;

use serde::ser::SerializeSeq;

use crate::definitions::DefinitionsBuilder;
use crate::serializers::extra::SerCheck;
use crate::serializers::type_serializers::any::AnySerializer;
use crate::tools::SchemaDict;
use crate::PydanticSerializationUnexpectedValue;

use super::{
    infer_json_key, infer_serialize, infer_to_python, py_err_se_err, BuildSerializer, CombinedSerializer, Extra,
    PydanticSerializer, SchemaFilter, SerMode, TypeSerializer,
};

#[derive(Debug, Clone)]
pub struct TupleSerializer {
    serializers: Vec<CombinedSerializer>,
    variadic_item_index: Option<usize>,
    filter: SchemaFilter<usize>,
    name: String,
}

impl BuildSerializer for TupleSerializer {
    const EXPECTED_TYPE: &'static str = "tuple";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let py = schema.py();
        let items: &PyList = schema.get_as_req(intern!(py, "items_schema"))?;
        let serializers: Vec<CombinedSerializer> = items
            .iter()
            .map(|item| CombinedSerializer::build(item.downcast()?, config, definitions))
            .collect::<PyResult<_>>()?;

        let mut serializer_names = serializers.iter().map(TypeSerializer::get_name).collect::<Vec<_>>();
        let variadic_item_index: Option<usize> = schema.get_as(intern!(py, "variadic_item_index"))?;
        if let Some(variadic_item_index) = variadic_item_index {
            serializer_names.insert(variadic_item_index + 1, "...");
        }
        let name = format!("tuple[{}]", serializer_names.join(", "));

        Ok(Self {
            serializers,
            variadic_item_index,
            filter: SchemaFilter::from_schema(schema)?,
            name,
        }
        .into())
    }
}

impl_py_gc_traverse!(TupleSerializer { serializers });

impl TypeSerializer for TupleSerializer {
    fn to_python(
        &self,
        value: &PyAny,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        match value.downcast::<PyTuple>() {
            Ok(py_tuple) => {
                let py = value.py();

                let n_items = py_tuple.len();
                let mut items = Vec::with_capacity(n_items);

                self.for_each_tuple_item_and_serializer(py_tuple, include, exclude, extra, |entry| {
                    entry
                        .serializer
                        .to_python(entry.item, entry.include, entry.exclude, extra)
                        .map(|item| items.push(item))
                })??;

                match extra.mode {
                    SerMode::Json => Ok(PyList::new(py, items).into_py(py)),
                    _ => Ok(PyTuple::new(py, items).into_py(py)),
                }
            }
            Err(_) => {
                extra.warnings.on_fallback_py(&self.name, value, extra)?;
                infer_to_python(value, include, exclude, extra)
            }
        }
    }

    fn json_key<'py>(&self, key: &'py PyAny, extra: &Extra) -> PyResult<Cow<'py, str>> {
        match key.downcast::<PyTuple>() {
            Ok(py_tuple) => {
                let mut key_builder = KeyBuilder::new();

                self.for_each_tuple_item_and_serializer(py_tuple, None, None, extra, |entry| {
                    entry
                        .serializer
                        .json_key(entry.item, extra)
                        .map(|key| key_builder.push(&key))
                })??;

                Ok(Cow::Owned(key_builder.finish()))
            }
            Err(_) => {
                extra.warnings.on_fallback_py(&self.name, key, extra)?;
                infer_json_key(key, extra)
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
        match value.downcast::<PyTuple>() {
            Ok(py_tuple) => {
                let py_tuple: &PyTuple = py_tuple.downcast().map_err(py_err_se_err)?;

                let n_items = py_tuple.len();
                let mut seq = serializer.serialize_seq(Some(n_items))?;

                self.for_each_tuple_item_and_serializer(py_tuple, include, exclude, extra, |entry| {
                    seq.serialize_element(&PydanticSerializer::new(
                        entry.item,
                        entry.serializer,
                        entry.include,
                        entry.exclude,
                        extra,
                    ))
                })
                .map_err(py_err_se_err)??;

                seq.end()
            }
            Err(_) => {
                extra.warnings.on_fallback_ser::<S>(&self.name, value, extra)?;
                infer_serialize(value, serializer, include, exclude, extra)
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

struct TupleSerializerEntry<'a, 'py> {
    item: &'py PyAny,
    include: Option<&'py PyAny>,
    exclude: Option<&'py PyAny>,
    serializer: &'a CombinedSerializer,
}

impl TupleSerializer {
    /// Try to serialize each item in the tuple with the corresponding serializer.
    ///
    /// If the tuple doesn't match the length of the serializer, in strict mode, an error is returned.
    ///
    /// The error type E is the type of the error returned by the closure, which is why there are two
    /// levels of `Result`.
    fn for_each_tuple_item_and_serializer<E>(
        &self,
        tuple: &PyTuple,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
        mut f: impl for<'a, 'py> FnMut(TupleSerializerEntry<'a, 'py>) -> Result<(), E>,
    ) -> PyResult<Result<(), E>> {
        let n_items = tuple.len();
        let mut py_tuple_iter = tuple.iter();

        macro_rules! use_serializers {
            ($serializers_iter:expr) => {
                for (index, serializer) in $serializers_iter.enumerate() {
                    let element = match py_tuple_iter.next() {
                        Some(value) => value,
                        None => break,
                    };
                    let op_next = self.filter.index_filter(index, include, exclude, Some(n_items))?;
                    if let Some((next_include, next_exclude)) = op_next {
                        if let Err(e) = f(TupleSerializerEntry {
                            item: element,
                            include: next_include,
                            exclude: next_exclude,
                            serializer,
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
        } else if extra.check == SerCheck::Strict && n_items != self.serializers.len() {
            return Err(PydanticSerializationUnexpectedValue::new_err(Some(format!(
                "Expected {} items, but got {}",
                self.serializers.len(),
                n_items
            ))));
        } else {
            use_serializers!(self.serializers.iter());
            let mut warned = false;
            for (i, element) in py_tuple_iter.enumerate() {
                if !warned {
                    extra
                        .warnings
                        .custom_warning("Unexpected extra items present in tuple".to_string());
                    warned = true;
                }
                let op_next = self
                    .filter
                    .index_filter(i + self.serializers.len(), include, exclude, Some(n_items))?;
                if let Some((next_include, next_exclude)) = op_next {
                    if let Err(e) = f(TupleSerializerEntry {
                        item: element,
                        include: next_include,
                        exclude: next_exclude,
                        serializer: &CombinedSerializer::Any(AnySerializer),
                    }) {
                        return Ok(Err(e));
                    };
                }
            }
        };
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
