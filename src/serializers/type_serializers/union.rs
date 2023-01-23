use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use std::borrow::Cow;

use crate::build_context::BuildContext;
use crate::build_tools::{py_err, SchemaDict};
use crate::serializers::extra::SerCheck;
use crate::PydanticSerializationUnexpectedValue;

use super::{
    infer_json_key, infer_serialize, infer_to_python, py_err_se_err, BuildSerializer, CombinedSerializer, Extra,
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
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let py = schema.py();
        let choices: Vec<CombinedSerializer> = schema
            .get_as_req::<&PyList>(intern!(py, "choices"))?
            .iter()
            .map(|choice| CombinedSerializer::build(choice.downcast()?, config, build_context))
            .collect::<PyResult<Vec<CombinedSerializer>>>()?;

        Self::from_choices(choices)
    }
}

impl UnionSerializer {
    fn from_choices(choices: Vec<CombinedSerializer>) -> PyResult<CombinedSerializer> {
        match choices.len() {
            0 => py_err!("One or more union choices required"),
            1 => Ok(choices.into_iter().next().unwrap()),
            _ => {
                let descr = choices.iter().map(|v| v.get_name()).collect::<Vec<_>>().join(", ");
                Ok(Self {
                    choices,
                    name: format!("Union[{descr}]"),
                }
                .into())
            }
        }
    }
}

impl TypeSerializer for UnionSerializer {
    fn to_python(
        &self,
        value: &PyAny,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        // try the serializers in with error_on fallback=true
        let mut new_extra = extra.clone();
        new_extra.check = SerCheck::Strict;
        for comb_serializer in &self.choices {
            match comb_serializer.to_python(value, include, exclude, &new_extra) {
                Ok(v) => return Ok(v),
                Err(err) => match err.is_instance_of::<PydanticSerializationUnexpectedValue>(value.py()) {
                    true => (),
                    false => return Err(err),
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
                        false => return Err(err),
                    },
                }
            }
        }

        extra.warnings.on_fallback_py(self.get_name(), value, extra)?;
        infer_to_python(value, include, exclude, extra)
    }

    fn json_key<'py>(&self, key: &'py PyAny, extra: &Extra) -> PyResult<Cow<'py, str>> {
        let mut new_extra = extra.clone();
        new_extra.check = SerCheck::Strict;
        for comb_serializer in &self.choices {
            match comb_serializer.json_key(key, &new_extra) {
                Ok(v) => return Ok(v),
                Err(err) => match err.is_instance_of::<PydanticSerializationUnexpectedValue>(key.py()) {
                    true => (),
                    false => return Err(err),
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
                        false => return Err(err),
                    },
                }
            }
        }

        extra.warnings.on_fallback_py(self.get_name(), key, extra)?;
        infer_json_key(key, extra)
    }

    fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        value: &PyAny,
        serializer: S,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> Result<S::Ok, S::Error> {
        let py = value.py();
        let mut new_extra = extra.clone();
        new_extra.check = SerCheck::Strict;
        for comb_serializer in &self.choices {
            match comb_serializer.to_python(value, include, exclude, &new_extra) {
                Ok(v) => return infer_serialize(v.as_ref(py), serializer, None, None, extra),
                Err(err) => match err.is_instance_of::<PydanticSerializationUnexpectedValue>(py) {
                    true => (),
                    false => return Err(py_err_se_err(err)),
                },
            }
        }
        if self.retry_with_lax_check() {
            new_extra.check = SerCheck::Lax;
            for comb_serializer in &self.choices {
                match comb_serializer.to_python(value, include, exclude, &new_extra) {
                    Ok(v) => return infer_serialize(v.as_ref(py), serializer, None, None, extra),
                    Err(err) => match err.is_instance_of::<PydanticSerializationUnexpectedValue>(py) {
                        true => (),
                        false => return Err(py_err_se_err(err)),
                    },
                }
            }
        }

        extra.warnings.on_fallback_ser::<S>(self.get_name(), value, extra)?;
        infer_serialize(value, serializer, include, exclude, extra)
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn retry_with_lax_check(&self) -> bool {
        self.choices.iter().any(|c| c.retry_with_lax_check())
    }
}

pub struct TaggedUnionBuilder;

impl BuildSerializer for TaggedUnionBuilder {
    const EXPECTED_TYPE: &'static str = "tagged-union";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let schema_choices: &PyDict = schema.get_as_req(intern!(schema.py(), "choices"))?;
        let mut choices: Vec<CombinedSerializer> = Vec::with_capacity(schema_choices.len());

        for (_, value) in schema_choices {
            if let Ok(choice_schema) = value.downcast::<PyDict>() {
                choices.push(CombinedSerializer::build(choice_schema, config, build_context)?)
            }
        }
        UnionSerializer::from_choices(choices)
    }
}
