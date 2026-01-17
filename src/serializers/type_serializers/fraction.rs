use std::borrow::Cow;
use std::sync::Arc;

use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::LazyLock;
use crate::definitions::DefinitionsBuilder;
use crate::serializers::infer::{infer_json_key_known, infer_serialize_known, infer_to_python_known};
use crate::serializers::ob_type::{IsType, ObType};

use crate::serializers::SerializationState;

use super::{
    infer_json_key, infer_serialize, infer_to_python, BuildSerializer, CombinedSerializer, TypeSerializer,
};

#[derive(Debug)]
pub struct FractionSerializer {}

static FRACTION_SERIALIZER: LazyLock<Arc<CombinedSerializer>> =
    LazyLock::new(|| Arc::new(FractionSerializer {}.into()));

impl BuildSerializer for FractionSerializer {
    const EXPECTED_TYPE: &'static str = "fraction";

    fn build(
        _schema: &Bound<'_, PyDict>,
        _config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        Ok(FRACTION_SERIALIZER.clone())
    }
}

impl_py_gc_traverse!(FractionSerializer {});

impl TypeSerializer for FractionSerializer {
    fn to_python<'py>(
        &self,
        value: &Bound<'py, PyAny>,
        state: &mut SerializationState<'_, 'py>,
    ) -> PyResult<Py<PyAny>> {
        let _py = value.py();
        match state.extra.ob_type_lookup.is_type(value, ObType::Fraction) {
            IsType::Exact | IsType::Subclass => infer_to_python_known(ObType::Fraction, value, state),
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
        match state.extra.ob_type_lookup.is_type(key, ObType::Fraction) {
            IsType::Exact | IsType::Subclass => infer_json_key_known(ObType::Fraction, key, state),
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
            IsType::Exact | IsType::Subclass => infer_serialize_known(ObType::Fraction, value, serializer, state),
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
