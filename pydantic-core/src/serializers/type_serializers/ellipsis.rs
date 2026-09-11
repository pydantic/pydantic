// This serializer is defined so that building a schema serializer containing an
// 'ellipsis' core schema doesn't crash. In practice, the serializer can be used
// if the 'ellipsis' core schema is used standalone (e.g. with a Pydantic type
// adapter), but this isn't something we explicitly support.

use std::borrow::Cow;
use std::sync::{Arc, LazyLock};

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyEllipsis};

use serde::ser::Error;

use crate::PydanticSerializationUnexpectedValue;
use crate::definitions::DefinitionsBuilder;
use crate::serializers::SerializationState;

use super::{BuildSerializer, CombinedSerializer, TypeSerializer};

#[derive(Debug)]
pub struct EllipsisSerializer {}

static ELLIPSIS_SERIALIZER: LazyLock<Arc<CombinedSerializer>> =
    LazyLock::new(|| Arc::new(EllipsisSerializer {}.into()));

impl BuildSerializer for EllipsisSerializer {
    const EXPECTED_TYPE: &'static str = "ellipsis";

    fn build(
        _schema: &Bound<'_, PyDict>,
        _config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        Ok(ELLIPSIS_SERIALIZER.clone())
    }
}

impl_py_gc_traverse!(EllipsisSerializer {});

impl TypeSerializer for EllipsisSerializer {
    fn to_python(&self, value: &Bound<'_, PyAny>, _state: &mut SerializationState<'_>) -> PyResult<Py<PyAny>> {
        let ellipsis = PyEllipsis::get(value.py());

        if value.is(ellipsis) {
            Ok(ellipsis.to_owned().into_any().unbind())
        } else {
            Err(
                PydanticSerializationUnexpectedValue::new_from_msg(Some("Expected 'Ellipsis' object".to_string()))
                    .to_py_err(),
            )
        }
    }

    fn json_key<'a, 'py>(
        &self,
        key: &'a Bound<'py, PyAny>,
        state: &mut SerializationState<'py>,
    ) -> PyResult<Cow<'a, str>> {
        self.invalid_as_json_key(key, state, Self::EXPECTED_TYPE)
    }

    fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        _value: &Bound<'_, PyAny>,
        _serializer: S,
        _state: &mut SerializationState<'_>,
    ) -> Result<S::Ok, S::Error> {
        Err(Error::custom("'Ellipsis' can't be serialized to JSON".to_string()))
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}
