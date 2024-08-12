use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyTuple};
use smallvec::SmallVec;
use std::borrow::Cow;

use crate::build_tools::py_schema_err;
use crate::definitions::DefinitionsBuilder;
use crate::tools::{SchemaDict, UNION_ERR_SMALLVEC_CAPACITY};
use crate::PydanticSerializationUnexpectedValue;

use super::{
    infer_json_key, infer_serialize, infer_to_python, BuildSerializer, CombinedSerializer, Extra, SerCheck,
    TypeSerializer,
};

#[derive(Debug, Clone)]
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

impl TypeSerializer for UnionSerializer {
    fn to_python(
        &self,
        value: &Bound<'_, PyAny>,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        // try the serializers in left to right order with error_on fallback=true
        let mut new_extra = extra.clone();
        new_extra.check = SerCheck::Strict;
        let mut errors: SmallVec<[PyErr; UNION_ERR_SMALLVEC_CAPACITY]> = SmallVec::new();

        for comb_serializer in &self.choices {
            match comb_serializer.to_python(value, include, exclude, &new_extra) {
                Ok(v) => return Ok(v),
                Err(err) => match err.is_instance_of::<PydanticSerializationUnexpectedValue>(value.py()) {
                    true => (),
                    false => errors.push(err),
                },
            }
        }
        if self.retry_with_lax_check() {
            new_extra.check = SerCheck::Lax;
            for comb_serializer in &self.choices {
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

        extra.warnings.on_fallback_py(self.get_name(), value, extra)?;
        infer_to_python(value, include, exclude, extra)
    }

    fn json_key<'a>(&self, key: &'a Bound<'_, PyAny>, extra: &Extra) -> PyResult<Cow<'a, str>> {
        let mut new_extra = extra.clone();
        new_extra.check = SerCheck::Strict;
        let mut errors: SmallVec<[PyErr; UNION_ERR_SMALLVEC_CAPACITY]> = SmallVec::new();

        for comb_serializer in &self.choices {
            match comb_serializer.json_key(key, &new_extra) {
                Ok(v) => return Ok(v),
                Err(err) => match err.is_instance_of::<PydanticSerializationUnexpectedValue>(key.py()) {
                    true => (),
                    false => errors.push(err),
                },
            }
        }
        if self.retry_with_lax_check() {
            new_extra.check = SerCheck::Lax;
            for comb_serializer in &self.choices {
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

        extra.warnings.on_fallback_py(self.get_name(), key, extra)?;
        infer_json_key(key, extra)
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
        let mut errors: SmallVec<[PyErr; UNION_ERR_SMALLVEC_CAPACITY]> = SmallVec::new();

        for comb_serializer in &self.choices {
            match comb_serializer.to_python(value, include, exclude, &new_extra) {
                Ok(v) => return infer_serialize(v.bind(py), serializer, None, None, extra),
                Err(err) => match err.is_instance_of::<PydanticSerializationUnexpectedValue>(value.py()) {
                    true => (),
                    false => errors.push(err),
                },
            }
        }
        if self.retry_with_lax_check() {
            new_extra.check = SerCheck::Lax;
            for comb_serializer in &self.choices {
                match comb_serializer.to_python(value, include, exclude, &new_extra) {
                    Ok(v) => return infer_serialize(v.bind(py), serializer, None, None, extra),
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

        extra.warnings.on_fallback_ser::<S>(self.get_name(), value, extra)?;
        infer_serialize(value, serializer, include, exclude, extra)
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn retry_with_lax_check(&self) -> bool {
        self.choices.iter().any(CombinedSerializer::retry_with_lax_check)
    }
}

pub struct TaggedUnionBuilder;

impl BuildSerializer for TaggedUnionBuilder {
    const EXPECTED_TYPE: &'static str = "tagged-union";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let schema_choices: Bound<'_, PyDict> = schema.get_as_req(intern!(schema.py(), "choices"))?;
        let mut choices: Vec<CombinedSerializer> = Vec::with_capacity(schema_choices.len());

        for (_, value) in schema_choices {
            if let Ok(choice_schema) = value.downcast::<PyDict>() {
                choices.push(CombinedSerializer::build(choice_schema, config, definitions)?);
            }
        }
        UnionSerializer::from_choices(choices)
    }
}
