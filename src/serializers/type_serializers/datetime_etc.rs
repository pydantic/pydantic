use std::borrow::Cow;

use pyo3::prelude::*;
use pyo3::types::{PyDate, PyDateTime, PyDict, PyTime};

use crate::definitions::DefinitionsBuilder;
use crate::input::{pydate_as_date, pydatetime_as_datetime, pytime_as_time};
use crate::PydanticSerializationUnexpectedValue;

use super::{
    infer_json_key, infer_serialize, infer_to_python, py_err_se_err, BuildSerializer, CombinedSerializer, Extra,
    SerMode, TypeSerializer,
};

pub(crate) fn datetime_to_string(py_dt: &PyDateTime) -> PyResult<String> {
    pydatetime_as_datetime(py_dt).map(|dt| dt.to_string())
}

pub(crate) fn date_to_string(py_date: &PyDate) -> PyResult<String> {
    pydate_as_date(py_date).map(|dt| dt.to_string())
}

pub(crate) fn time_to_string(py_time: &PyTime) -> PyResult<String> {
    pytime_as_time(py_time, None).map(|dt| dt.to_string())
}

fn downcast_date_reject_datetime(py_date: &PyAny) -> PyResult<&PyDate> {
    if let Ok(py_date) = py_date.downcast::<PyDate>() {
        // because `datetime` is a subclass of `date` we have to check that the value is not a
        // `datetime` to avoid lossy serialization
        if !py_date.is_instance_of::<PyDateTime>() {
            return Ok(py_date);
        }
    }

    Err(PydanticSerializationUnexpectedValue::new_err(None))
}

macro_rules! build_serializer {
    ($struct_name:ident, $expected_type:literal, $downcast:path, $convert_func:ident $(, $json_check_func:ident)?) => {
        #[derive(Debug, Clone)]
        pub struct $struct_name;

        impl BuildSerializer for $struct_name {
            const EXPECTED_TYPE: &'static str = $expected_type;

            fn build(
                _schema: &PyDict,
                _config: Option<&PyDict>,
                _definitions: &mut DefinitionsBuilder<CombinedSerializer>,
            ) -> PyResult<CombinedSerializer> {
                Ok(Self {}.into())
            }
        }

        impl_py_gc_traverse!($struct_name {});

        impl TypeSerializer for $struct_name {
            fn to_python(
                &self,
                value: &PyAny,
                include: Option<&PyAny>,
                exclude: Option<&PyAny>,
                extra: &Extra,
            ) -> PyResult<PyObject> {
                let py = value.py();
                match $downcast(value) {
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
                match $downcast(key) {
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
                match $downcast(value) {
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

build_serializer!(
    DatetimeSerializer,
    "datetime",
    PyAny::downcast::<PyDateTime>,
    datetime_to_string
);
build_serializer!(DateSerializer, "date", downcast_date_reject_datetime, date_to_string);
build_serializer!(TimeSerializer, "time", PyAny::downcast::<PyTime>, time_to_string);
