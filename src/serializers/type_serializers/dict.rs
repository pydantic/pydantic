use std::borrow::Cow;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use serde::ser::SerializeMap;

use crate::definitions::DefinitionsBuilder;
use crate::tools::SchemaDict;

use super::any::AnySerializer;
use super::{
    infer_serialize, infer_to_python, py_err_se_err, BuildSerializer, CombinedSerializer, Extra, PydanticSerializer,
    SchemaFilter, SerMode, TypeSerializer,
};

#[derive(Debug, Clone)]
pub struct DictSerializer {
    key_serializer: Box<CombinedSerializer>,
    value_serializer: Box<CombinedSerializer>,
    // isize because we look up include exclude via `.hash()` which returns an isize
    filter: SchemaFilter<isize>,
    name: String,
}

impl BuildSerializer for DictSerializer {
    const EXPECTED_TYPE: &'static str = "dict";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
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
        Ok(Self {
            key_serializer: Box::new(key_serializer),
            value_serializer: Box::new(value_serializer),
            filter,
            name,
        }
        .into())
    }
}

impl_py_gc_traverse!(DictSerializer {
    key_serializer,
    value_serializer
});

impl TypeSerializer for DictSerializer {
    fn to_python(
        &self,
        value: &Bound<'_, PyAny>,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        let py = value.py();
        match value.downcast::<PyDict>() {
            Ok(py_dict) => {
                let value_serializer = self.value_serializer.as_ref();

                let new_dict = PyDict::new_bound(py);
                for (key, value) in py_dict.iter() {
                    let op_next = self.filter.key_filter(&key, include, exclude)?;
                    if let Some((next_include, next_exclude)) = op_next {
                        let key = match extra.mode {
                            SerMode::Json => self.key_serializer.json_key(&key, extra)?.into_py(py),
                            _ => self.key_serializer.to_python(&key, None, None, extra)?,
                        };
                        let value =
                            value_serializer.to_python(&value, next_include.as_ref(), next_exclude.as_ref(), extra)?;
                        new_dict.set_item(key, value)?;
                    }
                }
                Ok(new_dict.into_py(py))
            }
            Err(_) => {
                extra.warnings.on_fallback_py(self.get_name(), value, extra)?;
                infer_to_python(value, include, exclude, extra)
            }
        }
    }

    fn json_key<'a>(&self, key: &'a Bound<'_, PyAny>, extra: &Extra) -> PyResult<Cow<'a, str>> {
        self._invalid_as_json_key(key, extra, Self::EXPECTED_TYPE)
    }

    fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        value: &Bound<'_, PyAny>,
        serializer: S,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> Result<S::Ok, S::Error> {
        match value.downcast::<PyDict>() {
            Ok(py_dict) => {
                let mut map = serializer.serialize_map(Some(py_dict.len()))?;
                let key_serializer = self.key_serializer.as_ref();
                let value_serializer = self.value_serializer.as_ref();

                for (key, value) in py_dict.iter() {
                    let op_next = self.filter.key_filter(&key, include, exclude).map_err(py_err_se_err)?;
                    if let Some((next_include, next_exclude)) = op_next {
                        let key = key_serializer.json_key(&key, extra).map_err(py_err_se_err)?;
                        let value_serialize = PydanticSerializer::new(
                            &value,
                            value_serializer,
                            next_include.as_ref(),
                            next_exclude.as_ref(),
                            extra,
                        );
                        map.serialize_entry(&key, &value_serialize)?;
                    }
                }
                map.end()
            }
            Err(_) => {
                extra.warnings.on_fallback_ser::<S>(self.get_name(), value, extra)?;
                infer_serialize(value, serializer, include, exclude, extra)
            }
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}
