use std::borrow::Cow;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};

use ahash::{AHashMap, AHashSet};
use serde::ser::SerializeMap;

use crate::build_context::BuildContext;
use crate::build_tools::{py_error_type, schema_or_config, SchemaDict};
use crate::PydanticSerializationUnexpectedValue;

use super::with_default::get_default;
use super::{
    infer_json_key, infer_serialize, infer_to_python, py_err_se_err, BuildSerializer, CombinedSerializer, Extra,
    PydanticSerializer, SchemaFilter, SerializeInfer, TypeSerializer,
};

#[derive(Debug, Clone)]
struct TypedDictField {
    key_py: Py<PyString>,
    alias: Option<String>,
    alias_py: Option<Py<PyString>>,
    serializer: CombinedSerializer,
    required: bool,
}

impl TypedDictField {
    fn get_key_py<'py>(&'py self, py: Python<'py>, extra: &Extra) -> &'py PyAny {
        if extra.by_alias {
            if let Some(ref alias_py) = self.alias_py {
                return alias_py.as_ref(py);
            }
        }
        self.key_py.as_ref(py)
    }

    fn get_key_json<'a>(&'a self, key_str: &'a str, extra: &Extra) -> Cow<'a, str> {
        if extra.by_alias {
            if let Some(ref alias) = self.alias {
                return Cow::Borrowed(alias.as_str());
            }
        }
        Cow::Borrowed(key_str)
    }
}

#[derive(Debug, Clone)]
pub struct TypedDictSerializer {
    fields: AHashMap<String, TypedDictField>,
    include_extra: bool,
    // isize because we look up include exclude via `.hash()` which returns an isize
    filter: SchemaFilter<isize>,
}

impl BuildSerializer for TypedDictSerializer {
    const EXPECTED_TYPE: &'static str = "typed-dict";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let py = schema.py();

        let extra_behavior = schema_or_config::<&str>(
            schema,
            config,
            intern!(py, "extra_behavior"),
            intern!(py, "typed_dict_extra_behavior"),
        )?;
        let total =
            schema_or_config(schema, config, intern!(py, "total"), intern!(py, "typed_dict_total"))?.unwrap_or(true);

        let include_extra = extra_behavior == Some("allow");

        let fields_dict: &PyDict = schema.get_as_req(intern!(py, "fields"))?;
        let mut fields: AHashMap<String, TypedDictField> = AHashMap::with_capacity(fields_dict.len());
        let mut exclude: Vec<Py<PyString>> = Vec::with_capacity(fields_dict.len());

        for (key, value) in fields_dict.iter() {
            let key: String = key.extract()?;
            let field_info: &PyDict = value.downcast()?;

            let schema = field_info.get_as_req(intern!(py, "schema"))?;

            let serializer = CombinedSerializer::build(schema, config, build_context)
                .map_err(|e| py_error_type!("Field `{}`:\n  {}", key, e))?;

            let (alias, alias_py) = match field_info.get_as::<&PyString>(intern!(py, "serialization_alias"))? {
                Some(alias_py) => {
                    let alias: String = alias_py.extract()?;
                    let alias_py = PyString::intern(py, &alias);
                    (Some(alias), Some(alias_py.into_py(py)))
                }
                None => (None, None),
            };

            let key_py: Py<PyString> = PyString::intern(py, &key).into_py(py);

            let required = field_info.get_as::<bool>(intern!(py, "required"))?.unwrap_or(total);

            if field_info.get_as(intern!(py, "serialization_exclude"))? == Some(true) {
                exclude.push(key_py.clone_ref(py));
            }
            fields.insert(
                key,
                TypedDictField {
                    key_py,
                    alias,
                    alias_py,
                    serializer,
                    required,
                },
            );
        }

        let filter = SchemaFilter::from_vec_hash(py, exclude)?;

        Ok(Self {
            fields,
            include_extra,
            filter,
        }
        .into())
    }
}

