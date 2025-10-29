use std::borrow::Cow;
use std::sync::Arc;

use crate::build_tools::py_schema_err;
use crate::serializers::SerializationState;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyType};

use crate::definitions::DefinitionsBuilder;
use crate::serializers::errors::py_err_se_err;
use crate::serializers::infer::{infer_json_key, infer_serialize, infer_to_python};
use crate::tools::SchemaDict;

use super::float::FloatSerializer;
use super::simple::IntSerializer;
use super::string::StrSerializer;
use super::{BuildSerializer, CombinedSerializer, TypeSerializer};

#[derive(Debug)]
pub struct EnumSerializer {
    class: Py<PyType>,
    serializer: Option<Arc<CombinedSerializer>>,
}

impl BuildSerializer for EnumSerializer {
    const EXPECTED_TYPE: &'static str = "enum";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        let sub_type: Option<String> = schema.get_as(intern!(schema.py(), "sub_type"))?;

        let serializer = match sub_type.as_deref() {
            Some("int") => Some(IntSerializer::get().clone()),
            Some("str") => Some(StrSerializer::get().clone()),
            Some("float") => Some(FloatSerializer::get(schema.py(), config)?.clone()),
            Some(_) => return py_schema_err!("`sub_type` must be one of: 'int', 'str', 'float' or None"),
            None => None,
        };
        Ok(CombinedSerializer::Enum(Self {
            class: schema.get_as_req(intern!(schema.py(), "cls"))?,
            serializer,
        })
        .into())
    }
}

impl_py_gc_traverse!(EnumSerializer { serializer });

impl TypeSerializer for EnumSerializer {
    fn to_python<'py>(
        &self,
        value: &Bound<'py, PyAny>,
        state: &mut SerializationState<'_, 'py>,
    ) -> PyResult<Py<PyAny>> {
        let py = value.py();
        if value.is_exact_instance(self.class.bind(py)) {
            // if we're in JSON mode, we need to get the value attribute and serialize that
            if state.extra.mode.is_json() {
                let dot_value = value.getattr(intern!(py, "value"))?;
                match self.serializer {
                    Some(ref s) => s.to_python(&dot_value, state),
                    None => infer_to_python(&dot_value, state),
                }
            } else {
                // if we're not in JSON mode, we assume the value is safe to return directly
                Ok(value.clone().unbind())
            }
        } else {
            state.warn_fallback_py(self.get_name(), value)?;
            infer_to_python(value, state)
        }
    }

    fn json_key<'a, 'py>(
        &self,
        key: &'a Bound<'py, PyAny>,
        state: &mut SerializationState<'_, 'py>,
    ) -> PyResult<Cow<'a, str>> {
        let py = key.py();
        if key.is_exact_instance(self.class.bind(py)) {
            let dot_value = key.getattr(intern!(py, "value"))?;
            let k = match self.serializer {
                Some(ref s) => s.json_key(&dot_value, state),
                None => infer_json_key(&dot_value, state),
            }?;
            // since dot_value is a local reference, we need to allocate it and returned an
            // owned variant of cow.
            Ok(Cow::Owned(k.into_owned()))
        } else {
            state.warn_fallback_py(self.get_name(), key)?;
            infer_json_key(key, state)
        }
    }

    fn serde_serialize<'py, S: serde::ser::Serializer>(
        &self,
        value: &Bound<'py, PyAny>,
        serializer: S,
        state: &mut SerializationState<'_, 'py>,
    ) -> Result<S::Ok, S::Error> {
        if value.is_exact_instance(self.class.bind(value.py())) {
            let dot_value = value.getattr(intern!(value.py(), "value")).map_err(py_err_se_err)?;
            match self.serializer {
                Some(ref s) => s.serde_serialize(&dot_value, serializer, state),
                None => infer_serialize(&dot_value, serializer, state),
            }
        } else {
            state.warn_fallback_ser::<S>(self.get_name(), value)?;
            infer_serialize(value, serializer, state)
        }
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }

    fn retry_with_lax_check(&self) -> bool {
        match self.serializer {
            Some(ref s) => s.retry_with_lax_check(),
            None => false,
        }
    }
}
