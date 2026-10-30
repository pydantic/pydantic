use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::borrow::Cow;
use std::sync::Arc;

use crate::definitions::DefinitionsBuilder;
use crate::input::EitherTimedelta;
use crate::serializers::SerializationState;
use crate::serializers::config::TemporalMode;

use super::{
    BuildSerializer, CombinedSerializer, SerMode, TypeSerializer, infer_json_key, infer_serialize, infer_to_python,
};

#[derive(Debug)]
pub struct TimeDeltaSerializer {
    temporal_mode: TemporalMode,
}

impl BuildSerializer for TimeDeltaSerializer {
    const EXPECTED_TYPE: &'static str = "timedelta";

    fn build(
        _schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        let temporal_mode = TemporalMode::timedelta_from_config(config)?;

        Ok(Arc::new(Self { temporal_mode }.into()))
    }
}

impl_py_gc_traverse!(TimeDeltaSerializer {});

impl TypeSerializer for TimeDeltaSerializer {
    fn to_python<'py>(&self, value: &Bound<'py, PyAny>, state: &mut SerializationState<'py>) -> PyResult<Py<PyAny>> {
        match EitherTimedelta::try_from(value) {
            Ok(either_timedelta) => match state.extra.mode {
                SerMode::Json => Ok(self.temporal_mode.timedelta_to_json(value.py(), either_timedelta)?),
                _ => Ok(value.clone().unbind()),
            },
            _ => {
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
        match EitherTimedelta::try_from(key) {
            Ok(either_timedelta) => self.temporal_mode.timedelta_json_key(&either_timedelta),
            Err(_) => {
                state.warn_fallback_py(self.get_name(), key)?;
                infer_json_key(key, state)
            }
        }
    }

    fn serde_serialize<'py, S: serde::ser::Serializer>(
        &self,
        value: &Bound<'py, PyAny>,
        serializer: S,
        state: &mut SerializationState<'py>,
    ) -> Result<S::Ok, S::Error> {
        match EitherTimedelta::try_from(value) {
            Ok(either_timedelta) => self.temporal_mode.timedelta_serialize(either_timedelta, serializer),
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
