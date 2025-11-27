use std::borrow::Cow;
use std::string::ToString;
use std::sync::Arc;

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};

use ahash::AHashMap;
use serde::ser::SerializeMap;
use smallvec::SmallVec;

use crate::PydanticSerializationUnexpectedValue;
use crate::common::missing_sentinel::get_missing_sentinel_object;
use crate::serializers::SerializationState;
use crate::serializers::extra::{FieldName, SerCheck};
use crate::serializers::type_serializers::any::AnySerializer;
use crate::serializers::type_serializers::function::{FunctionPlainSerializer, FunctionWrapSerializer};

use super::computed_fields::ComputedFields;
use super::errors::py_err_se_err;
use super::extra::Extra;
use super::filter::SchemaFilter;
use super::infer::{SerializeInfer, infer_json_key, infer_serialize, infer_to_python};
use super::shared::{CombinedSerializer, PydanticSerializer, TypeSerializer};

/// representation of a field for serialization
#[derive(Debug)]
pub(super) struct SerField {
    pub key_py: Py<PyString>,
    pub alias: Option<String>,
    pub alias_py: Option<Py<PyString>>,
    // None serializer means exclude
    pub serializer: Option<Arc<CombinedSerializer>>,
    pub required: bool,
    pub serialize_by_alias: Option<bool>,
    pub serialization_exclude_if: Option<Py<PyAny>>,
}

impl_py_gc_traverse!(SerField { serializer });

impl SerField {
    pub fn new(
        py: Python,
        key_py: Py<PyString>,
        alias: Option<String>,
        serializer: Option<Arc<CombinedSerializer>>,
        required: bool,
        serialize_by_alias: Option<bool>,
        serialization_exclude_if: Option<Py<PyAny>>,
    ) -> Self {
        let alias_py = alias.as_ref().map(|alias| PyString::new(py, alias.as_str()).into());
        Self {
            key_py,
            alias,
            alias_py,
            serializer,
            required,
            serialize_by_alias,
            serialization_exclude_if,
        }
    }

