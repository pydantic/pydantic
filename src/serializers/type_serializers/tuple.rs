use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyTuple};

use serde::ser::SerializeSeq;

use crate::build_context::BuildContext;
use crate::build_tools::SchemaDict;

use super::any::{fallback_serialize, fallback_to_python, AnySerializer};
use super::{
    py_err_se_err, BuildSerializer, CombinedSerializer, Extra, PydanticSerializer, SchemaFilter, SerMode,
    TypeSerializer,
};

pub struct TupleBuilder;

impl BuildSerializer for TupleBuilder {
    const EXPECTED_TYPE: &'static str = "tuple";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        match schema.get_as::<&str>(intern!(schema.py(), "mode"))? {
            Some("positional") => TuplePositionalSerializer::build(schema, config, build_context),
            _ => TupleVariableSerializer::build(schema, config, build_context),
        }
    }
}

#[derive(Debug, Clone)]
pub struct TupleVariableSerializer {
    item_serializer: Box<CombinedSerializer>,
    filter: SchemaFilter<usize>,
}

impl TupleVariableSerializer {
    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let py = schema.py();
        if let Some("positional") = schema.get_as::<&str>(intern!(py, "mode"))? {
            return TuplePositionalSerializer::build(schema, config, build_context);
        }
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

impl TypeSerializer for TupleVariableSerializer {
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
                let item_serializer = self.item_serializer.as_ref();

                let mut items = Vec::with_capacity(py_tuple.len());
                for (index, element) in py_tuple.iter().enumerate() {
                    let op_next = self.filter.value_filter(index, include, exclude)?;
                    if let Some((next_include, next_exclude)) = op_next {
                        items.push(item_serializer.to_python(element, next_include, next_exclude, extra)?);
                    }
                }
                match extra.mode {
                    SerMode::Json => Ok(PyList::new(py, items).into_py(py)),
                    _ => Ok(PyTuple::new(py, items).into_py(py)),
                }
            }
            Err(_) => {
                extra.warnings.fallback_filtering("tuple", value);
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
        match value.downcast::<PyTuple>() {
            Ok(py_tuple) => {
                let py_tuple: &PyTuple = py_tuple.downcast().map_err(py_err_se_err)?;
                let item_serializer = self.item_serializer.as_ref();

                let mut seq = serializer.serialize_seq(Some(py_tuple.len()))?;
                for (index, element) in py_tuple.iter().enumerate() {
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
                extra.warnings.fallback_filtering("tuple", value);
                fallback_serialize(value, serializer, include, exclude, extra)
            }
        }
    }
}

#[derive(Debug, Clone)]
pub struct TuplePositionalSerializer {
    items_serializers: Vec<CombinedSerializer>,
    extra_serializer: Box<CombinedSerializer>,
    filter: SchemaFilter<usize>,
}

impl TuplePositionalSerializer {
    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let py = schema.py();
        let items: &PyList = schema.get_as_req(intern!(py, "items_schema"))?;

        let extra_serializer = match schema.get_as::<&PyDict>(intern!(py, "extra_schema"))? {
            Some(extra_schema) => CombinedSerializer::build(extra_schema, config, build_context)?,
            None => AnySerializer::build(schema, config, build_context)?,
        };
        Ok(Self {
            items_serializers: items
                .iter()
                .map(|item| CombinedSerializer::build(item.downcast()?, config, build_context))
                .collect::<PyResult<_>>()?,
            extra_serializer: Box::new(extra_serializer),
            filter: SchemaFilter::from_schema(schema)?,
        }
        .into())
    }
}

impl TypeSerializer for TuplePositionalSerializer {
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

                let mut py_tuple_iter = py_tuple.iter();
                let mut items = Vec::with_capacity(py_tuple.len());
                for (index, serializer) in self.items_serializers.iter().enumerate() {
                    let element = match py_tuple_iter.next() {
                        Some(value) => value,
                        None => break,
                    };
                    let op_next = self.filter.value_filter(index, include, exclude)?;
                    if let Some((next_include, next_exclude)) = op_next {
                        items.push(serializer.to_python(element, next_include, next_exclude, extra)?);
                    }
                }
                let expected_length = self.items_serializers.len();
                let extra_serializer = self.extra_serializer.as_ref();
                for (index2, element) in py_tuple_iter.enumerate() {
                    let index = index2 + expected_length;
                    let op_next = self.filter.value_filter(index, include, exclude)?;
                    if let Some((next_include, next_exclude)) = op_next {
                        items.push(extra_serializer.to_python(element, next_include, next_exclude, extra)?);
                    }
                }

                match extra.mode {
                    SerMode::Json => Ok(PyList::new(py, items).into_py(py)),
                    _ => Ok(PyTuple::new(py, items).into_py(py)),
                }
            }
            Err(_) => {
                extra.warnings.fallback_filtering("tuple", value);
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
        match value.downcast::<PyTuple>() {
            Ok(py_tuple) => {
                let py_tuple: &PyTuple = py_tuple.downcast().map_err(py_err_se_err)?;

                let mut py_tuple_iter = py_tuple.iter();
                let mut seq = serializer.serialize_seq(Some(py_tuple.len()))?;
                for (index, serializer) in self.items_serializers.iter().enumerate() {
                    let element = match py_tuple_iter.next() {
                        Some(value) => value,
                        None => break,
                    };
                    let op_next = self
                        .filter
                        .value_filter(index, include, exclude)
                        .map_err(py_err_se_err)?;
                    if let Some((next_include, next_exclude)) = op_next {
                        let item_serialize =
                            PydanticSerializer::new(element, serializer, next_include, next_exclude, extra);
                        seq.serialize_element(&item_serialize)?;
                    }
                }

                let expected_length = self.items_serializers.len();
                let extra_serializer = self.extra_serializer.as_ref();
                for (index2, element) in py_tuple_iter.enumerate() {
                    let index = index2 + expected_length;
                    let op_next = self
                        .filter
                        .value_filter(index, include, exclude)
                        .map_err(py_err_se_err)?;
                    if let Some((next_include, next_exclude)) = op_next {
                        let item_serialize =
                            PydanticSerializer::new(element, extra_serializer, next_include, next_exclude, extra);
                        seq.serialize_element(&item_serialize)?;
                    }
                }

                seq.end()
            }
            Err(_) => {
                extra.warnings.fallback_filtering("tuple", value);
                fallback_serialize(value, serializer, include, exclude, extra)
            }
        }
    }
}
