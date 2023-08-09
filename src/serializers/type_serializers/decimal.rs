use std::borrow::Cow;

use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::definitions::DefinitionsBuilder;
use crate::serializers::infer::{infer_json_key_known, infer_serialize_known, infer_to_python_known};
use crate::serializers::ob_type::{IsType, ObType};

use super::{
    infer_json_key, infer_serialize, infer_to_python, BuildSerializer, CombinedSerializer, Extra, TypeSerializer,
};

#[derive(Debug, Clone)]
pub struct DecimalSerializer {}

impl BuildSerializer for DecimalSerializer {
    const EXPECTED_TYPE: &'static str = "decimal";

    fn build(
        _schema: &PyDict,
        _config: Option<&PyDict>,
        _definitions: &mut DefinitionsBuilder<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        Ok(Self {}.into())
    }
}

impl_py_gc_traverse!(DecimalSerializer {});

impl TypeSerializer for DecimalSerializer {
    fn to_python(
        &self,
        value: &PyAny,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        let _py = value.py();
        match extra.ob_type_lookup.is_type(value, ObType::Decimal) {
            IsType::Exact | IsType::Subclass => infer_to_python_known(&ObType::Decimal, value, include, exclude, extra),
            IsType::False => {
                extra.warnings.on_fallback_py(self.get_name(), value, extra)?;
                infer_to_python(value, include, exclude, extra)
            }
        }
    }

    fn json_key<'py>(&self, key: &'py PyAny, extra: &Extra) -> PyResult<Cow<'py, str>> {
        match extra.ob_type_lookup.is_type(key, ObType::Decimal) {
            IsType::Exact | IsType::Subclass => infer_json_key_known(&ObType::Decimal, key, extra),
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
        match extra.ob_type_lookup.is_type(value, ObType::Decimal) {
            IsType::Exact | IsType::Subclass => {
                infer_serialize_known(&ObType::Decimal, value, serializer, include, exclude, extra)
            }
            IsType::False => {
                extra.warnings.on_fallback_ser::<S>(self.get_name(), value, extra)?;
                infer_serialize(value, serializer, include, exclude, extra)
            }
        }
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}
