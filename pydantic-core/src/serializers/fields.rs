use std::borrow::Cow;
use std::string::ToString;
use std::sync::Arc;

use pyo3::prelude::*;
use pyo3::pybacked::PyBackedStr;
use pyo3::types::PyDict;

use ahash::AHashMap;
use smallvec::SmallVec;

use crate::PydanticSerializationUnexpectedValue;
use crate::common::missing_sentinel::get_missing_sentinel_object;
use crate::serializers::SerializationState;
use crate::serializers::errors::unwrap_ser_error;
use crate::serializers::extra::{IncludeExclude, SerCheck};
use crate::serializers::shared::{DoSerialize, SerializeMap, serialize_to_json, serialize_to_python};
use crate::serializers::type_serializers::any::AnySerializer;
use crate::serializers::type_serializers::function::{FunctionPlainSerializer, FunctionWrapSerializer};
use crate::tools::pybackedstr_to_pystring;

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

/// representation of a extra field for serialization
#[derive(Debug)]
pub(super) struct ExtraSerFields {
    pub extra_serializer: Option<Arc<CombinedSerializer>>,
    pub serialization_exclude_if: Option<Py<PyAny>>,
}

impl ExtraSerFields {
    pub fn new(extra_serializer: Option<Arc<CombinedSerializer>>, serialization_exclude_if: Option<Py<PyAny>>) -> Self {
        Self {
            extra_serializer,
            serialization_exclude_if,
        }
    }
}

/// General purpose serializer for fields - used by dataclasses, models and typed_dicts
#[derive(Debug)]
pub struct GeneralFieldsSerializer {
    fields: AHashMap<PyBackedStr, SerField>,
    computed_fields: Option<ComputedFields>,
    mode: FieldsMode,
    extra_fields: Option<ExtraSerFields>,
    // isize because we look up filter via `.hash()` which returns an isize
    filter: SchemaFilter<isize>,
    required_fields: usize,
}

impl GeneralFieldsSerializer {
    pub(super) fn new(
        fields: AHashMap<PyBackedStr, SerField>,
        mode: FieldsMode,
        extra_fields: Option<ExtraSerFields>,
        computed_fields: Option<ComputedFields>,
    ) -> Self {
        let required_fields = fields.values().filter(|f| f.required).count();
        Self {
            fields,
            mode,
            extra_fields,
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
        let Some((main_dict, extra_dict)) = self.extract_dicts(value) else {
            return do_serialize.serialize_fallback(self.get_name(), value, state);
        };

        self.serialize_iterators(
            &get_model(state)?,
            dict_items(&main_dict),
            extra_dict.into_iter().flatten().map(Ok),
            state,
            do_serialize,
        )
    }

    /// Serialize from two iterators - one for the main fields, one for extra fields. Order of iteration is preserved.
    ///
    /// It is assumed that the iterators do not yield duplicate keys (the check logic will be incorrect if duplicates are present)
    pub(crate) fn serialize_iterators<'py, S: DoSerialize>(
        &self,
        model: &Bound<'py, PyAny>,
        main_iter: impl Iterator<Item = PyResult<(Bound<'py, PyAny>, Bound<'py, PyAny>)>>,
        extras_iter: impl Iterator<Item = PyResult<(Bound<'py, PyAny>, Bound<'py, PyAny>)>>,
        state: &mut SerializationState<'py>,
        do_serialize: S,
    ) -> Result<S::Ok, S::Error> {
        let py = model.py();
        let mut map = do_serialize.serialize_map()?;
        let mut used_req_fields: usize = 0;
        let missing_sentinel = get_missing_sentinel_object(py);

        for result in main_iter {
            let (key, value) = result?;
            let key_str: PyBackedStr = key.extract()?;

            let state = &mut state.scoped_set_field_name(Some(key_str.as_py_str().bind(py).clone()));

            if let Some(field) = self.fields.get(&*key_str) {
                if field.required {
                    used_req_fields += 1;
                }

                let Some((serializer, next_include_exclude)) =
                    self.prepare_value(&key, &value, field, state, missing_sentinel)?
                else {
                    // field was excluded
                    continue;
                };

                let state = &mut state.scoped_include_exclude(next_include_exclude);
                map.serialize_entry_string_key(field.get_key(&state.extra), &value, serializer, state)?;
            } else if self.mode == FieldsMode::TypedDictAllow {
                self.serialize_extra(&key_str, &value, state, missing_sentinel, &mut map)?;
            } else if state.check == SerCheck::Strict {
                return Err(unexpected_field(&key_str, model).into());
            }
        }

        if state.check.enabled() && self.required_fields > used_req_fields {
            return Err(incorrect_field_count(self.required_fields, used_req_fields, model, state).into());
        }

        for result in extras_iter {
            let (key, value) = result?;
            self.serialize_extra(&key.extract()?, &value, state, missing_sentinel, &mut map)?;
        }

        if let Some(computed_fields) = &self.computed_fields {
            computed_fields.serialize(model, &mut map, &self.filter, state, missing_sentinel)?;
        }

        map.end()
    }

