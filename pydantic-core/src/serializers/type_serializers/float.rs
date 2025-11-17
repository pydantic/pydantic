use pyo3::types::PyDict;
use pyo3::{intern, prelude::*, IntoPyObjectExt};

use std::borrow::Cow;
use std::sync::Arc;

use serde::Serializer;

use crate::build_tools::LazyLock;
use crate::definitions::DefinitionsBuilder;
use crate::serializers::config::InfNanMode;
use crate::serializers::SerializationState;
use crate::tools::SchemaDict;

use super::simple::to_str_json_key;
use super::{
    infer_json_key, infer_serialize, infer_to_python, BuildSerializer, CombinedSerializer, IsType, ObType, SerCheck,
    SerMode, TypeSerializer,
};
use crate::serializers::errors::PydanticSerializationUnexpectedValue;

#[derive(Debug)]
pub struct FloatSerializer {
    inf_nan_mode: InfNanMode,
}

static FLOAT_SERIALIZER_NULL: LazyLock<Arc<CombinedSerializer>> = LazyLock::new(|| {
    Arc::new(CombinedSerializer::Float(FloatSerializer {
        inf_nan_mode: InfNanMode::Null,
    }))
});

static FLOAT_SERIALIZER_CONSTANTS: LazyLock<Arc<CombinedSerializer>> = LazyLock::new(|| {
    Arc::new(CombinedSerializer::Float(FloatSerializer {
        inf_nan_mode: InfNanMode::Constants,
    }))
});

static FLOAT_SERIALIZER_STRINGS: LazyLock<Arc<CombinedSerializer>> = LazyLock::new(|| {
    Arc::new(CombinedSerializer::Float(FloatSerializer {
        inf_nan_mode: InfNanMode::Strings,
    }))
});

impl FloatSerializer {
    pub fn get(py: Python, config: Option<&Bound<'_, PyDict>>) -> PyResult<&'static Arc<CombinedSerializer>> {
        let inf_nan_mode = config
            .and_then(|c| c.get_as(intern!(py, "ser_json_inf_nan")).transpose())
            .transpose()?
            .unwrap_or_default();

        match inf_nan_mode {
            InfNanMode::Null => Ok(&FLOAT_SERIALIZER_NULL),
            InfNanMode::Constants => Ok(&FLOAT_SERIALIZER_CONSTANTS),
            InfNanMode::Strings => Ok(&FLOAT_SERIALIZER_STRINGS),
        }
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
        _definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        Self::get(schema.py(), config).cloned()
    }
}

impl_py_gc_traverse!(FloatSerializer {});

impl TypeSerializer for FloatSerializer {
    fn to_python<'py>(
        &self,
        value: &Bound<'py, PyAny>,
        state: &mut SerializationState<'_, 'py>,
    ) -> PyResult<Py<PyAny>> {
        let py = value.py();
        match state.extra.ob_type_lookup.is_type(value, ObType::Float) {
            IsType::Exact => Ok(value.clone().unbind()),
            IsType::Subclass => match state.check {
                SerCheck::Strict => Err(PydanticSerializationUnexpectedValue::new_from_msg(None).to_py_err()),
                SerCheck::Lax | SerCheck::None => match state.extra.mode {
                    SerMode::Json => value.extract::<f64>()?.into_py_any(py),
                    _ => infer_to_python(value, state),
                },
            },
            IsType::False => {
                state.warn_fallback_py(self.get_name(), value)?;
                infer_to_python(value, state)
            }
        }
    }

    fn json_key<'a, 'py>(
        &self,
        key: &'a Bound<'py, PyAny>,
        state: &mut SerializationState<'_, 'py>,
    ) -> PyResult<Cow<'a, str>> {
        match state.extra.ob_type_lookup.is_type(key, ObType::Float) {
            IsType::Exact | IsType::Subclass => to_str_json_key(key),
            IsType::False => {
                state.warn_fallback_py(self.get_name(), key)?;
                infer_json_key(key, state)
            }
        }
    }

    fn serde_serialize<'py, S: Serializer>(
        &self,
        value: &Bound<'py, PyAny>,
        serializer: S,
        state: &mut SerializationState<'_, 'py>,
    ) -> Result<S::Ok, S::Error> {
        match value.extract::<f64>() {
            Ok(v) => serialize_f64(v, serializer, self.inf_nan_mode),
            Err(_) => {
                state.warn_fallback_ser::<S>(self.get_name(), value)?;
                infer_serialize(value, serializer, state)
            }
        }
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}
