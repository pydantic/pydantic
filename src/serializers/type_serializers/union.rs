use ahash::AHashMap as HashMap;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyTuple};
use smallvec::SmallVec;
use std::borrow::Cow;

use crate::build_tools::py_schema_err;
use crate::common::union::{Discriminator, SMALL_UNION_THRESHOLD};
use crate::definitions::DefinitionsBuilder;
use crate::serializers::PydanticSerializationUnexpectedValue;
use crate::tools::SchemaDict;

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

fn union_serialize<S>(
    // if this returns `Ok(Some(v))`, we picked a union variant to serialize,
    // Or `Ok(None)` if we couldn't find a suitable variant to serialize
    // Finally, `Err(err)` if we encountered errors while trying to serialize
    mut selector: impl FnMut(&CombinedSerializer, &Extra) -> PyResult<S>,
    extra: &Extra,
    choices: &[CombinedSerializer],
    retry_with_lax_check: bool,
    py: Python<'_>,
) -> PyResult<Option<S>> {
    // try the serializers in left to right order with error_on fallback=true
    let mut new_extra = extra.clone();
    new_extra.check = SerCheck::Strict;
    let mut errors: SmallVec<[PyErr; SMALL_UNION_THRESHOLD]> = SmallVec::new();

    for comb_serializer in choices {
        match selector(comb_serializer, &new_extra) {
            Ok(v) => return Ok(Some(v)),
            Err(err) => errors.push(err),
        }
    }

    // If extra.check is SerCheck::Strict, we're in a nested union
    if extra.check != SerCheck::Strict && retry_with_lax_check {
        new_extra.check = SerCheck::Lax;
        for comb_serializer in choices {
            if let Ok(v) = selector(comb_serializer, &new_extra) {
                return Ok(Some(v));
            }
        }
    }

    // If extra.check is SerCheck::None, we're in a top-level union. We should thus raise the warnings
    if extra.check == SerCheck::None {
        for err in &errors {
            if err.is_instance_of::<PydanticSerializationUnexpectedValue>(py) {
                let pydantic_err: PydanticSerializationUnexpectedValue = err.value(py).extract()?;
                extra.warnings.register_warning(pydantic_err);
            } else {
                extra
                    .warnings
                    .register_warning(PydanticSerializationUnexpectedValue::new_from_msg(Some(
                        err.to_string(),
                    )));
            }
        }
    }
    // Otherwise, if we've encountered errors, return them to the parent union, which should take
    // care of the formatting for us
    else if !errors.is_empty() {
        let message = errors.iter().map(ToString::to_string).collect::<Vec<_>>().join("\n");
        return Err(PydanticSerializationUnexpectedValue::new_from_msg(Some(message)).to_py_err());
    }

    Ok(None)
}

