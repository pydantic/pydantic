use std::borrow::Cow;
use std::sync::Arc;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use pyo3::IntoPyObjectExt;
use serde::ser::SerializeMap;

use crate::definitions::DefinitionsBuilder;
use crate::serializers::SerializationState;
use crate::tools::SchemaDict;

use super::any::AnySerializer;
use super::{
    infer_serialize, infer_to_python, py_err_se_err, BuildSerializer, CombinedSerializer, Extra, PydanticSerializer,
    SchemaFilter, SerMode, TypeSerializer,
};

#[derive(Debug)]
pub struct DictSerializer {
    key_serializer: Arc<CombinedSerializer>,
    value_serializer: Arc<CombinedSerializer>,
    // isize because we look up include exclude via `.hash()` which returns an isize
    filter: SchemaFilter<isize>,
    name: String,
}

impl BuildSerializer for DictSerializer {
    const EXPECTED_TYPE: &'static str = "dict";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        let py = schema.py();
        let key_serializer = match schema.get_as(intern!(py, "keys_schema"))? {
            Some(items_schema) => CombinedSerializer::build(&items_schema, config, definitions)?,
            None => AnySerializer::build(schema, config, definitions)?,
        };
        let value_serializer = match schema.get_as(intern!(py, "values_schema"))? {
            Some(items_schema) => CombinedSerializer::build(&items_schema, config, definitions)?,
            None => AnySerializer::build(schema, config, definitions)?,
        };
        let filter = match schema.get_as::<Bound<'_, PyDict>>(intern!(py, "serialization"))? {
            Some(ser) => {
                let include = ser.get_item(intern!(py, "include"))?;
                let exclude = ser.get_item(intern!(py, "exclude"))?;
                SchemaFilter::from_set_hash(include.as_ref(), exclude.as_ref())?
            }
            None => SchemaFilter::default(),
        };
        let name = format!(
            "{}[{}, {}]",
            Self::EXPECTED_TYPE,
            key_serializer.get_name(),
            value_serializer.get_name()
        );
        Ok(CombinedSerializer::Dict(Self {
            key_serializer,
            value_serializer,
            filter,
            name,
        })
        .into())
    }
}

impl_py_gc_traverse!(DictSerializer {
    key_serializer,
    value_serializer
});

impl TypeSerializer for DictSerializer {
    fn to_python<'py>(
        &self,
        value: &Bound<'py, PyAny>,
        state: &mut SerializationState<'py>,
        extra: &Extra<'_, 'py>,
    ) -> PyResult<Py<PyAny>> {
        let py = value.py();
        match value.downcast::<PyDict>() {
            Ok(py_dict) => {
                let value_serializer = self.value_serializer.as_ref();

                let new_dict = PyDict::new(py);
                for (key, value) in py_dict.iter() {
                    let op_next = self.filter.key_filter(&key, state)?;
                    if let Some((next_include, next_exclude)) = op_next {
                        let key = {
                            // disable include/exclude for keys
                            let state = &mut state.scoped_include_exclude(None, None);
                            match extra.mode {
                                SerMode::Json => self.key_serializer.json_key(&key, state, extra)?.into_py_any(py)?,
                                _ => self.key_serializer.to_python(&key, state, extra)?,
                            }
                        };
                        let state = &mut state.scoped_include_exclude(next_include, next_exclude);
                        let value = value_serializer.to_python(&value, state, extra)?;
                        new_dict.set_item(key, value)?;
                    }
                }
                Ok(new_dict.into())
            }
            Err(_) => {
                state.warn_fallback_py(self.get_name(), value, extra)?;
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
        match value.downcast::<PyDict>() {
            Ok(py_dict) => {
                let mut map = serializer.serialize_map(Some(py_dict.len()))?;
                let key_serializer = self.key_serializer.as_ref();
                let value_serializer = self.value_serializer.as_ref();

                for (key, value) in py_dict.iter() {
                    let op_next = self.filter.key_filter(&key, state).map_err(py_err_se_err)?;
                    if let Some((next_include, next_exclude)) = op_next {
                        let state = &mut state.scoped_include_exclude(next_include, next_exclude);
                        let key = key_serializer.json_key(&key, state, extra).map_err(py_err_se_err)?;
                        let value_serialize = PydanticSerializer::new(&value, value_serializer, state, extra);
                        map.serialize_entry(&key, &value_serialize)?;
                    }
                }
                map.end()
            }
            Err(_) => {
                state.warn_fallback_ser::<S>(self.get_name(), value, extra)?;
                infer_serialize(value, serializer, state, extra)
            }
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}
