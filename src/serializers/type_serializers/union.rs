use ahash::AHashMap as HashMap;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyTuple};
use smallvec::SmallVec;
use std::borrow::Cow;

use crate::build_tools::py_schema_err;
use crate::common::union::{Discriminator, SMALL_UNION_THRESHOLD};
use crate::definitions::DefinitionsBuilder;
use crate::tools::{truncate_safe_repr, SchemaDict};

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
    retry_with_lax_check: bool,
) -> PyResult<PyObject> {
    // try the serializers in left to right order with error_on fallback=true
    let mut new_extra = extra.clone();
    new_extra.check = SerCheck::Strict;
    let mut errors: SmallVec<[PyErr; SMALL_UNION_THRESHOLD]> = SmallVec::new();

    for comb_serializer in choices {
        match comb_serializer.to_python(value, include, exclude, &new_extra) {
            Ok(v) => return Ok(v),
            Err(err) => errors.push(err),
        }
    }

    if retry_with_lax_check {
        new_extra.check = SerCheck::Lax;
        for comb_serializer in choices {
            if let Ok(v) = comb_serializer.to_python(value, include, exclude, &new_extra) {
                return Ok(v);
            }
        }
    }

    for err in &errors {
        extra.warnings.custom_warning(err.to_string());
    }

    infer_to_python(value, include, exclude, extra)
}

fn json_key<'a>(
    key: &'a Bound<'_, PyAny>,
    extra: &Extra,
    choices: &[CombinedSerializer],
    retry_with_lax_check: bool,
) -> PyResult<Cow<'a, str>> {
    let mut new_extra = extra.clone();
    new_extra.check = SerCheck::Strict;
    let mut errors: SmallVec<[PyErr; SMALL_UNION_THRESHOLD]> = SmallVec::new();

    for comb_serializer in choices {
        match comb_serializer.json_key(key, &new_extra) {
            Ok(v) => return Ok(v),
            Err(err) => errors.push(err),
        }
    }

    if retry_with_lax_check {
        new_extra.check = SerCheck::Lax;
        for comb_serializer in choices {
            if let Ok(v) = comb_serializer.json_key(key, &new_extra) {
                return Ok(v);
            }
        }
    }

    for err in &errors {
        extra.warnings.custom_warning(err.to_string());
    }

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
    retry_with_lax_check: bool,
) -> Result<S::Ok, S::Error> {
    let py = value.py();
    let mut new_extra = extra.clone();
    new_extra.check = SerCheck::Strict;
    let mut errors: SmallVec<[PyErr; SMALL_UNION_THRESHOLD]> = SmallVec::new();

    for comb_serializer in choices {
        match comb_serializer.to_python(value, include, exclude, &new_extra) {
            Ok(v) => return infer_serialize(v.bind(py), serializer, None, None, extra),
            Err(err) => errors.push(err),
        }
    }

    if retry_with_lax_check {
        new_extra.check = SerCheck::Lax;
        for comb_serializer in choices {
            if let Ok(v) = comb_serializer.to_python(value, include, exclude, &new_extra) {
                return infer_serialize(v.bind(py), serializer, None, None, extra);
            }
        }
    }

    for err in &errors {
        extra.warnings.custom_warning(err.to_string());
    }

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
            self.retry_with_lax_check(),
        )
    }

    fn json_key<'a>(&self, key: &'a Bound<'_, PyAny>, extra: &Extra) -> PyResult<Cow<'a, str>> {
        json_key(key, extra, &self.choices, self.retry_with_lax_check())
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
        let mut new_extra = extra.clone();
        new_extra.check = SerCheck::Strict;

        if let Some(tag) = self.get_discriminator_value(value, extra) {
            let tag_str = tag.to_string();
            if let Some(&serializer_index) = self.lookup.get(&tag_str) {
                let serializer = &self.choices[serializer_index];

                match serializer.to_python(value, include, exclude, &new_extra) {
                    Ok(v) => return Ok(v),
                    Err(_) => {
                        if self.retry_with_lax_check() {
                            new_extra.check = SerCheck::Lax;
                            if let Ok(v) = serializer.to_python(value, include, exclude, &new_extra) {
                                return Ok(v);
                            }
                        }
                    }
                }
            }
        }

        to_python(
            value,
            include,
            exclude,
            extra,
            &self.choices,
            self.retry_with_lax_check(),
        )
    }

    fn json_key<'a>(&self, key: &'a Bound<'_, PyAny>, extra: &Extra) -> PyResult<Cow<'a, str>> {
        let mut new_extra = extra.clone();
        new_extra.check = SerCheck::Strict;

        if let Some(tag) = self.get_discriminator_value(key, extra) {
            let tag_str = tag.to_string();
            if let Some(&serializer_index) = self.lookup.get(&tag_str) {
                let serializer = &self.choices[serializer_index];

                match serializer.json_key(key, &new_extra) {
                    Ok(v) => return Ok(v),
                    Err(_) => {
                        if self.retry_with_lax_check() {
                            new_extra.check = SerCheck::Lax;
                            if let Ok(v) = serializer.json_key(key, &new_extra) {
                                return Ok(v);
                            }
                        }
                    }
                }
            }
        }

        json_key(key, extra, &self.choices, self.retry_with_lax_check())
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
                    Err(_) => {
                        if self.retry_with_lax_check() {
                            new_extra.check = SerCheck::Lax;
                            if let Ok(v) = selected_serializer.to_python(value, include, exclude, &new_extra) {
                                return infer_serialize(v.bind(py), serializer, None, None, extra);
                            }
                        }
                    }
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
            Discriminator::LookupKey(lookup_key) => lookup_key
                .simple_py_get_attr(value)
                .ok()
                .and_then(|opt| opt.map(|(_, bound)| bound.to_object(py))),
            Discriminator::Function(func) => func.call1(py, (value,)).ok(),
        };
        if discriminator_value.is_none() {
            let value_str = truncate_safe_repr(value, None);
            extra.warnings.custom_warning(
                format!(
                    "Failed to get discriminator value for tagged union serialization with value `{value_str}` - defaulting to left to right union serialization."
                )
            );
        }
        discriminator_value
    }
}