    pub fn get_key_py<'py>(&self, py: Python<'py>, extra: &Extra) -> &Bound<'py, PyAny> {
        if extra.serialize_by_alias_or(self.serialize_by_alias) {
            if let Some(ref alias_py) = self.alias_py {
                return alias_py.bind(py);
            }
        }
        self.key_py.bind(py)
    }

    pub fn get_key_json<'a>(&'a self, key_str: &'a str, extra: &Extra) -> Cow<'a, str> {
        if extra.serialize_by_alias_or(self.serialize_by_alias) {
            if let Some(ref alias) = self.alias {
                return Cow::Borrowed(alias.as_str());
            }
        }
        Cow::Borrowed(key_str)
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
    extra: &Extra<'_, 'py>,
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

macro_rules! option_length {
    ($op_has_len:expr) => {
        match $op_has_len {
            Some(ref has_len) => has_len.len(),
            None => 0,
        }
    };
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

    pub(crate) fn main_to_python<'py>(
        &self,
        py: Python<'py>,
        model: &Bound<'py, PyAny>,
        main_iter: impl Iterator<Item = PyResult<(Bound<'py, PyAny>, Bound<'py, PyAny>)>>,
        state: &mut SerializationState<'_, 'py>,
    ) -> PyResult<Bound<'py, PyDict>> {
        let output_dict = PyDict::new(py);
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

            let field_name = FieldName::from(key.clone().cast_into()?);
            let state = &mut state.scoped_set(|s| &mut s.field_name, Some(field_name));
            if let Some((next_include, next_exclude)) = self.filter.key_filter(&key, state)? {
                let state = &mut state.scoped_include_exclude(next_include, next_exclude);
                let (key, serializer) = if let Some(field) = op_field {
                    let serializer = Self::prepare_value(&value, field, &state.extra)?;

                    if field.required {
                        used_req_fields += 1;
                    }

                    let Some(serializer) = serializer else {
                        continue;
                    };

                    (field.get_key_py(output_dict.py(), &state.extra), serializer)
                } else if self.mode == FieldsMode::TypedDictAllow {
                    let serializer = self
                        .extra_serializer
                        .as_ref()
                        // If using `serialize_as_any`, extras are always inferred
                        .filter(|_| !state.extra.serialize_as_any)
                        .unwrap_or_else(|| AnySerializer::get());
                    (&key, serializer)
                } else if state.check == SerCheck::Strict {
                    return Err(PydanticSerializationUnexpectedValue::new(
                        Some(format!("Unexpected field `{key}`")),
                        Some(key_str.to_string()),
                        model_type_name(model),
                        None,
                    )
                    .to_py_err());
                } else {
                    continue;
                };

                // Use `no_infer` here because the `serialize_as_any` logic has been handled in `prepare_value`
                let value = serializer.to_python_no_infer(&value, state)?;
                output_dict.set_item(key, value)?;
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
            .to_py_err())
        } else {
            Ok(output_dict)
        }
    }

    pub(crate) fn main_serde_serialize<'py, S: serde::ser::Serializer>(
        &self,
        main_iter: impl Iterator<Item = PyResult<(Bound<'py, PyAny>, Bound<'py, PyAny>)>>,
        expected_len: usize,
        serializer: S,
        state: &mut SerializationState<'_, 'py>,
    ) -> Result<S::SerializeMap, S::Error> {
        // NOTE! As above, we maintain the order of the input dict assuming that's right
        // we don't both with `used_req_fields` here because on unions, `to_python(..., mode='json')` is used
        let mut map = serializer.serialize_map(Some(expected_len))?;

        for result in main_iter {
            let (key, value) = result.map_err(py_err_se_err)?;
            let missing_sentinel = get_missing_sentinel_object(value.py());
            if state.extra.exclude_none && value.is_none() {
                continue;
            }
            if value.is(missing_sentinel) {
                continue;
            }
            let key_str = key_str(&key).map_err(py_err_se_err)?;

            let field_name = FieldName::from(key.clone().cast_into().map_err(py_err_se_err)?);
            let state = &mut state.scoped_set(|s| &mut s.field_name, Some(field_name));

            let filter = self.filter.key_filter(&key, state).map_err(py_err_se_err)?;
            if let Some((next_include, next_exclude)) = filter {
                let state = &mut state.scoped_include_exclude(next_include, next_exclude);
                if let Some(field) = self.fields.get(key_str) {
                    let Some(serializer) = Self::prepare_value(&value, field, &state.extra).map_err(py_err_se_err)?
                    else {
                        continue;
                    };

                    let output_key = field.get_key_json(key_str, &state.extra);
                    // Use `no_infer` here because the `serialize_as_any` logic has been handled in `prepare_value`
                    let s = PydanticSerializer::new_no_infer(&value, serializer, state);
                    map.serialize_entry(&output_key, &s)?;
                } else if self.mode == FieldsMode::TypedDictAllow {
                    // FIXME: why is `extra_serializer` not used here when `serialize_as_any` is not set?
                    let output_key = infer_json_key(&key, state).map_err(py_err_se_err)?;
                    let s = SerializeInfer::new(&value, state);
                    map.serialize_entry(&output_key, &s)?;
                }
                // no error case here since unions (which need the error case) use `to_python(..., mode='json')`
            }
        }
        Ok(map)
    }

    /// Gets the serializer to use for a field, applying `serialize_as_any` logic and applying any
    /// field-level exclusions
    fn prepare_value<'s>(
        value: &Bound<'_, PyAny>,
        field: &'s SerField,
        field_extra: &Extra<'_, '_>,
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

    pub(crate) fn add_computed_fields_python<'py>(
        &self,
        model: &Bound<'py, PyAny>,
        output_dict: &Bound<'py, PyDict>,
        state: &mut SerializationState<'_, 'py>,
    ) -> PyResult<()> {
        if let Some(ref computed_fields) = self.computed_fields {
            computed_fields.to_python(model, output_dict, &self.filter, state)?;
        }
        Ok(())
    }

    pub(crate) fn add_computed_fields_json<'py, S: serde::ser::Serializer>(
        &self,
        model: &Bound<'py, PyAny>,
        map: &mut S::SerializeMap,
        state: &mut SerializationState<'_, 'py>,
    ) -> Result<(), S::Error> {
        if let Some(ref computed_fields) = self.computed_fields {
            computed_fields.serde_serialize::<S>(model, map, &self.filter, state)?;
        }
        Ok(())
    }

    pub(crate) fn computed_field_count(&self) -> usize {
        option_length!(self.computed_fields)
    }
}

