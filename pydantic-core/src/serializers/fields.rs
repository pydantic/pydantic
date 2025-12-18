use std::borrow::Cow;
use std::string::ToString;
use std::sync::Arc;

use pyo3::prelude::*;
use pyo3::pybacked::PyBackedStr;
use pyo3::types::{PyDict, PyString};

use ahash::AHashMap;
use smallvec::SmallVec;

use crate::PydanticSerializationUnexpectedValue;
use crate::common::missing_sentinel::get_missing_sentinel_object;
use crate::serializers::SerializationState;
use crate::serializers::errors::unwrap_ser_error;
use crate::serializers::extra::{FieldName, SerCheck};
use crate::serializers::shared::{DoSerialize, SerializeMap, serialize_to_json, serialize_to_python};
use crate::serializers::type_serializers::any::AnySerializer;
use crate::serializers::type_serializers::function::{FunctionPlainSerializer, FunctionWrapSerializer};

use super::computed_fields::ComputedFields;
use super::extra::Extra;
use super::filter::SchemaFilter;
use super::shared::{CombinedSerializer, TypeSerializer};

/// representation of a field for serialization
#[derive(Debug)]
pub(super) struct SerField {
    pub key: PyBackedStr,
    pub alias: Option<PyBackedStr>,
    // None serializer means exclude
    pub serializer: Option<Arc<CombinedSerializer>>,
    pub required: bool,
    pub serialize_by_alias: Option<bool>,
    pub serialization_exclude_if: Option<Py<PyAny>>,
}

impl_py_gc_traverse!(SerField { serializer });

impl SerField {
    pub fn new(
        key: PyBackedStr,
        alias: Option<PyBackedStr>,
        serializer: Option<Arc<CombinedSerializer>>,
        required: bool,
        serialize_by_alias: Option<bool>,
        serialization_exclude_if: Option<Py<PyAny>>,
    ) -> Self {
        Self {
            key,
            alias,
            serializer,
            required,
            serialize_by_alias,
            serialization_exclude_if,
        }
    }

    pub fn get_key(&self, extra: &Extra) -> &PyBackedStr {
        if extra.serialize_by_alias_or(self.serialize_by_alias)
            && let Some(alias) = &self.alias
        {
            return alias;
        }
        &self.key
    }
}

fn serialization_exclude_if(exclude_if_callable: Option<&Py<PyAny>>, value: &Bound<'_, PyAny>) -> PyResult<bool> {
    if let Some(exclude_if_callable) = exclude_if_callable {
        let py = value.py();
        let result = exclude_if_callable.call1(py, (value,))?;
        let exclude = result.extract::<bool>(py)?;
        if exclude {
            return Ok(true);
        }
    }
    Ok(false)
}

fn exclude_default<'py>(
    value: &Bound<'py, PyAny>,
    extra: &Extra<'py>,
    serializer: &CombinedSerializer,
) -> PyResult<bool> {
    if extra.exclude_defaults
        && let Some(default) = serializer.get_default(value.py())?
        && value.eq(default)?
    {
        return Ok(true);
    }
    Ok(false)
}

#[derive(Debug, Clone, Eq, PartialEq)]
pub(super) enum FieldsMode {
    // typeddict with no extra items
    SimpleDict,
    // a model - get `__dict__` and `__pydantic_extra__` - `GeneralFieldsSerializer` will get a tuple
    ModelExtra,
    // typeddict with extra items - one dict with extra items
    TypedDictAllow,
}

/// General purpose serializer for fields - used by dataclasses, models and typed_dicts
#[derive(Debug)]
pub struct GeneralFieldsSerializer {
    fields: AHashMap<String, SerField>,
    computed_fields: Option<ComputedFields>,
    mode: FieldsMode,
    extra_serializer: Option<Arc<CombinedSerializer>>,
    // isize because we look up filter via `.hash()` which returns an isize
    filter: SchemaFilter<isize>,
    required_fields: usize,
}

impl GeneralFieldsSerializer {
    pub(super) fn new(
        fields: AHashMap<String, SerField>,
        mode: FieldsMode,
        extra_serializer: Option<Arc<CombinedSerializer>>,
        computed_fields: Option<ComputedFields>,
    ) -> Self {
        let required_fields = fields.values().filter(|f| f.required).count();
        Self {
            fields,
            mode,
            extra_serializer,
            filter: SchemaFilter::default(),
            computed_fields,
            required_fields,
        }
    }

