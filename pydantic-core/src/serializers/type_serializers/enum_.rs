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
    use_enum_name: bool,
}

impl BuildSerializer for EnumSerializer {
    const EXPECTED_TYPE: &'static str = "enum";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        let py = schema.py();
        let use_enum_name: bool = schema.get_as(intern!(py, "use_enum_name"))?.unwrap_or(false);
        let sub_type: Option<String> = schema.get_as(intern!(py, "sub_type"))?;

        let serializer = match sub_type.as_deref() {
            Some("int") => Some(IntSerializer::get().clone()),
            Some("str") => Some(StrSerializer::get().clone()),
            Some("float") => Some(FloatSerializer::get(py, config)?.clone()),
            Some(_) => return py_schema_err!("`sub_type` must be one of: 'int', 'str', 'float' or None"),
            None => None,
        };
        Ok(CombinedSerializer::Enum(Self {
            class: schema.get_as_req(intern!(py, "cls"))?,
            serializer,
            use_enum_name,
        })
        .into())
    }
}

impl_py_gc_traverse!(EnumSerializer { serializer });

impl TypeSerializer for EnumSerializer {
    fn to_python<'py>(&self, value: &Bound<'py, PyAny>, state: &mut SerializationState<'py>) -> PyResult<Py<PyAny>> {
        let py = value.py();
        if value.is_exact_instance(self.class.bind(py)) {
            let attr = if self.use_enum_name {
                intern!(py, "name")
            } else {
                intern!(py, "value")
            };
            if state.extra.mode.is_json() {
                let dot_attr = value.getattr(attr)?;
                match self.serializer {
                    Some(ref s) => s.to_python(&dot_attr, state),
                    None => infer_to_python(&dot_attr, state),
                }
            } else if self.use_enum_name {
                let dot_attr = value.getattr(attr)?;
                Ok(dot_attr.unbind())
            } else {
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
        state: &mut SerializationState<'py>,
    ) -> PyResult<Cow<'a, str>> {
        let py = key.py();
        if key.is_exact_instance(self.class.bind(py)) {
            let attr = if self.use_enum_name {
                intern!(py, "name")
            } else {
                intern!(py, "value")
            };
            let dot_attr = key.getattr(attr)?;
            let k = match self.serializer {
                Some(ref s) => s.json_key(&dot_attr, state),
                None => infer_json_key(&dot_attr, state),
            }?;
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
        state: &mut SerializationState<'py>,
    ) -> Result<S::Ok, S::Error> {
        let py = value.py();
        if value.is_exact_instance(self.class.bind(py)) {
            let attr = if self.use_enum_name {
                intern!(py, "name")
            } else {
                intern!(py, "value")
            };
            let dot_attr = value.getattr(attr).map_err(py_err_se_err)?;
            match self.serializer {
                Some(ref s) => s.serde_serialize(&dot_attr, serializer, state),
                None => infer_serialize(&dot_attr, serializer, state),
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
