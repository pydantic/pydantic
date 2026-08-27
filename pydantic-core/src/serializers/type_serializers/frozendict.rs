use std::borrow::Cow;
use std::sync::Arc;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyMapping};

use pyo3::IntoPyObjectExt;
use serde::ser::SerializeMap;

use crate::build_tools::py_schema_err;
use crate::common::frozendict::get_frozendict_type;
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
pub struct FrozenDictSerializer {
    key_serializer: Arc<CombinedSerializer>,
    value_serializer: Arc<CombinedSerializer>,
    // isize because we look up include exclude via `.hash()` which returns an isize
    filter: SchemaFilter<isize>,
    name: String,
}

impl BuildSerializer for FrozenDictSerializer {
    const EXPECTED_TYPE: &'static str = "frozendict";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        let py = schema.py();
        if get_frozendict_type(py).is_err() {
            return py_schema_err!("The `frozendict` builtin type is only available on Python 3.15 and above");
        }
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
        Ok(CombinedSerializer::FrozenDict(Self {
            key_serializer,
            value_serializer,
            filter,
            name,
        })
        .into())
    }
}

impl_py_gc_traverse!(FrozenDictSerializer {
    key_serializer,
    value_serializer
});

fn as_frozendict<'py>(value: &Bound<'py, PyAny>) -> Option<Bound<'py, PyMapping>> {
    match get_frozendict_type(value.py()) {
        Ok(frozendict_type) if value.is_instance(frozendict_type).unwrap_or(false) => {
            value.cast::<PyMapping>().ok().map(Bound::to_owned)
        }
        _ => None,
    }
}

impl TypeSerializer for FrozenDictSerializer {
    fn to_python<'py>(&self, value: &Bound<'py, PyAny>, state: &mut SerializationState<'py>) -> PyResult<Py<PyAny>> {
        let py = value.py();
        match as_frozendict(value) {
            Some(mapping) => {
                let value_serializer = self.value_serializer.as_ref();

                let new_dict = PyDict::new(py);
                for item in mapping.items()?.iter() {
                    let (key, value) = item.extract::<(Bound<PyAny>, Bound<PyAny>)>()?;
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
                    _ => Ok(get_frozendict_type(py)?.call1((new_dict,))?.unbind()),
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
        match as_frozendict(value) {
            Some(mapping) => {
                let items = mapping.items().map_err(py_err_se_err)?;
                let mut map = serializer.serialize_map(Some(items.len()))?;
                let key_serializer = self.key_serializer.as_ref();
                let value_serializer = self.value_serializer.as_ref();

                for item in items.iter() {
                    let (key, value) = item.extract::<(Bound<PyAny>, Bound<PyAny>)>().map_err(py_err_se_err)?;
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
