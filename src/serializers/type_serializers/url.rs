use std::borrow::Cow;
use std::sync::Arc;

use pyo3::prelude::*;
use pyo3::types::PyDict;
use pyo3::IntoPyObjectExt;

use crate::build_tools::LazyLock;
use crate::definitions::DefinitionsBuilder;
use crate::serializers::SerializationState;
use crate::url::{PyMultiHostUrl, PyUrl};

use super::{
    infer_json_key, infer_serialize, infer_to_python, BuildSerializer, CombinedSerializer, Extra, SerMode,
    TypeSerializer,
};

macro_rules! build_serializer {
    ($struct_name:ident, $expected_type:literal, $extract:ty) => {
        #[derive(Debug)]
        pub struct $struct_name;

        impl BuildSerializer for $struct_name {
            const EXPECTED_TYPE: &'static str = $expected_type;

            fn build(
                _schema: &Bound<'_, PyDict>,
                _config: Option<&Bound<'_, PyDict>>,
                _definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
            ) -> PyResult<Arc<CombinedSerializer>> {
                static SERIALIZER: LazyLock<Arc<CombinedSerializer>> =
                    LazyLock::new(|| Arc::new(CombinedSerializer::from($struct_name {})));
                Ok(SERIALIZER.clone())
            }
        }

        impl_py_gc_traverse!($struct_name {});

        impl TypeSerializer for $struct_name {
            fn to_python<'py>(
                &self,
                value: &Bound<'py, PyAny>,
                include: Option<&Bound<'py, PyAny>>,
                exclude: Option<&Bound<'py, PyAny>>,
                state: &mut SerializationState<'py>,
                extra: &Extra<'_, 'py>,
            ) -> PyResult<Py<PyAny>> {
                let py = value.py();
                match value.extract::<$extract>() {
                    Ok(py_url) => match extra.mode {
                        SerMode::Json => py_url.__str__(value.py()).into_py_any(py),
                        _ => Ok(value.clone().unbind()),
                    },
                    Err(_) => {
                        state.warn_fallback_py(self.get_name(), value, extra)?;
                        infer_to_python(value, include, exclude, state, extra)
                    }
                }
            }

            fn json_key<'a, 'py>(
                &self,
                key: &'a Bound<'py, PyAny>,
                state: &mut SerializationState<'py>,
                extra: &Extra<'_, 'py>,
            ) -> PyResult<Cow<'a, str>> {
                match key.extract::<$extract>() {
                    Ok(py_url) => Ok(Cow::Owned(py_url.__str__(key.py()).to_string())),
                    Err(_) => {
                        state.warn_fallback_py(self.get_name(), key, extra)?;
                        infer_json_key(key, state, extra)
                    }
                }
            }

            fn serde_serialize<'py, S: serde::ser::Serializer>(
                &self,
                value: &Bound<'py, PyAny>,
                serializer: S,
                include: Option<&Bound<'py, PyAny>>,
                exclude: Option<&Bound<'py, PyAny>>,
                state: &mut SerializationState<'py>,
                extra: &Extra<'_, 'py>,
            ) -> Result<S::Ok, S::Error> {
                match value.extract::<$extract>() {
                    Ok(py_url) => serializer.serialize_str(&py_url.__str__(value.py())),
                    Err(_) => {
                        state.warn_fallback_ser::<S>(self.get_name(), value, extra)?;
                        infer_serialize(value, serializer, include, exclude, state, extra)
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