impl TypeSerializer for UnionSerializer {
    fn to_python(
        &self,
        value: &Bound<'_, PyAny>,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        union_serialize(
            |comb_serializer, new_extra| comb_serializer.to_python(value, include, exclude, new_extra),
            extra,
            &self.choices,
            self.retry_with_lax_check(),
            value.py(),
        )?
        .map_or_else(|| infer_to_python(value, include, exclude, extra), Ok)
    }

    fn json_key<'a>(&self, key: &'a Bound<'_, PyAny>, extra: &Extra) -> PyResult<Cow<'a, str>> {
        union_serialize(
            |comb_serializer, new_extra| comb_serializer.json_key(key, new_extra),
            extra,
            &self.choices,
            self.retry_with_lax_check(),
            key.py(),
        )?
        .map_or_else(|| infer_json_key(key, extra), Ok)
    }

    fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        value: &Bound<'_, PyAny>,
        serializer: S,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> Result<S::Ok, S::Error> {
        match union_serialize(
            |comb_serializer, new_extra| comb_serializer.to_python(value, include, exclude, new_extra),
            extra,
            &self.choices,
            self.retry_with_lax_check(),
            value.py(),
        ) {
            Ok(Some(v)) => infer_serialize(v.bind(value.py()), serializer, None, None, extra),
            Ok(None) => infer_serialize(value, serializer, include, exclude, extra),
            Err(err) => Err(serde::ser::Error::custom(err.to_string())),
        }
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
        self.tagged_union_serialize(
            value,
            |comb_serializer: &CombinedSerializer, new_extra: &Extra| {
                comb_serializer.to_python(value, include, exclude, new_extra)
            },
            extra,
        )?
        .map_or_else(|| infer_to_python(value, include, exclude, extra), Ok)
    }

    fn json_key<'a>(&self, key: &'a Bound<'_, PyAny>, extra: &Extra) -> PyResult<Cow<'a, str>> {
        self.tagged_union_serialize(
            key,
            |comb_serializer: &CombinedSerializer, new_extra: &Extra| comb_serializer.json_key(key, new_extra),
            extra,
        )?
        .map_or_else(|| infer_json_key(key, extra), Ok)
    }

    fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        value: &Bound<'_, PyAny>,
        serializer: S,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> Result<S::Ok, S::Error> {
        match self.tagged_union_serialize(
            value,
            |comb_serializer: &CombinedSerializer, new_extra: &Extra| {
                comb_serializer.to_python(value, include, exclude, new_extra)
            },
            extra,
        ) {
            Ok(Some(v)) => infer_serialize(v.bind(value.py()), serializer, None, None, extra),
            Ok(None) => infer_serialize(value, serializer, include, exclude, extra),
            Err(err) => Err(serde::ser::Error::custom(err.to_string())),
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn retry_with_lax_check(&self) -> bool {
        self.choices.iter().any(CombinedSerializer::retry_with_lax_check)
    }
}

impl TaggedUnionSerializer {
    fn get_discriminator_value<'py>(&self, value: &Bound<'py, PyAny>) -> Option<Bound<'py, PyAny>> {
        let py = value.py();
        match &self.discriminator {
            Discriminator::LookupKey(lookup_key) => {
                // we're pretty lax here, we allow either dict[key] or object.key, as we very well could
                // be doing a discriminator lookup on a typed dict, and there's no good way to check that
                // at this point. we could be more strict and only do this in lax mode...
                if let Ok(value_dict) = value.downcast::<PyDict>() {
                    lookup_key.py_get_dict_item(value_dict).ok().flatten()
                } else {
                    lookup_key.simple_py_get_attr(value).ok().flatten()
                }
                .map(|(_, tag)| tag)
            }
            Discriminator::Function(func) => func.bind(py).call1((value,)).ok(),
        }
    }

    fn tagged_union_serialize<S>(
        &self,
        value: &Bound<'_, PyAny>,
        // if this returns `Ok(v)`, we picked a union variant to serialize, where
        // `S` is intermediate state which can be passed on to the finalizer
        mut selector: impl FnMut(&CombinedSerializer, &Extra) -> PyResult<S>,
        extra: &Extra,
    ) -> PyResult<Option<S>> {
        if let Some(tag) = self.get_discriminator_value(value) {
            let mut new_extra = extra.clone();
            new_extra.check = SerCheck::Strict;

            let tag_str = tag.to_string();
            if let Some(&serializer_index) = self.lookup.get(&tag_str) {
                let selected_serializer = &self.choices[serializer_index];

                match selector(selected_serializer, &new_extra) {
                    Ok(v) => return Ok(Some(v)),
                    Err(_) => {
                        if self.retry_with_lax_check() {
                            new_extra.check = SerCheck::Lax;
                            if let Ok(v) = selector(selected_serializer, &new_extra) {
                                return Ok(Some(v));
                            }
                        }
                    }
                }
            }
        } else if extra.check == SerCheck::None {
            // If extra.check is SerCheck::None, we're in a top-level union. We should thus raise
            // this warning
            extra.warnings.register_warning(
                PydanticSerializationUnexpectedValue::new(
                    Some("Defaulting to left to right union serialization - failed to get discriminator value for tagged union serialization".to_string()),
                    None,
                    Some(value.clone().unbind()),
                )
            );
        }

        // if we haven't returned at this point, we should fallback to the union serializer
        // which preserves the historical expectation that we do our best with serialization
        // even if that means we resort to inference
        union_serialize(selector, extra, &self.choices, self.retry_with_lax_check(), value.py())
    }
}