impl TypedDictSerializer {
    fn exclude_default(&self, value: &PyAny, extra: &Extra, field: &TypedDictField) -> PyResult<bool> {
        if extra.exclude_defaults {
            if let Some(default) = get_default(value.py(), &field.serializer)? {
                if value.eq(default.as_ref())? {
                    return Ok(true);
                }
            }
        }
        Ok(false)
    }
}

impl TypeSerializer for TypedDictSerializer {
    fn to_python(
        &self,
        value: &PyAny,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        let py = value.py();
        match value.downcast::<PyDict>() {
            Ok(py_dict) => {
                // NOTE! we maintain the order of the input dict assuming that's right
                let new_dict = PyDict::new(py);
                let mut used_fields = if extra.check.enabled() {
                    Some(AHashSet::with_capacity(self.fields.len()))
                } else {
                    None
                };

                for (key, value) in py_dict {
                    if extra.exclude_none && value.is_none() {
                        continue;
                    }
                    if let Some((next_include, next_exclude)) = self.filter.key_filter(key, include, exclude)? {
                        if let Ok(key_py_str) = key.downcast::<PyString>() {
                            let key_str = key_py_str.to_str()?;
                            if let Some(field) = self.fields.get(key_str) {
                                if self.exclude_default(value, extra, field)? {
                                    continue;
                                }
                                let value = field.serializer.to_python(value, next_include, next_exclude, extra)?;
                                let output_key = field.get_key_py(py, extra);
                                new_dict.set_item(output_key, value)?;

                                if let Some(ref mut used_fields) = used_fields {
                                    used_fields.insert(key_str);
                                }
                                continue;
                            }
                        }
                        if self.include_extra {
                            let value = infer_to_python(value, include, exclude, extra)?;
                            new_dict.set_item(key, value)?;
                        } else if extra.check.enabled() {
                            return Err(PydanticSerializationUnexpectedValue::new_err(None));
                        }
                    }
                }
                if let Some(ref used_fields) = used_fields {
                    let unused_fields = self
                        .fields
                        .iter()
                        .any(|(k, v)| v.required && !used_fields.contains(k.as_str()));
                    if unused_fields {
                        return Err(PydanticSerializationUnexpectedValue::new_err(None));
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

    fn json_key<'py>(&self, key: &'py PyAny, extra: &Extra) -> PyResult<Cow<'py, str>> {
        self._invalid_as_json_key(key, extra, Self::EXPECTED_TYPE)
    }

    fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        value: &PyAny,
        serializer: S,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> Result<S::Ok, S::Error> {
        match value.downcast::<PyDict>() {
            Ok(py_dict) => {
                let expected_len = match self.include_extra {
                    true => py_dict.len(),
                    false => self.fields.len(),
                };
                // NOTE! As above, we maintain the order of the input dict assuming that's right
                // we don't both with `used_fields` here because on unions, `to_python(..., mode='json')` is used
                let mut map = serializer.serialize_map(Some(expected_len))?;

                for (key, value) in py_dict {
                    if extra.exclude_none && value.is_none() {
                        continue;
                    }
                    if let Some((next_include, next_exclude)) =
                        self.filter.key_filter(key, include, exclude).map_err(py_err_se_err)?
                    {
                        if let Ok(key_py_str) = key.downcast::<PyString>() {
                            let key_str = key_py_str.to_str().map_err(py_err_se_err)?;
                            if let Some(field) = self.fields.get(key_str) {
                                if self.exclude_default(value, extra, field).map_err(py_err_se_err)? {
                                    continue;
                                }
                                let output_key = field.get_key_json(key_str, extra);
                                let s = PydanticSerializer::new(
                                    value,
                                    &field.serializer,
                                    next_include,
                                    next_exclude,
                                    extra,
                                );
                                map.serialize_entry(&output_key, &s)?;
                                continue;
                            }
                        }
                        if self.include_extra {
                            let s = SerializeInfer::new(value, include, exclude, extra);
                            let output_key = infer_json_key(key, extra).map_err(py_err_se_err)?;
                            map.serialize_entry(&output_key, &s)?
                        }
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
        Self::EXPECTED_TYPE
    }
}
