use std::borrow::Cow;

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};

use ahash::AHashMap;
use serde::ser::SerializeMap;
use smallvec::SmallVec;

use crate::serializers::extra::SerCheck;
use crate::serializers::DuckTypingSerMode;
use crate::PydanticSerializationUnexpectedValue;

use super::computed_fields::ComputedFields;
use super::errors::py_err_se_err;
use super::extra::Extra;
use super::filter::SchemaFilter;
use super::infer::{infer_json_key, infer_serialize, infer_to_python, SerializeInfer};
use super::shared::PydanticSerializer;
use super::shared::{CombinedSerializer, TypeSerializer};

/// representation of a field for serialization
#[derive(Debug)]
pub(super) struct SerField {
    pub key_py: Py<PyString>,
    pub alias: Option<String>,
    pub alias_py: Option<Py<PyString>>,
    // None serializer means exclude
    pub serializer: Option<CombinedSerializer>,
    pub required: bool,
}

impl_py_gc_traverse!(SerField { serializer });

impl SerField {
    pub fn new(
        py: Python,
        key_py: Py<PyString>,
        alias: Option<String>,
        serializer: Option<CombinedSerializer>,
        required: bool,
    ) -> Self {
        let alias_py = alias
            .as_ref()
            .map(|alias| PyString::new_bound(py, alias.as_str()).into());
        Self {
            key_py,
            alias,
            alias_py,
            serializer,
            required,
        }
    }

    pub fn get_key_py<'py>(&'py self, py: Python<'py>, extra: &Extra) -> &Bound<'py, PyAny> {
        if extra.by_alias {
            if let Some(ref alias_py) = self.alias_py {
                return alias_py.bind(py);
            }
        }
        self.key_py.bind(py)
    }

    pub fn get_key_json<'a>(&'a self, key_str: &'a str, extra: &Extra) -> Cow<'a, str> {
        if extra.by_alias {
            if let Some(ref alias) = self.alias {
                return Cow::Borrowed(alias.as_str());
            }
        }
        Cow::Borrowed(key_str)
    }
}