impl_py_gc_traverse!(GeneralFieldsSerializer {
    fields,
    computed_fields
});

impl TypeSerializer for GeneralFieldsSerializer {
    fn to_python<'py>(
        &self,
        value: &Bound<'py, PyAny>,
        state: &mut SerializationState<'_, 'py>,
    ) -> PyResult<Py<PyAny>> {
        let py = value.py();
        let missing_sentinel = get_missing_sentinel_object(py);

        let model = get_model(state)?;

        let Some((main_dict, extra_dict)) = self.extract_dicts(value) else {
            state.warn_fallback_py(self.get_name(), value)?;
            return infer_to_python(value, state);
        };
        let output_dict = self.main_to_python(py, &model, dict_items(&main_dict), state)?;

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
                    let value = match &self.extra_serializer {
                        Some(serializer) => serializer.to_python(&value, state)?,
                        _ => infer_to_python(&value, state)?,
                    };
                    output_dict.set_item(key, value)?;
                }
            }
        }
        self.add_computed_fields_python(&model, &output_dict, state)?;
        Ok(output_dict.into())
    }

    fn json_key<'a, 'py>(
        &self,
        key: &'a Bound<'py, PyAny>,
        state: &mut SerializationState<'_, 'py>,
    ) -> PyResult<Cow<'a, str>> {
        self.invalid_as_json_key(key, state, "fields")
    }

    fn serde_serialize<'py, S: serde::ser::Serializer>(
        &self,
        value: &Bound<'py, PyAny>,
        serializer: S,
        state: &mut SerializationState<'_, 'py>,
    ) -> Result<S::Ok, S::Error> {
        let Some((main_dict, extra_dict)) = self.extract_dicts(value) else {
            state.warn_fallback_ser::<S>(self.get_name(), value)?;
            return infer_serialize(value, serializer, state);
        };
        let missing_sentinel = get_missing_sentinel_object(value.py());
        let model = get_model(state).map_err(py_err_se_err)?;

        let expected_len = match self.mode {
            FieldsMode::TypedDictAllow => main_dict.len() + self.computed_field_count(),
            _ => self.fields.len() + option_length!(extra_dict) + self.computed_field_count(),
        };
        // NOTE! As above, we maintain the order of the input dict assuming that's right
        // we don't both with `used_req_fields` here because on unions, `to_python(..., mode='json')` is used
        let mut map = self.main_serde_serialize(dict_items(&main_dict), expected_len, serializer, state)?;

        // this is used to include `__pydantic_extra__` in serialization on models
        if let Some(extra_dict) = extra_dict {
            for (key, value) in extra_dict {
                if state.extra.exclude_none && value.is_none() {
                    continue;
                }
                if value.is(missing_sentinel) {
                    continue;
                }
                let filter = self.filter.key_filter(&key, state).map_err(py_err_se_err)?;
                if let Some((next_include, next_exclude)) = filter {
                    let state = &mut state.scoped_include_exclude(next_include, next_exclude);
                    let output_key = infer_json_key(&key, state).map_err(py_err_se_err)?;
                    let s = SerializeInfer::new(&value, state);
                    map.serialize_entry(&output_key, &s)?;
                }
            }
        }

        self.add_computed_fields_json::<S>(&model, &mut map, state)?;
        map.end()
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

fn get_model<'py>(state: &mut SerializationState<'_, 'py>) -> PyResult<Bound<'py, PyAny>> {
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
