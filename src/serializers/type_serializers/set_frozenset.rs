use std::borrow::Cow;
use std::sync::Arc;

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyFrozenSet, PyList, PySet};
use pyo3::{intern, IntoPyObjectExt};

use serde::ser::SerializeSeq;

use crate::definitions::DefinitionsBuilder;
use crate::serializers::SerializationState;
use crate::tools::SchemaDict;

use super::any::AnySerializer;
use super::{
    infer_serialize, infer_to_python, BuildSerializer, CombinedSerializer, Extra, PydanticSerializer, SerMode,
    TypeSerializer,
};

macro_rules! build_serializer {
    ($struct_name:ident, $expected_type:literal, $py_type:ty) => {
        #[derive(Debug)]
        pub struct $struct_name {
            item_serializer: Arc<CombinedSerializer>,
            name: String,
        }

        impl BuildSerializer for $struct_name {
            const EXPECTED_TYPE: &'static str = $expected_type;

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
                        name,
                    }
                    .into(),
                ))
            }
        }

        impl_py_gc_traverse!($struct_name { item_serializer });

        impl TypeSerializer for $struct_name {
            fn to_python<'py>(
                &self,
                value: &Bound<'py, PyAny>,
                state: &mut SerializationState<'py>,
                extra: &Extra<'_, 'py>,
            ) -> PyResult<Py<PyAny>> {
                let py = value.py();
                match value.downcast::<$py_type>() {
                    Ok(py_set) => {
                        let item_serializer = self.item_serializer.as_ref();

                        let mut items = Vec::with_capacity(py_set.len());
                        for element in py_set.iter() {
                            items.push(item_serializer.to_python(&element, state, extra)?);
                        }
                        match extra.mode {
                            SerMode::Json => Ok(PyList::new(py, items)?.into()),
                            _ => <$py_type>::new(py, &items)?.into_py_any(py),
                        }
                    }
                    Err(_) => {
                        state.warn_fallback_py(self.get_name(), value)?;
                        infer_to_python(value, state, extra)
                    }
                }
            }

            fn json_key<'a, 'py>(
                &self,
                key: &'a Bound<'py, PyAny>,
                state: &mut SerializationState<'py>,
                extra: &Extra<'_, 'py>,
            ) -> PyResult<Cow<'a, str>> {
                self.invalid_as_json_key(key, state, extra, Self::EXPECTED_TYPE)
            }

            fn serde_serialize<'py, S: serde::ser::Serializer>(
                &self,
                value: &Bound<'py, PyAny>,
                serializer: S,
                state: &mut SerializationState<'py>,
                extra: &Extra<'_, 'py>,
            ) -> Result<S::Ok, S::Error> {
                match value.downcast::<$py_type>() {
                    Ok(py_set) => {
                        let mut seq = serializer.serialize_seq(Some(py_set.len()))?;
                        let item_serializer = self.item_serializer.as_ref();

                        for value in py_set.iter() {
                            let item_serialize = PydanticSerializer::new(&value, item_serializer, state, extra);
                            seq.serialize_element(&item_serialize)?;
                        }
                        seq.end()
                    }
                    Err(_) => {
                        state.warn_fallback_ser::<S>(self.get_name(), value)?;
                        infer_serialize(value, serializer, state, extra)
                    }
                }
            }

            fn get_name(&self) -> &str {
                &self.name
            }
        }
    };
}

build_serializer!(SetSerializer, "set", PySet);
build_serializer!(FrozenSetSerializer, "frozenset", PyFrozenSet);
