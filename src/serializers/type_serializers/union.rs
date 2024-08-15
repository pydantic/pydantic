use ahash::AHashMap as HashMap;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyTuple};
use smallvec::SmallVec;
use std::borrow::Cow;

use crate::build_tools::py_schema_err;
use crate::common::union::{Discriminator, SMALL_UNION_THRESHOLD};
use crate::definitions::DefinitionsBuilder;
use crate::errors::write_truncated_to_50_bytes;
use crate::lookup_key::LookupKey;
use crate::serializers::type_serializers::py_err_se_err;
use crate::tools::{safe_repr, SchemaDict};
use crate::PydanticSerializationUnexpectedValue;

use super::{
    infer_json_key, infer_serialize, infer_to_python, BuildSerializer, CombinedSerializer, Extra, SerCheck,
    TypeSerializer,
};

#[derive(Debug)]
pub struct UnionSerializer {
    choices: Vec<CombinedSerializer>,
    name: String,
}

impl BuildSerializer for UnionSerializer {
    const EXPECTED_TYPE: &'static str = "union";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let py = schema.py();
        let choices: Vec<CombinedSerializer> = schema
            .get_as_req::<Bound<'_, PyList>>(intern!(py, "choices"))?
            .iter()
            .map(|choice| {
                let choice = match choice.downcast::<PyTuple>() {
                    Ok(py_tuple) => py_tuple.get_item(0)?,
                    Err(_) => choice,
                };
                CombinedSerializer::build(choice.downcast()?, config, definitions)
            })
            .collect::<PyResult<Vec<CombinedSerializer>>>()?;

        Self::from_choices(choices)
    }
}

impl UnionSerializer {
    fn from_choices(choices: Vec<CombinedSerializer>) -> PyResult<CombinedSerializer> {
        match choices.len() {
            0 => py_schema_err!("One or more union choices required"),
            1 => Ok(choices.into_iter().next().unwrap()),
            _ => {
                let descr = choices
                    .iter()
                    .map(TypeSerializer::get_name)
                    .collect::<Vec<_>>()
                    .join(", ");
                Ok(Self {
                    choices,
                    name: format!("Union[{descr}]"),
                }
                .into())
            }
        }
    }
}

impl_py_gc_traverse!(UnionSerializer { choices });

fn to_python(
    value: &Bound<'_, PyAny>,
    include: Option<&Bound<'_, PyAny>>,
    exclude: Option<&Bound<'_, PyAny>>,
    extra: &Extra,
    choices: &[CombinedSerializer],
    name: &str,
    retry_with_lax_check: bool,
) -> PyResult<PyObject> {
    // try the serializers in left to right order with error_on fallback=true
    let mut new_extra = extra.clone();
    new_extra.check = SerCheck::Strict;
    let mut errors: SmallVec<[PyErr; SMALL_UNION_THRESHOLD]> = SmallVec::new();

    for comb_serializer in choices {
        match comb_serializer.to_python(value, include, exclude, &new_extra) {
            Ok(v) => return Ok(v),
            Err(err) => match err.is_instance_of::<PydanticSerializationUnexpectedValue>(value.py()) {
                true => (),
                false => errors.push(err),
            },
        }
    }

    if retry_with_lax_check {
        new_extra.check = SerCheck::Lax;
        for comb_serializer in choices {
            match comb_serializer.to_python(value, include, exclude, &new_extra) {
                Ok(v) => return Ok(v),
                Err(err) => match err.is_instance_of::<PydanticSerializationUnexpectedValue>(value.py()) {
                    true => (),
                    false => errors.push(err),
                },
            }
        }
    }

    for err in &errors {
        extra.warnings.custom_warning(err.to_string());
    }

    extra.warnings.on_fallback_py(name, value, extra)?;
    infer_to_python(value, include, exclude, extra)
}

fn json_key<'a>(
    key: &'a Bound<'_, PyAny>,
    extra: &Extra,
    choices: &[CombinedSerializer],
    name: &str,
    retry_with_lax_check: bool,
) -> PyResult<Cow<'a, str>> {
    let mut new_extra = extra.clone();
    new_extra.check = SerCheck::Strict;
    let mut errors: SmallVec<[PyErr; SMALL_UNION_THRESHOLD]> = SmallVec::new();

    for comb_serializer in choices {
        match comb_serializer.json_key(key, &new_extra) {
            Ok(v) => return Ok(v),
            Err(err) => match err.is_instance_of::<PydanticSerializationUnexpectedValue>(key.py()) {
                true => (),
                false => errors.push(err),
            },
        }
    }

    if retry_with_lax_check {
        new_extra.check = SerCheck::Lax;
        for comb_serializer in choices {
            match comb_serializer.json_key(key, &new_extra) {
                Ok(v) => return Ok(v),
                Err(err) => match err.is_instance_of::<PydanticSerializationUnexpectedValue>(key.py()) {
                    true => (),
                    false => errors.push(err),
                },
            }
        }
    }

    for err in &errors {
        extra.warnings.custom_warning(err.to_string());
    }

    extra.warnings.on_fallback_py(name, key, extra)?;
    infer_json_key(key, extra)
}

