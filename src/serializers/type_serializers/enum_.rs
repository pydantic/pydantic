use std::borrow::Cow;

use crate::build_tools::py_schema_err;
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
use super::{BuildSerializer, CombinedSerializer, Extra, TypeSerializer};

#[derive(Debug, Clone)]
pub struct EnumSerializer {
    class: Py<PyType>,
    serializer: Option<Box<CombinedSerializer>>,
}

impl BuildSerializer for EnumSerializer {
    const EXPECTED_TYPE: &'static str = "enum";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let sub_type: Option<String> = schema.get_as(intern!(schema.py(), "sub_type"))?;

        let serializer = match sub_type.as_deref() {
            Some("int") => Some(Box::new(IntSerializer::new().into())),
            Some("str") => Some(Box::new(StrSerializer::new().into())),
            Some("float") => Some(Box::new(FloatSerializer::new(schema.py(), config)?.into())),
            Some(_) => return py_schema_err!("`sub_type` must be one of: 'int', 'str', 'float' or None"),
            None => None,
        };
        Ok(Self {
            class: schema.get_as_req(intern!(schema.py(), "cls"))?,
            serializer,
        }
        .into())
    }
}

impl_py_gc_traverse!(EnumSerializer { serializer });

impl TypeSerializer for EnumSerializer {
    fn to_python(
        &self,
        value: &Bound<'_, PyAny>,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        let py = value.py();
        if value.is_exact_instance(self.class.bind(py)) {
            // if we're in JSON mode, we need to get the value attribute and serialize that
            if extra.mode.is_json() {
                let dot_value = value.getattr(intern!(py, "value"))?;
                match self.serializer {
                    Some(ref s) => s.to_python(&dot_value, include, exclude, extra),
                    None => infer_to_python(&dot_value, include, exclude, extra),
                }
            } else {
                // if we're not in JSON mode, we assume the value is safe to return directly
                Ok(value.into_py(py))
            }
        } else {
            extra.warnings.on_fallback_py(self.get_name(), value, extra)?;
            infer_to_python(value, include, exclude, extra)
        }
    }

    fn json_key<'a>(&self, key: &'a Bound<'_, PyAny>, extra: &Extra) -> PyResult<Cow<'a, str>> {
        let py = key.py();
        if key.is_exact_instance(self.class.bind(py)) {
            let dot_value = key.getattr(intern!(py, "value"))?;
            let k = match self.serializer {
                Some(ref s) => s.json_key(&dot_value, extra),
                None => infer_json_key(&dot_value, extra),
            }?;
            // since dot_value is a local reference, we need to allocate it and returned an
            // owned variant of cow.
            Ok(Cow::Owned(k.into_owned()))
        } else {
            extra.warnings.on_fallback_py(self.get_name(), key, extra)?;
            infer_json_key(key, extra)
        }
    }

    fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        value: &Bound<'_, PyAny>,
        serializer: S,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> Result<S::Ok, S::Error> {
        if value.is_exact_instance(self.class.bind(value.py())) {
            let dot_value = value.getattr(intern!(value.py(), "value")).map_err(py_err_se_err)?;
            match self.serializer {
                Some(ref s) => s.serde_serialize(&dot_value, serializer, include, exclude, extra),
                None => infer_serialize(&dot_value, serializer, include, exclude, extra),
            }
        } else {
            extra.warnings.on_fallback_ser::<S>(self.get_name(), value, extra)?;
            infer_serialize(value, serializer, include, exclude, extra)
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
