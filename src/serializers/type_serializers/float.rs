use pyo3::types::PyDict;
use pyo3::{intern, prelude::*};

use std::borrow::Cow;

use serde::Serializer;

use crate::definitions::DefinitionsBuilder;
use crate::serializers::config::InfNanMode;
use crate::tools::SchemaDict;

use super::simple::to_str_json_key;
use super::{
    infer_json_key, infer_serialize, infer_to_python, BuildSerializer, CombinedSerializer, Extra, IsType, ObType,
    SerMode, TypeSerializer,
};

#[derive(Debug, Clone)]
pub struct FloatSerializer {
    inf_nan_mode: InfNanMode,
}

impl FloatSerializer {
    pub fn new(py: Python, config: Option<&Bound<'_, PyDict>>) -> PyResult<Self> {
        let inf_nan_mode = config
            .and_then(|c| c.get_as(intern!(py, "ser_json_inf_nan")).transpose())
            .transpose()?
            .unwrap_or_default();
        Ok(Self { inf_nan_mode })
    }
}

pub fn serialize_f64<S: Serializer>(v: f64, serializer: S, inf_nan_mode: InfNanMode) -> Result<S::Ok, S::Error> {
    if v.is_nan() || v.is_infinite() {
        match inf_nan_mode {
            InfNanMode::Null => serializer.serialize_none(),
            InfNanMode::Constants => serializer.serialize_f64(v),
            InfNanMode::Strings => {
                if v.is_nan() {
                    serializer.serialize_str("NaN")
                } else {
                    serializer.serialize_str(if v.is_sign_positive() { "Infinity" } else { "-Infinity" })
                }
            }
        }
    } else {
        serializer.serialize_f64(v)
    }
}

impl BuildSerializer for FloatSerializer {
    const EXPECTED_TYPE: &'static str = "float";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        Self::new(schema.py(), config).map(Into::into)
    }
}

impl_py_gc_traverse!(FloatSerializer {});

impl TypeSerializer for FloatSerializer {
    fn to_python(
        &self,
        value: &Bound<'_, PyAny>,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        let py = value.py();
        match extra.ob_type_lookup.is_type(value, ObType::Float) {
            IsType::Exact => Ok(value.into_py(py)),
            IsType::Subclass => match extra.mode {
                SerMode::Json => {
                    let rust_value = value.extract::<f64>()?;
                    Ok(rust_value.to_object(py))
                }
                _ => infer_to_python(value, include, exclude, extra),
            },
            IsType::False => {
                extra.warnings.on_fallback_py(self.get_name(), value, extra)?;
                infer_to_python(value, include, exclude, extra)
            }
        }
    }

    fn json_key<'a>(&self, key: &'a Bound<'_, PyAny>, extra: &Extra) -> PyResult<Cow<'a, str>> {
        match extra.ob_type_lookup.is_type(key, ObType::Float) {
            IsType::Exact | IsType::Subclass => to_str_json_key(key),
            IsType::False => {
                extra.warnings.on_fallback_py(self.get_name(), key, extra)?;
                infer_json_key(key, extra)
            }
        }
    }

    fn serde_serialize<S: Serializer>(
        &self,
        value: &Bound<'_, PyAny>,
        serializer: S,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        // TODO: Merge extra.config into self.inf_nan_mode?
        extra: &Extra,
    ) -> Result<S::Ok, S::Error> {
        match value.extract::<f64>() {
            Ok(v) => serialize_f64(v, serializer, self.inf_nan_mode),
            Err(_) => {
                extra.warnings.on_fallback_ser::<S>(self.get_name(), value, extra)?;
                infer_serialize(value, serializer, include, exclude, extra)
            }
        }
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}