#[allow(clippy::too_many_arguments)]
fn serde_serialize<S: serde::ser::Serializer>(
    value: &Bound<'_, PyAny>,
    serializer: S,
    include: Option<&Bound<'_, PyAny>>,
    exclude: Option<&Bound<'_, PyAny>>,
    extra: &Extra,
    choices: &[CombinedSerializer],
    name: &str,
    retry_with_lax_check: bool,
) -> Result<S::Ok, S::Error> {
    let py = value.py();
    let mut new_extra = extra.clone();
    new_extra.check = SerCheck::Strict;
    let mut errors: SmallVec<[PyErr; SMALL_UNION_THRESHOLD]> = SmallVec::new();

    for comb_serializer in choices {
        match comb_serializer.to_python(value, include, exclude, &new_extra) {
            Ok(v) => return infer_serialize(v.bind(py), serializer, None, None, extra),
            Err(err) => match err.is_instance_of::<PydanticSerializationUnexpectedValue>(py) {
                true => (),
                false => errors.push(err),
            },
        }
    }

    if retry_with_lax_check {
        new_extra.check = SerCheck::Lax;
        for comb_serializer in choices {
            match comb_serializer.to_python(value, include, exclude, &new_extra) {
                Ok(v) => return infer_serialize(v.bind(py), serializer, None, None, extra),
                Err(err) => match err.is_instance_of::<PydanticSerializationUnexpectedValue>(py) {
                    true => (),
                    false => errors.push(err),
                },
            }
        }
    }

    for err in &errors {
        extra.warnings.custom_warning(err.to_string());
    }

    extra.warnings.on_fallback_ser::<S>(name, value, extra)?;
    infer_serialize(value, serializer, include, exclude, extra)
}

impl TypeSerializer for UnionSerializer {
    fn to_python(
        &self,
        value: &Bound<'_, PyAny>,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        to_python(
            value,
            include,
            exclude,
            extra,
            &self.choices,
            self.get_name(),
            self.retry_with_lax_check(),
        )
    }

    fn json_key<'a>(&self, key: &'a Bound<'_, PyAny>, extra: &Extra) -> PyResult<Cow<'a, str>> {
        json_key(key, extra, &self.choices, self.get_name(), self.retry_with_lax_check())
    }

    fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        value: &Bound<'_, PyAny>,
        serializer: S,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> Result<S::Ok, S::Error> {
        serde_serialize(
            value,
            serializer,
            include,
            exclude,
            extra,
            &self.choices,
            self.get_name(),
            self.retry_with_lax_check(),
        )
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn retry_with_lax_check(&self) -> bool {
        self.choices.iter().any(CombinedSerializer::retry_with_lax_check)
    }
}

#[derive(Debug)]
pub struct TaggedUnionSerializer {
    discriminator: Discriminator,
    lookup: HashMap<String, usize>,
    choices: Vec<CombinedSerializer>,
    name: String,
}

impl BuildSerializer for TaggedUnionSerializer {
    const EXPECTED_TYPE: &'static str = "tagged-union";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let py = schema.py();
        let discriminator = Discriminator::new(py, &schema.get_as_req(intern!(py, "discriminator"))?)?;

        // TODO: guarantee at least 1 choice
        let choices_map: Bound<PyDict> = schema.get_as_req(intern!(py, "choices"))?;
        let mut lookup = HashMap::with_capacity(choices_map.len());
        let mut choices = Vec::with_capacity(choices_map.len());

        for (idx, (choice_key, choice_schema)) in choices_map.into_iter().enumerate() {
            let serializer = CombinedSerializer::build(choice_schema.downcast()?, config, definitions)?;
            choices.push(serializer);
            lookup.insert(choice_key.to_string(), idx);
        }

        let descr = choices
            .iter()
            .map(TypeSerializer::get_name)
            .collect::<Vec<_>>()
            .join(", ");

        Ok(Self {
            discriminator,
            lookup,
            choices,
            name: format!("TaggedUnion[{descr}]"),
        }
        .into())
    }
}

impl_py_gc_traverse!(TaggedUnionSerializer { discriminator, choices });

