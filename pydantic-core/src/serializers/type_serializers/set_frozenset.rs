use std::borrow::Cow;
use std::sync::Arc;

use pyo3::exceptions::PyTypeError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyFrozenSet, PyList, PySet};
use pyo3::{IntoPyObjectExt, intern};

use serde::ser::SerializeSeq;

use crate::definitions::DefinitionsBuilder;
use crate::serializers::SerializationState;
use crate::serializers::errors::py_err_se_err;
use crate::serializers::extra::IncludeExclude;
use crate::serializers::filter::{FilterLogic, SchemaFilter};
use crate::tools::SchemaDict;

use super::any::AnySerializer;
use super::{
    BuildSerializer, CombinedSerializer, PydanticSerializer, SerMode, TypeSerializer, infer_serialize, infer_to_python,
};

/// Sets have no stable indices: only an all-items filter is meaningful.
pub(crate) fn set_filter<'py>(state: &SerializationState<'py>) -> PyResult<Option<IncludeExclude<'py>>> {
    let py = state.py();
    let all = intern!(py, "__all__");
    for filter in [state.include(), state.exclude()].into_iter().flatten() {
        if filter.is_none() {
            continue;
        }
        let invalid_filter =
            || PyTypeError::new_err("Set include/exclude filters must be a set or dict containing only '__all__'");
        if let Ok(dict) = filter.cast::<PyDict>() {
            for key in dict.keys().iter() {
                if !key.eq(all)? {
                    return Err(invalid_filter());
                }
            }
        } else if let Ok(set) = filter.cast::<PySet>() {
            for key in set.iter() {
                if !key.eq(all)? {
                    return Err(invalid_filter());
                }
            }
        } else {
            return Err(invalid_filter());
        }
    }
    SchemaFilter::<usize>::default().filter(all, 0, state.include(), state.exclude())
}

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
            ) -> PyResult<Py<PyAny>> {
                let py = value.py();
                match value.cast::<$py_type>() {
                    Ok(py_set) => {
                        let item_serializer = self.item_serializer.as_ref();

                        let mut items = Vec::with_capacity(py_set.len());
                        if let Some(filters) = set_filter(state)? {
                            let state = &mut state.scoped_include_exclude(filters);
                            for element in py_set.iter() {
                                items.push(item_serializer.to_python(&element, state)?);
                            }
                        }
                        match state.extra.mode {
                            SerMode::Json => Ok(PyList::new(py, items)?.into()),
                            _ => <$py_type>::new(py, &items)?.into_py_any(py),
                        }
                    }
                    Err(_) => {
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
                match value.cast::<$py_type>() {
                    Ok(py_set) => {
                        let filters = set_filter(state).map_err(py_err_se_err)?;
                        let mut seq =
                            serializer.serialize_seq(Some(if filters.is_some() { py_set.len() } else { 0 }))?;
                        let item_serializer = self.item_serializer.as_ref();
                        if let Some(filters) = filters {
                            let state = &mut state.scoped_include_exclude(filters);
                            for value in py_set.iter() {
                                let item_serialize = PydanticSerializer::new(&value, item_serializer, state);
                                seq.serialize_element(&item_serialize)?;
                            }
                        }
                        seq.end()
                    }
                    Err(_) => {
                        state.warn_fallback_ser::<S>(self.get_name(), value)?;
                        infer_serialize(value, serializer, state)
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
