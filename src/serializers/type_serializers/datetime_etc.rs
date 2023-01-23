use std::borrow::Cow;

use pyo3::prelude::*;
use pyo3::types::{PyDate, PyDateTime, PyDict, PyTime};

use crate::build_context::BuildContext;
use crate::input::{pydate_as_date, pydatetime_as_datetime, pytime_as_time};

use super::{
    infer_json_key, infer_serialize, infer_to_python, py_err_se_err, BuildSerializer, CombinedSerializer, Extra,
    SerMode, TypeSerializer,
};

pub(crate) fn datetime_to_string(py_dt: &PyDateTime) -> PyResult<String> {
    let dt = pydatetime_as_datetime(py_dt)?;
    Ok(dt.to_string())
}

pub(crate) fn date_to_string(py_date: &PyDate) -> PyResult<String> {
    let date = pydate_as_date!(py_date);
    Ok(date.to_string())
}

pub(crate) fn time_to_string(py_time: &PyTime) -> PyResult<String> {
    let time = pytime_as_time!(py_time);
    Ok(time.to_string())
}

macro_rules! build_serializer {
    ($struct_name:ident, $expected_type:literal, $cast_as:ty, $convert_func:ident) => {
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
                match value.downcast::<$cast_as>() {
                    Ok(py_value) => match extra.mode {
                        SerMode::Json => {
                            let s = $convert_func(py_value)?;
                            Ok(s.into_py(py))
                        }
                        _ => Ok(value.into_py(py)),
                    },
                    Err(_) => {
                        extra.warnings.on_fallback_py(self.get_name(), value, extra)?;
                        infer_to_python(value, include, exclude, extra)
                    }
                }
            }

            fn json_key<'py>(&self, key: &'py PyAny, extra: &Extra) -> PyResult<Cow<'py, str>> {
                match key.downcast::<$cast_as>() {
                    Ok(py_value) => Ok(Cow::Owned($convert_func(py_value)?)),
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
                match value.downcast::<$cast_as>() {
                    Ok(py_value) => {
                        let s = $convert_func(py_value).map_err(py_err_se_err)?;
                        serializer.serialize_str(&s)
                    }
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

build_serializer!(DatetimeSerializer, "datetime", PyDateTime, datetime_to_string);
build_serializer!(DateSerializer, "date", PyDate, date_to_string);
build_serializer!(TimeSerializer, "time", PyTime, time_to_string);
