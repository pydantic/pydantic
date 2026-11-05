use pyo3::types::PyDict;
use pyo3::{IntoPyObjectExt, intern, prelude::*};

use std::borrow::Cow;
use std::sync::{Arc, LazyLock};

use serde::Serializer;

use crate::definitions::DefinitionsBuilder;
use crate::serializers::SerializationState;
use crate::serializers::config::InfNanMode;
use crate::tools::SchemaDict;

use super::simple::to_str_json_key;
use super::{
    BuildSerializer, CombinedSerializer, IsType, ObType, SerCheck, SerMode, TypeSerializer, infer_json_key,
    infer_serialize, infer_to_python,
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

/// The JSON-compatible Python replacement for an `inf`/`nan` float, according to `inf_nan_mode`.
///
/// Returns `None` if no replacement is needed (finite value, or the `'constants'` mode, where
/// Python floats are the closest equivalent to the `Infinity`/`NaN` JSON constants).
pub(crate) fn inf_nan_to_python(py: Python<'_>, v: f64, inf_nan_mode: InfNanMode) -> Option<Py<PyAny>> {
    if v.is_finite() {
        return None;
    }
    match inf_nan_mode {
        InfNanMode::Null => Some(py.None()),
        InfNanMode::Constants => None,
        InfNanMode::Strings => {
            let s = if v.is_nan() {
                intern!(py, "NaN")
            } else if v.is_sign_positive() {
                intern!(py, "Infinity")
            } else {
                intern!(py, "-Infinity")
            };
            Some(s.clone().into_any().unbind())
        }
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
    fn to_python<'py>(&self, value: &Bound<'py, PyAny>, state: &mut SerializationState<'py>) -> PyResult<Py<PyAny>> {
        let py = value.py();
        match state.extra.ob_type_lookup.is_type(value, ObType::Float) {
            IsType::Exact => match state.extra.mode {
                SerMode::Json => match inf_nan_to_python(py, value.extract::<f64>()?, self.inf_nan_mode) {
                    Some(v) => Ok(v),
                    None => Ok(value.clone().unbind()),
                },
                _ => Ok(value.clone().unbind()),
            },
            IsType::Subclass => match state.check {
                SerCheck::Strict => Err(PydanticSerializationUnexpectedValue::new_from_msg(None).to_py_err()),
                SerCheck::Lax | SerCheck::None => match state.extra.mode {
                    SerMode::Json => {
                        let v = value.extract::<f64>()?;
                        match inf_nan_to_python(py, v, self.inf_nan_mode) {
                            Some(v) => Ok(v),
                            None => v.into_py_any(py),
                        }
                    }
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
        state: &mut SerializationState<'py>,
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
        state: &mut SerializationState<'py>,
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
