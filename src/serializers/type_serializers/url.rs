use std::borrow::Cow;

use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::definitions::DefinitionsBuilder;

use crate::url::{PyMultiHostUrl, PyUrl};

use super::{
    infer_json_key, infer_serialize, infer_to_python, BuildSerializer, CombinedSerializer, Extra, SerMode,
    TypeSerializer,
};

macro_rules! build_serializer {
    ($struct_name:ident, $expected_type:literal, $extract:ty) => {
        #[derive(Debug, Clone)]
        pub struct $struct_name;

        impl BuildSerializer for $struct_name {
            const EXPECTED_TYPE: &'static str = $expected_type;

            fn build(
                _schema: &Bound<'_, PyDict>,
                _config: Option<&Bound<'_, PyDict>>,
                _definitions: &mut DefinitionsBuilder<CombinedSerializer>,
            ) -> PyResult<CombinedSerializer> {
                Ok(Self {}.into())
            }
        }

        impl_py_gc_traverse!($struct_name {});

        impl TypeSerializer for $struct_name {
            fn to_python(
                &self,
                value: &Bound<'_, PyAny>,
                include: Option<&Bound<'_, PyAny>>,
                exclude: Option<&Bound<'_, PyAny>>,
                extra: &Extra,
            ) -> PyResult<PyObject> {
                let py = value.py();
                match value.extract::<$extract>() {
                    Ok(py_url) => match extra.mode {
                        SerMode::Json => Ok(py_url.__str__().into_py(py)),
                        _ => Ok(value.into_py(py)),
                    },
                    Err(_) => {
                        extra.warnings.on_fallback_py(self.get_name(), value, extra)?;
                        infer_to_python(value, include, exclude, extra)
                    }
                }
            }

            fn json_key<'a>(&self, key: &'a Bound<'_, PyAny>, extra: &Extra) -> PyResult<Cow<'a, str>> {
                match key.extract::<$extract>() {
                    Ok(py_url) => Ok(Cow::Owned(py_url.__str__().to_string())),
                    Err(_) => {
                        extra.warnings.on_fallback_py(self.get_name(), key, extra)?;
                        infer_json_key(key, extra)
                    }
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
                match value.extract::<$extract>() {
                    Ok(py_url) => serializer.serialize_str(&py_url.__str__()),
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
build_serializer!(UrlSerializer, "url", PyUrl);
build_serializer!(MultiHostUrlSerializer, "multi-host-url", PyMultiHostUrl);