    /// Gets the serializer to use for a field, applying `serialize_as_any` logic and applying any
    /// field-level exclusions
    fn prepare_value<'s, 'py>(
        &self,
        key: &Bound<'py, PyAny>,
        value: &Bound<'py, PyAny>,
        field: &'s SerField,
        state: &SerializationState<'py>,
        missing_sentinel: &Bound<'py, PyAny>,
    ) -> PyResult<Option<(&'s Arc<CombinedSerializer>, IncludeExclude<'py>)>> {
        // if field excluded at schema level, this is the cheapest exclusion
        let Some(serializer) = field.serializer.as_ref() else {
            return Ok(None);
        };

        // filtering on the keys
        let Some(next_include_exclude) = self.filter.key_filter(key, state)? else {
            return Ok(None);
        };

        // filtering on the value
        if exclude_field_by_value(value, state, missing_sentinel, field.serialization_exclude_if.as_ref())?
            || exclude_default(value, &state.extra, serializer)?
        {
            return Ok(None);
        }

        let serializer = if state.extra.serialize_as_any &&
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
        };

        Ok(Some((serializer, next_include_exclude)))
    }

    fn serialize_extra<'py, Map: SerializeMap>(
        &self,
        key: &PyBackedStr,
        value: &Bound<'py, PyAny>,
        state: &mut SerializationState<'py>,
        missing_sentinel: &Bound<'py, PyAny>,
        map: &mut Map,
    ) -> Result<(), Map::Error> {
        let key_py_string = pybackedstr_to_pystring(value.py(), key);
        let extras_serializer = self
            .extra_fields
            .as_ref()
            .filter(|_| !state.extra.serialize_as_any)
            .and_then(|e| e.extra_serializer.as_ref())
            .unwrap_or_else(|| AnySerializer::get());
        let extras_serialization_exclude_if = self
            .extra_fields
            .as_ref()
            .and_then(|e| e.serialization_exclude_if.as_ref());
        if let Some(next_include_exclude) = self.filter.key_filter(&key_py_string, state)?
            && !exclude_field_by_value(value, state, missing_sentinel, extras_serialization_exclude_if)?
        {
            let state = &mut state.scoped_include_exclude(next_include_exclude);
            map.serialize_entry_string_key(key, value, extras_serializer, state)
        } else {
            // field was excluded
            Ok(())
        }
    }
}

/// Common logic for excluding fields during serialization
pub fn exclude_field_by_value<'py>(
    value: &Bound<'py, PyAny>,
    state: &SerializationState<'py>,
    missing_sentinel: &Bound<'py, PyAny>,
    exclude_if_callable: Option<&Py<PyAny>>,
) -> PyResult<bool> {
    if state.extra.exclude_none && value.is_none() {
        return Ok(true);
    }

    if value.is(missing_sentinel) {
        return Ok(true);
    }

    if serialization_exclude_if(exclude_if_callable, value)? {
        return Ok(true);
    }

    Ok(false)
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

#[cold]
fn unexpected_field(key: &PyBackedStr, model: &Bound<'_, PyAny>) -> PyErr {
    PydanticSerializationUnexpectedValue::new(
        Some(format!("Unexpected field `{key}`")),
        Some(key.as_py_str().clone_ref(model.py())),
        model_type_name(model),
        None,
    )
    .to_py_err()
}

#[cold]
fn incorrect_field_count(
    expected_fields: usize,
    used_fields: usize,
    model: &Bound<'_, PyAny>,
    state: &SerializationState<'_>,
) -> PyErr {
    PydanticSerializationUnexpectedValue::new(
        Some(format!("Expected {expected_fields} fields but got {used_fields}").to_string()),
        state.field_name().map(|name| name.clone().unbind()),
        model_type_name(model),
        Some(model.clone().unbind()),
    )
    .to_py_err()
}