    fn extract_dicts<'a>(&self, value: &Bound<'a, PyAny>) -> Option<(Bound<'a, PyDict>, Option<Bound<'a, PyDict>>)> {
        match self.mode {
            FieldsMode::ModelExtra => value.extract().ok(),
            _ => {
                if let Ok(main_dict) = value.cast::<PyDict>() {
                    Some((main_dict.clone(), None))
                } else {
                    None
                }
            }
        }
    }

    fn serialize<'py, S: DoSerialize>(
        &self,
        value: &Bound<'py, PyAny>,
        state: &mut SerializationState<'py>,
        do_serialize: S,
    ) -> Result<S::Ok, S::Error> {
        let py = value.py();

        let Some((main_dict, extra_dict)) = self.extract_dicts(value) else {
            return do_serialize.serialize_fallback(self.get_name(), value, state);
        };

        let missing_sentinel = get_missing_sentinel_object(py);
        let model = get_model(state)?;

        let mut map = self.serialize_main(py, &model, dict_items(&main_dict), state, do_serialize)?;

        // this is used to include `__pydantic_extra__` in serialization on models
        if let Some(extra_dict) = extra_dict {
            for (key, value) in extra_dict {
                if state.extra.exclude_none && value.is_none() {
                    continue;
                }
                if value.is(missing_sentinel) {
                    continue;
                }
                if let Some((next_include, next_exclude)) = self.filter.key_filter(&key, state)? {
                    let state = &mut state.scoped_include_exclude(next_include, next_exclude);
                    map.serialize_entry(
                        &key,
                        AnySerializer::get(),
                        &value,
                        self.extra_serializer.as_ref().unwrap_or(AnySerializer::get()),
                        state,
                    )?;
                }
            }
        }
        self.add_computed_fields(&model, &mut map, state)?;
        map.end()
    }

    pub(crate) fn serialize_main<'py, S: DoSerialize>(
        &self,
        py: Python<'py>,
        model: &Bound<'py, PyAny>,
        main_iter: impl Iterator<Item = PyResult<(Bound<'py, PyAny>, Bound<'py, PyAny>)>>,
        state: &mut SerializationState<'py>,
        do_serialize: S,
    ) -> Result<S::Map, S::Error> {
        let mut map = do_serialize.serialize_map()?;
        let mut used_req_fields: usize = 0;
        let missing_sentinel = get_missing_sentinel_object(py);

        // NOTE! we maintain the order of the input dict assuming that's right
        for result in main_iter {
            let (key, value) = result?;
            let key_str = key_str(&key)?;
            let op_field = self.fields.get(key_str);
            if state.extra.exclude_none && value.is_none() {
                continue;
            }
            if value.is(missing_sentinel) {
                continue;
            }

            let field_name = FieldName::from(key.clone().cast_into().map_err(PyErr::from)?);
            let state = &mut state.scoped_set(|s| &mut s.field_name, Some(field_name));
            if let Some((next_include, next_exclude)) = self.filter.key_filter(&key, state)? {
                let state = &mut state.scoped_include_exclude(next_include, next_exclude);
                if let Some(field) = op_field {
                    let serializer = Self::prepare_value(&value, field, &state.extra)?;

                    if field.required {
                        used_req_fields += 1;
                    }

                    let Some(serializer) = serializer else {
                        // field is excluded
                        continue;
                    };

                    map.serialize_entry_string_key(field.get_key(&state.extra), &value, serializer, state)?;
                } else if self.mode == FieldsMode::TypedDictAllow {
                    let serializer = self
                        .extra_serializer
                        .as_ref()
                        // If using `serialize_as_any`, extras are always inferred
                        .filter(|_| !state.extra.serialize_as_any)
                        .unwrap_or_else(|| AnySerializer::get());
                    map.serialize_entry(&key, AnySerializer::get(), &value, serializer, state)?;
                } else if state.check == SerCheck::Strict {
                    return Err(PydanticSerializationUnexpectedValue::new(
                        Some(format!("Unexpected field `{key}`")),
                        Some(key_str.to_string()),
                        model_type_name(model),
                        None,
                    )
                    .to_py_err()
                    .into());
                }
            }
        }

        let extra = &state.extra;
        if state.check.enabled()
            // If any of these are true we can't count fields
            && !(extra.exclude_defaults || extra.exclude_unset || extra.exclude_none || extra.exclude_computed_fields || state.exclude().is_some())
            // Check for missing fields, we can't have extra fields here
            && self.required_fields > used_req_fields
        {
            let required_fields = self.required_fields;

            Err(PydanticSerializationUnexpectedValue::new(
                Some(format!("Expected {required_fields} fields but got {used_req_fields}").to_string()),
                state.field_name.as_ref().map(ToString::to_string),
                model_type_name(model),
                Some(model.clone().unbind()),
            )
            .to_py_err()
            .into())
        } else {
            Ok(map)
        }
    }

    /// Gets the serializer to use for a field, applying `serialize_as_any` logic and applying any
    /// field-level exclusions
    fn prepare_value<'s>(
        value: &Bound<'_, PyAny>,
        field: &'s SerField,
        field_extra: &Extra<'_>,
    ) -> PyResult<Option<&'s Arc<CombinedSerializer>>> {
        let Some(serializer) = field.serializer.as_ref() else {
            // field excluded at schema level
            return Ok(None);
        };

        if exclude_default(value, field_extra, serializer)? {
            return Ok(None);
        }

        // FIXME: should `exclude_if` be applied to extra fields too?
        if serialization_exclude_if(field.serialization_exclude_if.as_ref(), value)? {
            return Ok(None);
        }

        Ok(Some(
            if field_extra.serialize_as_any &&
            // if serialize_as_any is set, we ensure that field serializers are
            // still used, because this would match the `SerializeAsAny` annotation
            // on a field
            !matches!(
                serializer.as_ref(),
                CombinedSerializer::Function(FunctionPlainSerializer {
                    is_field_serializer: true,
                    ..
                }) | CombinedSerializer::FunctionWrap(FunctionWrapSerializer {
                    is_field_serializer: true,
                    ..
                })
            ) {
                AnySerializer::get()
            } else {
                serializer
            },
        ))
    }

    pub(crate) fn add_computed_fields<'py, M: SerializeMap>(
        &self,
        model: &Bound<'py, PyAny>,
        map: &mut M,
        state: &mut SerializationState<'py>,
    ) -> Result<(), M::Error> {
        if let Some(ref computed_fields) = self.computed_fields {
            computed_fields.serialize(model, map, &self.filter, state)?;
        }
        Ok(())
    }
}

