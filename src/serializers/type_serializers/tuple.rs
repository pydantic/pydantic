use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyTuple};
use std::borrow::Cow;
use std::iter;

use serde::ser::SerializeSeq;

use crate::definitions::DefinitionsBuilder;
use crate::serializers::type_serializers::any::AnySerializer;
use crate::tools::SchemaDict;

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
                let mut py_tuple_iter = py_tuple.iter();
                let mut items = Vec::with_capacity(n_items);

                macro_rules! use_serializers {
                    ($serializers_iter:expr) => {
                        for (index, serializer) in $serializers_iter.enumerate() {
                            let element = match py_tuple_iter.next() {
                                Some(value) => value,
                                None => break,
                            };
                            let op_next = self
                                .filter
                                .index_filter(index, include, exclude, Some(n_items))?;
                            if let Some((next_include, next_exclude)) = op_next {
                                items.push(serializer.to_python(element, next_include, next_exclude, extra)?);
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
                        let op_next =
                            self.filter
                                .index_filter(i + self.serializers.len(), include, exclude, Some(n_items))?;
                        if let Some((next_include, next_exclude)) = op_next {
                            items.push(AnySerializer.to_python(element, next_include, next_exclude, extra)?);
                        }
                    }
                };

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
                let mut py_tuple_iter = py_tuple.iter();

                let mut key_builder = KeyBuilder::new();

                let n_items = py_tuple.len();

                macro_rules! use_serializers {
                    ($serializers_iter:expr) => {
                        for serializer in $serializers_iter {
                            let element = match py_tuple_iter.next() {
                                Some(value) => value,
                                None => break,
                            };
                            key_builder.push(&serializer.json_key(element, extra)?);
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
                } else {
                    use_serializers!(self.serializers.iter());
                };

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
                let mut py_tuple_iter = py_tuple.iter();
                let mut seq = serializer.serialize_seq(Some(n_items))?;

                macro_rules! use_serializers {
                    ($serializers_iter:expr) => {
                        for (index, serializer) in $serializers_iter.enumerate() {
                            let element = match py_tuple_iter.next() {
                                Some(value) => value,
                                None => break,
                            };
                            let op_next = self
                                .filter
                                .index_filter(index, include, exclude, Some(n_items))
                                .map_err(py_err_se_err)?;
                            if let Some((next_include, next_exclude)) = op_next {
                                let item_serialize =
                                    PydanticSerializer::new(element, serializer, next_include, next_exclude, extra);
                                seq.serialize_element(&item_serialize)?;
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
                            .index_filter(i + self.serializers.len(), include, exclude, Some(n_items))
                            .map_err(py_err_se_err)?;
                        if let Some((next_include, next_exclude)) = op_next {
                            let item_serialize = PydanticSerializer::new(
                                element,
                                &CombinedSerializer::Any(AnySerializer),
                                next_include,
                                next_exclude,
                                extra,
                            );
                            seq.serialize_element(&item_serialize)?;
                        }
                    }
                };

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
