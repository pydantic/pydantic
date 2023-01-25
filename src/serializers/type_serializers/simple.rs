use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::borrow::Cow;

use serde::Serialize;

use crate::build_context::BuildContext;

use super::{
    infer_json_key, infer_serialize, infer_to_python, BuildSerializer, CombinedSerializer, Extra, IsType, ObType,
    SerMode, TypeSerializer,
};

#[derive(Debug, Clone)]
pub struct NoneSerializer;

impl BuildSerializer for NoneSerializer {
    const EXPECTED_TYPE: &'static str = "none";

    fn build(
        _schema: &PyDict,
        _config: Option<&PyDict>,
        _build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        Ok(Self {}.into())
    }
}

pub(crate) fn none_json_key() -> PyResult<Cow<'static, str>> {
    Ok(Cow::Borrowed("None"))
}

impl TypeSerializer for NoneSerializer {
    fn to_python(
        &self,
        value: &PyAny,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        let py = value.py();
        match extra.ob_type_lookup.is_type(value, ObType::None) {
            IsType::Exact => Ok(py.None().into_py(py)),
            // I don't think subclasses of None can exist
            _ => {
                extra.warnings.on_fallback_py(self.get_name(), value, extra)?;
                infer_to_python(value, include, exclude, extra)
            }
        }
    }

    fn json_key<'py>(&self, key: &'py PyAny, extra: &Extra) -> PyResult<Cow<'py, str>> {
        match extra.ob_type_lookup.is_type(key, ObType::None) {
            IsType::Exact => none_json_key(),
            _ => {
                extra.warnings.on_fallback_py(self.get_name(), key, extra)?;
                infer_json_key(key, extra)
            }
        }
    }

    fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        value: &PyAny,
        serializer: S,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> Result<S::Ok, S::Error> {
        match extra.ob_type_lookup.is_type(value, ObType::None) {
            IsType::Exact => serializer.serialize_none(),
            _ => {
                extra.warnings.on_fallback_ser::<S>(self.get_name(), value, extra)?;
                infer_serialize(value, serializer, include, exclude, extra)
            }
        }
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}

macro_rules! build_simple_serializer {
    ($struct_name:ident, $expected_type:literal, $rust_type:ty, $ob_type:expr, $key_method:ident) => {
        #[derive(Debug, Clone)]
        pub struct $struct_name;

        impl BuildSerializer for $struct_name {
            const EXPECTED_TYPE: &'static str = $expected_type;

            fn build(
                _schema: &PyDict,
                _config: Option<&PyDict>,
                _build_context: &mut BuildContext<CombinedSerializer>,
            ) -> PyResult<CombinedSerializer> {
                Ok(Self {}.into())
            }
        }

        impl TypeSerializer for $struct_name {
            fn to_python(
                &self,
                value: &PyAny,
                include: Option<&PyAny>,
                exclude: Option<&PyAny>,
                extra: &Extra,
            ) -> PyResult<PyObject> {
                let py = value.py();
                match extra.ob_type_lookup.is_type(value, $ob_type) {
                    IsType::Exact => Ok(value.into_py(py)),
                    IsType::Subclass => match extra.mode {
                        SerMode::Json => {
                            let rust_value = value.extract::<$rust_type>()?;
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

            fn json_key<'py>(&self, key: &'py PyAny, extra: &Extra) -> PyResult<Cow<'py, str>> {
                match extra.ob_type_lookup.is_type(key, $ob_type) {
                    IsType::Exact | IsType::Subclass => $key_method(key),
                    IsType::False => {
                        extra.warnings.on_fallback_py(self.get_name(), key, extra)?;
                        infer_json_key(key, extra)
                    }
                }
            }

            fn serde_serialize<S: serde::ser::Serializer>(
                &self,
                value: &PyAny,
                serializer: S,
                include: Option<&PyAny>,
                exclude: Option<&PyAny>,
                extra: &Extra,
            ) -> Result<S::Ok, S::Error> {
                match value.extract::<$rust_type>() {
                    Ok(v) => v.serialize(serializer),
                    Err(_) => {
                        extra
                            .warnings
                            .on_fallback_ser::<S>(self.get_name(), value, extra)?;
                        infer_serialize(value, serializer, include, exclude, extra)
                    }
                }
            }

            fn get_name(&self) -> &str {
                Self::EXPECTED_TYPE
            }
        }
    };
}

pub(crate) fn to_str_json_key(key: &PyAny) -> PyResult<Cow<str>> {
    Ok(key.str()?.to_string_lossy())
}

build_simple_serializer!(IntSerializer, "int", i64, ObType::Int, to_str_json_key);

pub(crate) fn bool_json_key(key: &PyAny) -> PyResult<Cow<str>> {
    let v = if key.is_true().unwrap_or(false) {
        "true"
    } else {
        "false"
    };
    Ok(Cow::Borrowed(v))
}

build_simple_serializer!(BoolSerializer, "bool", bool, ObType::Bool, bool_json_key);
build_simple_serializer!(FloatSerializer, "float", f64, ObType::Float, to_str_json_key);
