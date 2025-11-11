use ahash::AHashMap as HashMap;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyTuple};
use smallvec::SmallVec;
use std::borrow::Cow;
use std::sync::Arc;

use crate::build_tools::py_schema_err;
use crate::common::union::{Discriminator, SMALL_UNION_THRESHOLD};
use crate::definitions::DefinitionsBuilder;
use crate::serializers::PydanticSerializationUnexpectedValue;
use crate::serializers::SerializationState;
use crate::tools::SchemaDict;

use super::{
    infer_json_key, infer_serialize, infer_to_python, BuildSerializer, CombinedSerializer, SerCheck, TypeSerializer,
};

#[derive(Debug)]
pub struct UnionSerializer {
    choices: Vec<Arc<CombinedSerializer>>,
    name: String,
}

impl BuildSerializer for UnionSerializer {
    const EXPECTED_TYPE: &'static str = "union";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        let py = schema.py();
        let choices = schema
            .get_as_req::<Bound<'_, PyList>>(intern!(py, "choices"))?
            .iter()
            .map(|choice| {
                let choice = match choice.cast::<PyTuple>() {
                    Ok(py_tuple) => py_tuple.get_item(0)?,
                    Err(_) => choice,
                };
                CombinedSerializer::build(choice.cast()?, config, definitions)
            })
            .collect::<PyResult<_>>()?;

        Self::from_choices(choices)
    }
}

impl UnionSerializer {
    fn from_choices(choices: Vec<Arc<CombinedSerializer>>) -> PyResult<Arc<CombinedSerializer>> {
        match choices.len() {
            0 => py_schema_err!("One or more union choices required"),
            1 => Ok(choices.into_iter().next().unwrap()),
            _ => {
                let descr = choices.iter().map(|v| v.get_name()).collect::<Vec<_>>().join(", ");
                Ok(CombinedSerializer::Union(Self {
                    choices,
                    name: format!("Union[{descr}]"),
                })
                .into())
            }
        }
    }
}

impl_py_gc_traverse!(UnionSerializer { choices });