fn exclude_default(value: &Bound<'_, PyAny>, extra: &Extra, serializer: &CombinedSerializer) -> PyResult<bool> {
    if extra.exclude_defaults {
        if let Some(default) = serializer.get_default(value.py())? {
            if value.eq(default)? {
                return Ok(true);
            }
        }
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
    extra_serializer: Option<Box<CombinedSerializer>>,
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
        extra_serializer: Option<CombinedSerializer>,
        computed_fields: Option<ComputedFields>,
    ) -> Self {
        let required_fields = fields.values().filter(|f| f.required).count();
        Self {
            fields,
            mode,
            extra_serializer: extra_serializer.map(Box::new),
            filter: SchemaFilter::default(),
            computed_fields,
            required_fields,
        }
    }

    fn extract_dicts<'a>(&self, value: &Bound<'a, PyAny>) -> Option<(Bound<'a, PyDict>, Option<Bound<'a, PyDict>>)> {
        match self.mode {
            FieldsMode::ModelExtra => value.extract().ok(),
            _ => {
                if let Ok(main_dict) = value.downcast::<PyDict>() {
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
        main_iter: impl Iterator<Item = PyResult<(Bound<'py, PyAny>, Bound<'py, PyAny>)>>,
        include: Option<&Bound<'py, PyAny>>,
        exclude: Option<&Bound<'py, PyAny>>,
        extra: Extra,
    ) -> PyResult<Bound<'py, PyDict>> {
        let output_dict = PyDict::new_bound(py);
        let mut used_req_fields: usize = 0;

        // NOTE! we maintain the order of the input dict assuming that's right
        for result in main_iter {
            let (key, value) = result?;
            let key_str = key_str(&key)?;
            let op_field = self.fields.get(key_str);
            if extra.exclude_none && value.is_none() {
                if let Some(field) = op_field {
                    if field.required {
                        used_req_fields += 1;
                    }
                }
                continue;
            }
            let field_extra = Extra {
                field_name: Some(key_str),
                ..extra
            };
            if let Some((next_include, next_exclude)) = self.filter.key_filter(&key, include, exclude)? {
                if let Some(field) = op_field {
                    if let Some(ref serializer) = field.serializer {
                        if !exclude_default(&value, &field_extra, serializer)? {
                            let value = serializer.to_python(
                                &value,
                                next_include.as_ref(),
                                next_exclude.as_ref(),
                                &field_extra,
                            )?;
                            let output_key = field.get_key_py(output_dict.py(), &field_extra);
                            output_dict.set_item(output_key, value)?;
                        }
                    }

                    if field.required {
                        used_req_fields += 1;
                    }
                } else if self.mode == FieldsMode::TypedDictAllow {
                    let value = match &self.extra_serializer {
                        Some(serializer) => {
                            serializer.to_python(&value, next_include.as_ref(), next_exclude.as_ref(), &field_extra)?
                        }
                        None => infer_to_python(&value, next_include.as_ref(), next_exclude.as_ref(), &field_extra)?,
                    };
                    output_dict.set_item(key, value)?;
                } else if field_extra.check == SerCheck::Strict {
                    return Err(PydanticSerializationUnexpectedValue::new_err(None));
                }
            }
        }

        if extra.check.enabled()
            // If any of these are true we can't count fields
            && !(extra.exclude_defaults || extra.exclude_unset || extra.exclude_none)
            // Check for missing fields, we can't have extra fields here
            && self.required_fields > used_req_fields
        {
            Err(PydanticSerializationUnexpectedValue::new_err(None))
        } else {
            Ok(output_dict)
        }
    }

    pub(crate) fn main_serde_serialize<'py, S: serde::ser::Serializer>(
        &self,
        main_iter: impl Iterator<Item = PyResult<(Bound<'py, PyAny>, Bound<'py, PyAny>)>>,
        expected_len: usize,
        serializer: S,
        include: Option<&Bound<'py, PyAny>>,
        exclude: Option<&Bound<'py, PyAny>>,
        extra: Extra,
    ) -> Result<S::SerializeMap, S::Error> {
        // NOTE! As above, we maintain the order of the input dict assuming that's right
        // we don't both with `used_fields` here because on unions, `to_python(..., mode='json')` is used
        let mut map = serializer.serialize_map(Some(expected_len))?;

        for result in main_iter {
            let (key, value) = result.map_err(py_err_se_err)?;
            if extra.exclude_none && value.is_none() {
                continue;
            }
            let key_str = key_str(&key).map_err(py_err_se_err)?;
            let field_extra = Extra {
                field_name: Some(key_str),
                ..extra
            };

            let filter = self.filter.key_filter(&key, include, exclude).map_err(py_err_se_err)?;
            if let Some((next_include, next_exclude)) = filter {
                if let Some(field) = self.fields.get(key_str) {
                    if let Some(ref serializer) = field.serializer {
                        if !exclude_default(&value, &field_extra, serializer).map_err(py_err_se_err)? {
                            let s = PydanticSerializer::new(
                                &value,
                                serializer,
                                next_include.as_ref(),
                                next_exclude.as_ref(),
                                &field_extra,
                            );
                            let output_key = field.get_key_json(key_str, &field_extra);
                            map.serialize_entry(&output_key, &s)?;
                        }
                    }
                } else if self.mode == FieldsMode::TypedDictAllow {
                    let output_key = infer_json_key(&key, &field_extra).map_err(py_err_se_err)?;
                    let s = SerializeInfer::new(&value, next_include.as_ref(), next_exclude.as_ref(), &field_extra);
                    map.serialize_entry(&output_key, &s)?;
                }
                // no error case here since unions (which need the error case) use `to_python(..., mode='json')`
            }
        }
        Ok(map)
    }

    pub(crate) fn add_computed_fields_python(
        &self,
        model: Option<&Bound<'_, PyAny>>,
        output_dict: &Bound<'_, PyDict>,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> PyResult<()> {
        if let Some(ref computed_fields) = self.computed_fields {
            if let Some(model_value) = model {
                let cf_extra = Extra { model, ..*extra };
                computed_fields.to_python(model_value, output_dict, &self.filter, include, exclude, &cf_extra)?;
            }
        }
        Ok(())
    }

    pub(crate) fn add_computed_fields_json<S: serde::ser::Serializer>(
        &self,
        model: Option<&Bound<'_, PyAny>>,
        map: &mut S::SerializeMap,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> Result<(), S::Error> {
        if let Some(ref computed_fields) = self.computed_fields {
            if let Some(model) = model {
                computed_fields.serde_serialize::<S>(model, map, &self.filter, include, exclude, extra)?;
            }
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
    fn to_python(
        &self,
        value: &Bound<'_, PyAny>,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        let py = value.py();
        // If there is already a model registered (from a dataclass, BaseModel)
        // then do not touch it
        // If there is no model, we (a TypedDict) are the model
        let model = extra.model.map_or_else(|| Some(value), Some);

        // If there is no model, use duck typing ser logic for TypedDict
        // If there is a model, skip this step, as BaseModel and dataclass duck typing
        // is handled in their respective serializers
        if extra.model.is_none() {
            let duck_typing_ser_mode = extra.duck_typing_ser_mode.next_mode();
            let td_extra = Extra {
                model,
                duck_typing_ser_mode,
                ..*extra
            };
            if td_extra.duck_typing_ser_mode == DuckTypingSerMode::Inferred {
                return infer_to_python(value, include, exclude, &td_extra);
            }
        }
        let (main_dict, extra_dict) = if let Some(main_extra_dict) = self.extract_dicts(value) {
            main_extra_dict
        } else {
            extra.warnings.on_fallback_py(self.get_name(), value, extra)?;
            return infer_to_python(value, include, exclude, extra);
        };

        let output_dict =
            self.main_to_python(py, dict_items(&main_dict), include, exclude, Extra { model, ..*extra })?;

        // this is used to include `__pydantic_extra__` in serialization on models
        if let Some(extra_dict) = extra_dict {
            for (key, value) in extra_dict {
                if extra.exclude_none && value.is_none() {
                    continue;
                }
                if let Some((next_include, next_exclude)) = self.filter.key_filter(&key, include, exclude)? {
                    let value = match &self.extra_serializer {
                        Some(serializer) => {
                            serializer.to_python(&value, next_include.as_ref(), next_exclude.as_ref(), extra)?
                        }
                        None => infer_to_python(&value, next_include.as_ref(), next_exclude.as_ref(), extra)?,
                    };
                    output_dict.set_item(key, value)?;
                }
            }
        }
        self.add_computed_fields_python(model, &output_dict, include, exclude, extra)?;
        Ok(output_dict.into_py(py))
    }

    fn json_key<'a>(&self, key: &'a Bound<'_, PyAny>, extra: &Extra) -> PyResult<Cow<'a, str>> {
        self._invalid_as_json_key(key, extra, "fields")
    }

    fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        value: &Bound<'_, PyAny>,
        serializer: S,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> Result<S::Ok, S::Error> {
        let (main_dict, extra_dict) = if let Some(main_extra_dict) = self.extract_dicts(value) {
            main_extra_dict
        } else {
            extra.warnings.on_fallback_ser::<S>(self.get_name(), value, extra)?;
            return infer_serialize(value, serializer, include, exclude, extra);
        };

        // If there is already a model registered (from a dataclass, BaseModel)
        // then do not touch it
        // If there is no model, we (a TypedDict) are the model
        let model = extra.model.map_or_else(|| Some(value), Some);

        // If there is no model, use duck typing ser logic for TypedDict
        // If there is a model, skip this step, as BaseModel and dataclass duck typing
        // is handled in their respective serializers
        if extra.model.is_none() {
            let duck_typing_ser_mode = extra.duck_typing_ser_mode.next_mode();
            let td_extra = Extra {
                model,
                duck_typing_ser_mode,
                ..*extra
            };
            if td_extra.duck_typing_ser_mode == DuckTypingSerMode::Inferred {
                return infer_serialize(value, serializer, include, exclude, &td_extra);
            }
        }
        let expected_len = match self.mode {
            FieldsMode::TypedDictAllow => main_dict.len() + self.computed_field_count(),
            _ => self.fields.len() + option_length!(extra_dict) + self.computed_field_count(),
        };
        // NOTE! As above, we maintain the order of the input dict assuming that's right
        // we don't both with `used_fields` here because on unions, `to_python(..., mode='json')` is used
        let mut map = self.main_serde_serialize(
            dict_items(&main_dict),
            expected_len,
            serializer,
            include,
            exclude,
            Extra { model, ..*extra },
        )?;

        // this is used to include `__pydantic_extra__` in serialization on models
        if let Some(extra_dict) = extra_dict {
            for (key, value) in extra_dict {
                if extra.exclude_none && value.is_none() {
                    continue;
                }
                let filter = self.filter.key_filter(&key, include, exclude).map_err(py_err_se_err)?;
                if let Some((next_include, next_exclude)) = filter {
                    let output_key = infer_json_key(&key, extra).map_err(py_err_se_err)?;
                    let s = SerializeInfer::new(&value, next_include.as_ref(), next_exclude.as_ref(), extra);
                    map.serialize_entry(&output_key, &s)?;
                }
            }
        }

        self.add_computed_fields_json::<S>(model, &mut map, include, exclude, extra)?;
        map.end()
    }

    fn get_name(&self) -> &str {
        "general-fields"
    }
}

fn key_str<'a>(key: &'a Bound<'_, PyAny>) -> PyResult<&'a str> {
    key.downcast::<PyString>()?.to_str()
}

fn dict_items<'py>(
    main_dict: &'_ Bound<'py, PyDict>,
) -> impl Iterator<Item = PyResult<(Bound<'py, PyAny>, Bound<'py, PyAny>)>> {
    // Collect items before iterating to prevent panic on dict mutation.
    // Use a SmallVec to avoid heap allocation for models with a reasonable number of fields.
    let main_items: SmallVec<[_; 16]> = main_dict.iter().collect();
    main_items.into_iter().map(Ok)
}
