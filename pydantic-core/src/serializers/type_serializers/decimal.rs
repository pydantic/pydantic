use std::borrow::Cow;
use std::sync::Arc;

use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::LazyLock;
use crate::definitions::DefinitionsBuilder;
use crate::serializers::SerializationState;
use crate::serializers::infer::{infer_json_key_known, infer_serialize_known, infer_to_python_known};
use crate::serializers::ob_type::{IsType, ObType};

use super::{BuildSerializer, CombinedSerializer, TypeSerializer, infer_json_key, infer_serialize, infer_to_python};

#[derive(Debug)]
pub struct DecimalSerializer {}

static DECIMAL_SERIALIZER: LazyLock<Arc<CombinedSerializer>> = LazyLock::new(|| Arc::new(DecimalSerializer {}.into()));

impl BuildSerializer for DecimalSerializer {
    const EXPECTED_TYPE: &'static str = "decimal";

    fn build(
        _schema: &Bound<'_, PyDict>,
        _config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        Ok(DECIMAL_SERIALIZER.clone())
    }
}

impl_py_gc_traverse!(DecimalSerializer {});

impl TypeSerializer for DecimalSerializer {
    fn to_python<'py>(
        &self,
        value: &Bound<'py, PyAny>,
        state: &mut SerializationState<'_, 'py>,
    ) -> PyResult<Py<PyAny>> {
        let _py = value.py();
        match state.extra.ob_type_lookup.is_type(value, ObType::Decimal) {
            IsType::Exact | IsType::Subclass => infer_to_python_known(ObType::Decimal, value, state),
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
        match state.extra.ob_type_lookup.is_type(key, ObType::Decimal) {
            IsType::Exact | IsType::Subclass => infer_json_key_known(ObType::Decimal, key, state),
            IsType::False => {
                state.warn_fallback_py(self.get_name(), key)?;
                infer_json_key(key, state)
            }
        }
    }

    fn serde_serialize<'py, S: serde::ser::Serializer>(
        &self,
        value: &Bound<'py, PyAny>,
        serializer: S,
        state: &mut SerializationState<'_, 'py>,
    ) -> Result<S::Ok, S::Error> {
        match state.extra.ob_type_lookup.is_type(value, ObType::Decimal) {
            IsType::Exact | IsType::Subclass => infer_serialize_known(ObType::Decimal, value, serializer, state),
            IsType::False => {
                state.warn_fallback_ser::<S>(self.get_name(), value)?;
                infer_serialize(value, serializer, state)
            }
        }
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}
