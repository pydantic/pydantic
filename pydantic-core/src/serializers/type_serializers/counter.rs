use std::borrow::Cow;
use std::sync::Arc;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use pyo3::IntoPyObjectExt;
use serde::ser::SerializeMap;

use crate::common::counter::get_counter_type;
use crate::definitions::DefinitionsBuilder;
use crate::serializers::SerializationState;
use crate::serializers::extra::IncludeExclude;
use crate::tools::SchemaDict;

use super::any::AnySerializer;
use super::{
    BuildSerializer, CombinedSerializer, PydanticSerializer, SchemaFilter, SerMode, TypeSerializer, infer_serialize,
    infer_to_python, py_err_se_err,
};

#[derive(Debug)]
pub struct CounterSerializer {
    key_serializer: Arc<CombinedSerializer>,
    value_serializer: Arc<CombinedSerializer>,
    // isize because we look up include exclude via `.hash()` which returns an isize
    filter: SchemaFilter<isize>,
    name: String,
}

impl BuildSerializer for CounterSerializer {
    const EXPECTED_TYPE: &'static str = "counter";

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
        Ok(CombinedSerializer::Counter(Self {
            key_serializer,
            value_serializer,
            filter,
            name,
        })
        .into())
    }
}

impl_py_gc_traverse!(CounterSerializer {
    key_serializer,
    value_serializer
});

/// Returns `value` as a dict if it is a `collections.Counter` instance.
///
/// Unlike `OrderedDict`, a `Counter` can safely be iterated over using the `dict` C API.
fn as_counter<'a, 'py>(value: &'a Bound<'py, PyAny>) -> PyResult<Option<&'a Bound<'py, PyDict>>> {
    if value.is_instance(get_counter_type(value.py())?)? {
        Ok(Some(value.cast::<PyDict>()?))
    } else {
        Ok(None)
    }
}

impl TypeSerializer for CounterSerializer {
    fn to_python<'py>(&self, value: &Bound<'py, PyAny>, state: &mut SerializationState<'py>) -> PyResult<Py<PyAny>> {
        let py = value.py();
        match as_counter(value)? {
            Some(py_dict) => {
                let value_serializer = self.value_serializer.as_ref();

                let new_dict = PyDict::new(py);
                for (key, value) in py_dict.iter() {
                    if let Some(next_include_exclude) = self.filter.key_filter(&key, state)? {
                        let key = {
                            // disable include/exclude for keys
                            let state = &mut state.scoped_include_exclude(IncludeExclude::empty());
                            match state.extra.mode {
                                SerMode::Json => self.key_serializer.json_key(&key, state)?.into_py_any(py)?,
                                _ => self.key_serializer.to_python(&key, state)?,
                            }
                        };
                        let state = &mut state.scoped_include_exclude(next_include_exclude);
                        let value = value_serializer.to_python(&value, state)?;
                        new_dict.set_item(key, value)?;
                    }
                }
                match state.extra.mode {
                    SerMode::Json => Ok(new_dict.into()),
                    _ => Ok(get_counter_type(py)?.call1((new_dict,))?.unbind()),
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
        match as_counter(value).map_err(py_err_se_err)? {
            Some(py_dict) => {
                let mut map = serializer.serialize_map(Some(py_dict.len()))?;
                let key_serializer = self.key_serializer.as_ref();
                let value_serializer = self.value_serializer.as_ref();

                for (key, value) in py_dict.iter() {
                    if let Some(next_include_exclude) = self.filter.key_filter(&key, state).map_err(py_err_se_err)? {
                        let state = &mut state.scoped_include_exclude(next_include_exclude);
                        let key = key_serializer.json_key(&key, state).map_err(py_err_se_err)?;
                        let value_serialize = PydanticSerializer::new(&value, value_serializer, state);
                        map.serialize_entry(&key, &value_serialize)?;
                    }
                }
                map.end()
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
}