impl_py_gc_traverse!(GeneralFieldsSerializer {
    fields,
    computed_fields
});

impl TypeSerializer for GeneralFieldsSerializer {
    fn to_python<'py>(&self, value: &Bound<'py, PyAny>, state: &mut SerializationState<'py>) -> PyResult<Py<PyAny>> {
        self.serialize(value, state, serialize_to_python(value.py()))
    }

    fn json_key<'a, 'py>(
        &self,
        key: &'a Bound<'py, PyAny>,
        state: &mut SerializationState<'py>,
    ) -> PyResult<Cow<'a, str>> {
        self.invalid_as_json_key(key, state, "fields")
    }

    fn serde_serialize<'py, S: serde::ser::Serializer>(
        &self,
        value: &Bound<'py, PyAny>,
        serializer: S,
        state: &mut SerializationState<'py>,
    ) -> Result<S::Ok, S::Error> {
        self.serialize(value, state, serialize_to_json(serializer))
            .map_err(unwrap_ser_error)
    }

    fn get_name(&self) -> &'static str {
        "general-fields"
    }
}

fn key_str<'a>(key: &'a Bound<'_, PyAny>) -> PyResult<&'a str> {
    key.cast::<PyString>()?.to_str()
}

fn dict_items<'py>(
    main_dict: &'_ Bound<'py, PyDict>,
) -> impl Iterator<Item = PyResult<(Bound<'py, PyAny>, Bound<'py, PyAny>)>> {
    // Collect items before iterating to prevent panic on dict mutation.
    // Use a SmallVec to avoid heap allocation for models with a reasonable number of fields.
    let main_items: SmallVec<[_; 16]> = main_dict.iter().collect();
    main_items.into_iter().map(Ok)
}

fn get_model<'py>(state: &mut SerializationState<'py>) -> PyResult<Bound<'py, PyAny>> {
    state.model.clone().ok_or_else(|| {
        PydanticSerializationUnexpectedValue::new(
            Some("No model found for fields serialization".to_string()),
            None,
            None,
            None,
        )
        .to_py_err()
    })
}

fn model_type_name(model: &Bound<'_, PyAny>) -> Option<String> {
    model.get_type().name().ok().map(|s| s.to_string())
}