fn union_serialize<'py, S>(
    // if this returns `Ok(Some(v))`, we picked a union variant to serialize,
    // Or `Ok(None)` if we couldn't find a suitable variant to serialize
    // Finally, `Err(err)` if we encountered errors while trying to serialize
    mut selector: impl FnMut(&CombinedSerializer, &mut SerializationState<'_, 'py>) -> PyResult<S>,
    state: &mut SerializationState<'_, 'py>,
    choices: &[Arc<CombinedSerializer>],
    retry_with_lax_check: bool,
    py: Python<'_>,
) -> PyResult<Option<S>> {
    // try the serializers in left to right order with strict checking
    let mut errors: SmallVec<[PyErr; SMALL_UNION_THRESHOLD]> = SmallVec::new();

    {
        let state = &mut state.scoped_set(|s| &mut s.check, SerCheck::Strict);
        for comb_serializer in choices {
            match selector(comb_serializer, state) {
                Ok(v) => return Ok(Some(v)),
                Err(err) => errors.push(err),
            }
        }
    }

    // If state.check is SerCheck::Strict, we're in a nested union
    if state.check != SerCheck::Strict && retry_with_lax_check {
        let state = &mut state.scoped_set(|s| &mut s.check, SerCheck::Lax);
        for comb_serializer in choices {
            if let Ok(v) = selector(comb_serializer, state) {
                return Ok(Some(v));
            }
        }
    }

    // If state.check is SerCheck::None, we're in a top-level union. We should thus raise the warnings
    if state.check == SerCheck::None {
        for err in &errors {
            if err.is_instance_of::<PydanticSerializationUnexpectedValue>(py) {
                let pydantic_err: PydanticSerializationUnexpectedValue = err.value(py).extract()?;
                state.warnings.register_warning(pydantic_err);
            } else {
                state
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
    fn to_python<'py>(
        &self,
        value: &Bound<'py, PyAny>,
        state: &mut SerializationState<'_, 'py>,
    ) -> PyResult<Py<PyAny>> {
        union_serialize(
            |comb_serializer, state| comb_serializer.to_python(value, state),
            state,
            &self.choices,
            self.retry_with_lax_check(),
            value.py(),
        )?
        .map_or_else(|| infer_to_python(value, state), Ok)
    }

    fn json_key<'a, 'py>(
        &self,
        key: &'a Bound<'py, PyAny>,
        state: &mut SerializationState<'_, 'py>,
    ) -> PyResult<Cow<'a, str>> {
        union_serialize(
            |comb_serializer, state| comb_serializer.json_key(key, state),
            state,
            &self.choices,
            self.retry_with_lax_check(),
            key.py(),
        )?
        .map_or_else(|| infer_json_key(key, state), Ok)
    }

    fn serde_serialize<'py, S: serde::ser::Serializer>(
        &self,
        value: &Bound<'py, PyAny>,
        serializer: S,
        state: &mut SerializationState<'_, 'py>,
    ) -> Result<S::Ok, S::Error> {
        match union_serialize(
            |comb_serializer, state| comb_serializer.to_python(value, state),
            state,
            &self.choices,
            self.retry_with_lax_check(),
            value.py(),
        ) {
            Ok(Some(v)) => {
                let state = &mut state.scoped_include_exclude(None, None);
                infer_serialize(v.bind(value.py()), serializer, state)
            }
            Ok(None) => infer_serialize(value, serializer, state),
            Err(err) => Err(serde::ser::Error::custom(err.to_string())),
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn retry_with_lax_check(&self) -> bool {
        self.choices.iter().any(|c| c.retry_with_lax_check())
    }
}

#[derive(Debug)]
pub struct TaggedUnionSerializer {
    discriminator: Discriminator,
    lookup: HashMap<String, usize>,
    choices: Vec<Arc<CombinedSerializer>>,
    name: String,
}

impl BuildSerializer for TaggedUnionSerializer {
    const EXPECTED_TYPE: &'static str = "tagged-union";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        let py = schema.py();
        let discriminator = Discriminator::new(py, &schema.get_as_req(intern!(py, "discriminator"))?)?;

        // TODO: guarantee at least 1 choice
        let choices_map: Bound<PyDict> = schema.get_as_req(intern!(py, "choices"))?;
        let mut lookup = HashMap::with_capacity(choices_map.len());
        let mut choices = Vec::with_capacity(choices_map.len());

        for (idx, (choice_key, choice_schema)) in choices_map.into_iter().enumerate() {
            let serializer = CombinedSerializer::build(choice_schema.cast()?, config, definitions)?;
            choices.push(serializer);
            lookup.insert(choice_key.to_string(), idx);
        }

        let descr = choices.iter().map(|s| s.get_name()).collect::<Vec<_>>().join(", ");

        Ok(CombinedSerializer::TaggedUnion(Self {
            discriminator,
            lookup,
            choices,
            name: format!("TaggedUnion[{descr}]"),
        })
        .into())
    }
}

impl_py_gc_traverse!(TaggedUnionSerializer { discriminator, choices });

impl TypeSerializer for TaggedUnionSerializer {
    fn to_python<'py>(
        &self,
        value: &Bound<'py, PyAny>,
        state: &mut SerializationState<'_, 'py>,
    ) -> PyResult<Py<PyAny>> {
        self.tagged_union_serialize(
            value,
            |comb_serializer, state| comb_serializer.to_python(value, state),
            state,
        )?
        .map_or_else(|| infer_to_python(value, state), Ok)
    }

    fn json_key<'a, 'py>(
        &self,
        key: &'a Bound<'py, PyAny>,
        state: &mut SerializationState<'_, 'py>,
    ) -> PyResult<Cow<'a, str>> {
        self.tagged_union_serialize(
            key,
            |comb_serializer, state| comb_serializer.json_key(key, state),
            state,
        )?
        .map_or_else(|| infer_json_key(key, state), Ok)
    }

    fn serde_serialize<'py, S: serde::ser::Serializer>(
        &self,
        value: &Bound<'py, PyAny>,
        serializer: S,
        state: &mut SerializationState<'_, 'py>,
    ) -> Result<S::Ok, S::Error> {
        match self.tagged_union_serialize(
            value,
            |comb_serializer, state| comb_serializer.to_python(value, state),
            state,
        ) {
            Ok(Some(v)) => {
                let state = &mut state.scoped_include_exclude(None, None);
                infer_serialize(v.bind(value.py()), serializer, state)
            }
            Ok(None) => infer_serialize(value, serializer, state),
            Err(err) => Err(serde::ser::Error::custom(err.to_string())),
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn retry_with_lax_check(&self) -> bool {
        self.choices.iter().any(|c| c.retry_with_lax_check())
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
                if let Ok(value_dict) = value.cast::<PyDict>() {
                    lookup_key.py_get_dict_item(value_dict).ok().flatten()
                } else {
                    lookup_key.simple_py_get_attr(value).ok().flatten()
                }
                .map(|(_, tag)| tag)
            }
            Discriminator::Function(func) => func.bind(py).call1((value,)).ok(),
        }
    }

    fn tagged_union_serialize<'py, S>(
        &self,
        value: &Bound<'py, PyAny>,
        // if this returns `Ok(v)`, we picked a union variant to serialize, where
        // `S` is intermediate state which can be passed on to the finalizer
        mut selector: impl FnMut(&CombinedSerializer, &mut SerializationState<'_, 'py>) -> PyResult<S>,
        state: &mut SerializationState<'_, 'py>,
    ) -> PyResult<Option<S>> {
        if let Some(tag) = self.get_discriminator_value(value) {
            let state = &mut state.scoped_set(|s| &mut s.check, SerCheck::Strict);

            let tag_str = tag.to_string();
            if let Some(&serializer_index) = self.lookup.get(&tag_str) {
                let selected_serializer = &self.choices[serializer_index];

                match selector(selected_serializer, state) {
                    Ok(v) => return Ok(Some(v)),
                    Err(_) => {
                        if self.retry_with_lax_check() {
                            let state = &mut state.scoped_set(|s| &mut s.check, SerCheck::Lax);
                            if let Ok(v) = selector(selected_serializer, state) {
                                return Ok(Some(v));
                            }
                        }
                    }
                }
            }
        } else if state.check == SerCheck::None {
            // If state.check is SerCheck::None, we're in a top-level union. We should thus raise
            // this warning
            state.warnings.register_warning(
                PydanticSerializationUnexpectedValue::new(
                    Some("Defaulting to left to right union serialization - failed to get discriminator value for tagged union serialization".to_string()),
                    None,
                    None,
                    Some(value.clone().unbind()),
                )
            );
        }

        // if we haven't returned at this point, we should fallback to the union serializer
        // which preserves the historical expectation that we do our best with serialization
        // even if that means we resort to inference
        union_serialize(selector, state, &self.choices, self.retry_with_lax_check(), value.py())
    }
}
