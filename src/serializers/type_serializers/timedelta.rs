use std::borrow::Cow;

use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::definitions::DefinitionsBuilder;
use crate::input::EitherTimedelta;
use crate::serializers::config::{FromConfig, TimedeltaMode};

use super::{
    infer_json_key, infer_serialize, infer_to_python, BuildSerializer, CombinedSerializer, Extra, SerMode,
    TypeSerializer,
};

#[derive(Debug, Clone)]
pub struct TimeDeltaSerializer {
    timedelta_mode: TimedeltaMode,
}

impl BuildSerializer for TimeDeltaSerializer {
    const EXPECTED_TYPE: &'static str = "timedelta";

    fn build(
        _schema: &PyDict,
        config: Option<&PyDict>,
        _definitions: &mut DefinitionsBuilder<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let timedelta_mode = TimedeltaMode::from_config(config)?;
        Ok(Self { timedelta_mode }.into())
    }
}

impl_py_gc_traverse!(TimeDeltaSerializer {});

impl TypeSerializer for TimeDeltaSerializer {
    fn to_python(
        &self,
        value: &PyAny,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        match extra.mode {
            SerMode::Json => match EitherTimedelta::try_from(value) {
                Ok(either_timedelta) => self.timedelta_mode.either_delta_to_json(value.py(), &either_timedelta),
                Err(_) => {
                    extra.warnings.on_fallback_py(self.get_name(), value, extra)?;
                    infer_to_python(value, include, exclude, extra)
                }
            },
            _ => infer_to_python(value, include, exclude, extra),
        }
    }

    fn json_key<'py>(&self, key: &'py PyAny, extra: &Extra) -> PyResult<Cow<'py, str>> {
        match EitherTimedelta::try_from(key) {
            Ok(either_timedelta) => self.timedelta_mode.json_key(key.py(), &either_timedelta),
            Err(_) => {
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
        match EitherTimedelta::try_from(value) {
            Ok(either_timedelta) => self
                .timedelta_mode
                .timedelta_serialize(value.py(), &either_timedelta, serializer),
            Err(_) => {
                extra.warnings.on_fallback_ser::<S>(self.get_name(), value, extra)?;
                infer_serialize(value, serializer, include, exclude, extra)
            }
        }
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}