impl TypeSerializer for TaggedUnionSerializer {
    fn to_python(
        &self,
        value: &Bound<'_, PyAny>,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        let py = value.py();

        let mut new_extra = extra.clone();
        new_extra.check = SerCheck::Strict;

        if let Some(tag) = self.get_discriminator_value(value, extra) {
            let tag_str = tag.to_string();
            if let Some(&serializer_index) = self.lookup.get(&tag_str) {
                let serializer = &self.choices[serializer_index];

                match serializer.to_python(value, include, exclude, &new_extra) {
                    Ok(v) => return Ok(v),
                    Err(err) => match err.is_instance_of::<PydanticSerializationUnexpectedValue>(py) {
                        true => {
                            if self.retry_with_lax_check() {
                                new_extra.check = SerCheck::Lax;
                                return serializer.to_python(value, include, exclude, &new_extra);
                            }
                        }
                        false => return Err(err),
                    },
                }
            }
        }

        to_python(
            value,
            include,
            exclude,
            extra,
            &self.choices,
            self.get_name(),
            self.retry_with_lax_check(),
        )
    }

    fn json_key<'a>(&self, key: &'a Bound<'_, PyAny>, extra: &Extra) -> PyResult<Cow<'a, str>> {
        let py = key.py();
        let mut new_extra = extra.clone();
        new_extra.check = SerCheck::Strict;

        if let Some(tag) = self.get_discriminator_value(key, extra) {
            let tag_str = tag.to_string();
            if let Some(&serializer_index) = self.lookup.get(&tag_str) {
                let serializer = &self.choices[serializer_index];

                match serializer.json_key(key, &new_extra) {
                    Ok(v) => return Ok(v),
                    Err(err) => match err.is_instance_of::<PydanticSerializationUnexpectedValue>(py) {
                        true => {
                            if self.retry_with_lax_check() {
                                new_extra.check = SerCheck::Lax;
                                return serializer.json_key(key, &new_extra);
                            }
                        }
                        false => return Err(err),
                    },
                }
            }
        }

        json_key(key, extra, &self.choices, self.get_name(), self.retry_with_lax_check())
    }

    fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        value: &Bound<'_, PyAny>,
        serializer: S,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> Result<S::Ok, S::Error> {
        let py = value.py();
        let mut new_extra = extra.clone();
        new_extra.check = SerCheck::Strict;

        if let Some(tag) = self.get_discriminator_value(value, extra) {
            let tag_str = tag.to_string();
            if let Some(&serializer_index) = self.lookup.get(&tag_str) {
                let selected_serializer = &self.choices[serializer_index];

                match selected_serializer.to_python(value, include, exclude, &new_extra) {
                    Ok(v) => return infer_serialize(v.bind(py), serializer, None, None, extra),
                    Err(err) => match err.is_instance_of::<PydanticSerializationUnexpectedValue>(py) {
                        true => {
                            if self.retry_with_lax_check() {
                                new_extra.check = SerCheck::Lax;
                                match selected_serializer.to_python(value, include, exclude, &new_extra) {
                                    Ok(v) => return infer_serialize(v.bind(py), serializer, None, None, extra),
                                    Err(err) => return Err(py_err_se_err(err)),
                                }
                            }
                        }
                        false => return Err(py_err_se_err(err)),
                    },
                }
            }
        }

        serde_serialize(
            value,
            serializer,
            include,
            exclude,
            extra,
            &self.choices,
            self.get_name(),
            self.retry_with_lax_check(),
        )
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn retry_with_lax_check(&self) -> bool {
        self.choices.iter().any(CombinedSerializer::retry_with_lax_check)
    }
}

impl TaggedUnionSerializer {
    fn get_discriminator_value(&self, value: &Bound<'_, PyAny>, extra: &Extra) -> Option<Py<PyAny>> {
        let py = value.py();
        let discriminator_value = match &self.discriminator {
            Discriminator::LookupKey(lookup_key) => match lookup_key {
                LookupKey::Simple { py_key, .. } => value.getattr(py_key).ok().map(|obj| obj.to_object(py)),
                _ => None,
            },
            Discriminator::Function(func) => func.call1(py, (value,)).ok(),
        };
        if discriminator_value.is_none() {
            let input_str = safe_repr(value);
            let mut value_str = String::with_capacity(100);
            value_str.push_str("with value `");
            write_truncated_to_50_bytes(&mut value_str, input_str.to_cow()).expect("Writing to a `String` failed");
            value_str.push('`');

            extra.warnings.custom_warning(
                format!(
                    "Failed to get discriminator value for tagged union serialization {value_str} - defaulting to left to right union serialization."
                )
            );
        }
        discriminator_value
    }
}
