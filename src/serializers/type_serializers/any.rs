use std::borrow::Cow;
use std::str::from_utf8;

use pyo3::prelude::*;
use pyo3::types::{
    PyByteArray, PyBytes, PyDate, PyDateTime, PyDelta, PyDict, PyFrozenSet, PyList, PySet, PyString, PyTime, PyTuple,
};

use serde::ser::{Serialize, SerializeMap, SerializeSeq, Serializer};

use crate::build_context::BuildContext;
use crate::build_tools::safe_repr;
use crate::errors::PydanticSerializationError;
use crate::url::{PyMultiHostUrl, PyUrl};

use super::new_class::object_to_dict;
use super::{
    py_err_se_err, utf8_py_error, AnyFilter, BuildSerializer, CombinedSerializer, Extra, ObType, SerMode,
    TypeSerializer,
};

#[derive(Debug, Clone)]
pub struct AnySerializer;

impl BuildSerializer for AnySerializer {
    const EXPECTED_TYPE: &'static str = "any";

    fn build(
        _schema: &PyDict,
        _config: Option<&PyDict>,
        _build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        Ok(Self {}.into())
    }
}

impl TypeSerializer for AnySerializer {
    fn serde_serialize<S: Serializer>(
        &self,
        value: &PyAny,
        serializer: S,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> Result<S::Ok, S::Error> {
        SerializeInfer::new(value, include, exclude, extra).serialize(serializer)
    }
}

pub(crate) fn fallback_to_python(
    value: &PyAny,
    include: Option<&PyAny>,
    exclude: Option<&PyAny>,
    extra: &Extra,
) -> PyResult<PyObject> {
    fallback_to_python_known(&extra.ob_type_lookup.get_type(value), value, include, exclude, extra)
}

pub(crate) fn fallback_to_python_known(
    ob_type: &ObType,
    value: &PyAny,
    include: Option<&PyAny>,
    exclude: Option<&PyAny>,
    extra: &Extra,
) -> PyResult<PyObject> {
    let py = value.py();
    let value_id = match extra.rec_guard.add(value) {
        Ok(id) => id,
        Err(e) => {
            return match extra.mode {
                SerMode::Json => Err(e),
                // if recursion is detected by we're serializing to python, we just return the value
                _ => Ok(value.into_py(py)),
            };
        }
    };

    // have to do this to make sure subclasses of for example str are upcast to `str`
    macro_rules! extract_as {
        ($t:ty) => {
            value.extract::<$t>()?.into_py(py)
        };
    }

    macro_rules! serialize_seq {
        ($t:ty) => {
            value
                .cast_as::<$t>()?
                .iter()
                .map(|v| fallback_to_python(v, include, exclude, extra))
                .collect::<PyResult<Vec<PyObject>>>()?
        };
    }

    macro_rules! serialize_seq_filter {
        ($t:ty) => {{
            let py_seq: &$t = value.cast_as()?;
            let mut items = Vec::with_capacity(py_seq.len());
            let filter = AnyFilter::new();

            for (index, element) in py_seq.iter().enumerate() {
                let op_next = filter.value_filter(index, include, exclude)?;
                if let Some((next_include, next_exclude)) = op_next {
                    items.push(fallback_to_python(element, next_include, next_exclude, extra)?);
                }
            }
            items
        }};
    }

    let serialize_dict = |dict: &PyDict| {
        let new_dict = PyDict::new(py);
        let filter = AnyFilter::new();

        for (k, v) in dict {
            let op_next = filter.key_filter(k, include, exclude)?;
            if let Some((next_include, next_exclude)) = op_next {
                let k_str = fallback_json_key(k, extra)?;
                let k = PyString::new(py, &k_str);
                let v = fallback_to_python(v, next_include, next_exclude, extra)?;
                new_dict.set_item(k, v)?;
            }
        }
        Ok::<PyObject, PyErr>(new_dict.into_py(py))
    };

    let value = match extra.mode {
        SerMode::Json => match ob_type {
            ObType::None => value.into_py(py),
            ObType::Bool => extract_as!(bool),
            ObType::Int => extract_as!(i64),
            // `bool` and `None` can't be subclasses, so no need to do the same on bool
            ObType::Float => extract_as!(f64),
            ObType::Str => extract_as!(&str),
            ObType::Bytes => extra
                .config
                .bytes_mode
                .bytes_to_string(value.cast_as()?)
                .map(|s| s.into_py(py))?,
            ObType::Bytearray => {
                let py_byte_array: &PyByteArray = value.cast_as()?;
                // see https://docs.rs/pyo3/latest/pyo3/types/struct.PyByteArray.html#method.as_bytes
                // for why this is marked unsafe
                let bytes = unsafe { py_byte_array.as_bytes() };
                match from_utf8(bytes) {
                    Ok(s) => s.into_py(py),
                    Err(err) => return Err(utf8_py_error(py, err, bytes)),
                }
            }
            ObType::Tuple => {
                let elements = serialize_seq_filter!(PyTuple);
                PyList::new(py, elements).into_py(py)
            }
            ObType::List => {
                let elements = serialize_seq_filter!(PyList);
                PyList::new(py, elements).into_py(py)
            }
            ObType::Set => {
                let elements = serialize_seq!(PySet);
                PyList::new(py, elements).into_py(py)
            }
            ObType::Frozenset => {
                let elements = serialize_seq!(PyFrozenSet);
                PyList::new(py, elements).into_py(py)
            }
            ObType::Dict => serialize_dict(value.cast_as()?)?,
            ObType::Datetime => {
                let py_dt: &PyDateTime = value.cast_as()?;
                let iso_dt = super::datetime_etc::datetime_to_string(py_dt)?;
                iso_dt.into_py(py)
            }
            ObType::Date => {
                let py_date: &PyDate = value.cast_as()?;
                let iso_date = super::datetime_etc::date_to_string(py_date)?;
                iso_date.into_py(py)
            }
            ObType::Time => {
                let py_time: &PyTime = value.cast_as()?;
                let iso_time = super::datetime_etc::time_to_string(py_time)?;
                iso_time.into_py(py)
            }
            ObType::Timedelta => {
                let py_timedelta: &PyDelta = value.cast_as()?;
                extra.config.timedelta_mode.timedelta_to_json(py_timedelta)?
            }
            ObType::Url => {
                let py_url: PyUrl = value.extract()?;
                py_url.__str__().into_py(py)
            }
            ObType::MultiHostUrl => {
                let py_url: PyMultiHostUrl = value.extract()?;
                py_url.__str__().into_py(py)
            }
            ObType::Dataclass => serialize_dict(object_to_dict(value, false, extra)?)?,
            ObType::PydanticModel => serialize_dict(object_to_dict(value, true, extra)?)?,
            ObType::Unknown => return Err(unknown_type_error(value)),
        },
        _ => match ob_type {
            ObType::Tuple => {
                let elements = serialize_seq_filter!(PyTuple);
                PyTuple::new(py, elements).into_py(py)
            }
            ObType::List => {
                let elements = serialize_seq_filter!(PyList);
                PyList::new(py, elements).into_py(py)
            }
            ObType::Set => {
                let elements = serialize_seq!(PySet);
                PySet::new(py, &elements)?.into_py(py)
            }
            ObType::Frozenset => {
                let elements = serialize_seq!(PyFrozenSet);
                PyFrozenSet::new(py, &elements)?.into_py(py)
            }
            ObType::Dict => {
                // different logic for keys from above
                let dict: &PyDict = value.cast_as()?;
                let new_dict = PyDict::new(py);
                let filter = AnyFilter::new();

                for (k, v) in dict {
                    let op_next = filter.key_filter(k, include, exclude)?;
                    if let Some((next_include, next_exclude)) = op_next {
                        let v = fallback_to_python(v, next_include, next_exclude, extra)?;
                        new_dict.set_item(k, v)?;
                    }
                }
                new_dict.into_py(py)
            }
            ObType::Dataclass => serialize_dict(object_to_dict(value, false, extra)?)?,
            ObType::PydanticModel => serialize_dict(object_to_dict(value, true, extra)?)?,
            _ => value.into_py(py),
        },
    };
    extra.rec_guard.pop(value_id);
    Ok(value)
}

pub(crate) struct SerializeInfer<'py> {
    value: &'py PyAny,
    extra: &'py Extra<'py>,
    include: Option<&'py PyAny>,
    exclude: Option<&'py PyAny>,
}

impl<'py> SerializeInfer<'py> {
    pub(crate) fn new(
        value: &'py PyAny,
        include: Option<&'py PyAny>,
        exclude: Option<&'py PyAny>,
        extra: &'py Extra,
    ) -> Self {
        Self {
            value,
            extra,
            include,
            exclude,
        }
    }
}

impl<'py> Serialize for SerializeInfer<'py> {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        let ob_type = self.extra.ob_type_lookup.get_type(self.value);
        fallback_serialize_known(&ob_type, self.value, serializer, self.include, self.exclude, self.extra)
    }
}

pub(crate) fn fallback_serialize<S: Serializer>(
    value: &PyAny,
    serializer: S,
    include: Option<&PyAny>,
    exclude: Option<&PyAny>,
    extra: &Extra,
) -> Result<S::Ok, S::Error> {
    fallback_serialize_known(
        &extra.ob_type_lookup.get_type(value),
        value,
        serializer,
        include,
        exclude,
        extra,
    )
}

pub(crate) fn fallback_serialize_known<S: Serializer>(
    ob_type: &ObType,
    value: &PyAny,
    serializer: S,
    include: Option<&PyAny>,
    exclude: Option<&PyAny>,
    extra: &Extra,
) -> Result<S::Ok, S::Error> {
    let value_id = extra.rec_guard.add(value).map_err(py_err_se_err)?;
    macro_rules! serialize {
        ($t:ty) => {
            match value.extract::<$t>() {
                Ok(v) => v.serialize(serializer),
                Err(e) => Err(py_err_se_err(e)),
            }
        };
    }

    macro_rules! serialize_seq {
        ($t:ty) => {{
            let py_seq: &$t = value.cast_as().map_err(py_err_se_err)?;
            let mut seq = serializer.serialize_seq(Some(py_seq.len()))?;
            for element in py_seq {
                let item_serializer = SerializeInfer::new(element, include, exclude, extra);
                seq.serialize_element(&item_serializer)?
            }
            seq.end()
        }};
    }

    macro_rules! serialize_seq_filter {
        ($t:ty) => {{
            let py_seq: &$t = value.cast_as().map_err(py_err_se_err)?;
            let mut seq = serializer.serialize_seq(Some(py_seq.len()))?;
            let filter = AnyFilter::new();
            for (index, element) in py_seq.iter().enumerate() {
                let op_next = filter.value_filter(index, include, exclude).map_err(py_err_se_err)?;
                if let Some((next_include, next_exclude)) = op_next {
                    let item_serializer = SerializeInfer::new(element, next_include, next_exclude, extra);
                    seq.serialize_element(&item_serializer)?
                }
            }
            seq.end()
        }};
    }

    macro_rules! serialize_dict {
        ($py_dict:expr) => {{
            let mut map = serializer.serialize_map(Some($py_dict.len()))?;
            let filter = AnyFilter::new();

            for (key, value) in $py_dict {
                let op_next = filter.key_filter(key, include, exclude).map_err(py_err_se_err)?;
                if let Some((next_include, next_exclude)) = op_next {
                    let key = fallback_json_key(key, extra).map_err(py_err_se_err)?;
                    let value_serializer = SerializeInfer::new(value, next_include, next_exclude, extra);
                    map.serialize_entry(&key, &value_serializer)?;
                }
            }
            map.end()
        }};
    }

    let ser_result = match ob_type {
        ObType::None => serializer.serialize_none(),
        ObType::Int => serialize!(i64),
        ObType::Bool => serialize!(bool),
        ObType::Float => serialize!(f64),
        ObType::Str => {
            let py_str: &PyString = value.cast_as().map_err(py_err_se_err)?;
            super::string::serialize_py_str(py_str, serializer)
        }
        ObType::Bytes => {
            let py_bytes: &PyBytes = value.cast_as().map_err(py_err_se_err)?;
            extra.config.bytes_mode.serialize_bytes(py_bytes, serializer)
        }
        ObType::Bytearray => {
            let py_byte_array: &PyByteArray = value.cast_as().map_err(py_err_se_err)?;
            let bytes = unsafe { py_byte_array.as_bytes() };
            match from_utf8(bytes) {
                Ok(s) => serializer.serialize_str(s),
                Err(e) => Err(py_err_se_err(e)),
            }
        }
        ObType::Dict => serialize_dict!(value.cast_as::<PyDict>().map_err(py_err_se_err)?),
        ObType::List => serialize_seq_filter!(PyList),
        ObType::Tuple => serialize_seq_filter!(PyTuple),
        ObType::Set => serialize_seq!(PySet),
        ObType::Frozenset => serialize_seq!(PyFrozenSet),
        ObType::Datetime => {
            let py_dt: &PyDateTime = value.cast_as().map_err(py_err_se_err)?;
            let iso_dt = super::datetime_etc::datetime_to_string(py_dt).map_err(py_err_se_err)?;
            serializer.serialize_str(&iso_dt)
        }
        ObType::Date => {
            let py_date: &PyDate = value.cast_as().map_err(py_err_se_err)?;
            let iso_date = super::datetime_etc::date_to_string(py_date).map_err(py_err_se_err)?;
            serializer.serialize_str(&iso_date)
        }
        ObType::Time => {
            let py_time: &PyTime = value.cast_as().map_err(py_err_se_err)?;
            let iso_time = super::datetime_etc::time_to_string(py_time).map_err(py_err_se_err)?;
            serializer.serialize_str(&iso_time)
        }
        ObType::Timedelta => {
            let py_timedelta: &PyDelta = value.cast_as().map_err(py_err_se_err)?;
            extra
                .config
                .timedelta_mode
                .timedelta_serialize(py_timedelta, serializer)
        }
        ObType::Url => {
            let py_url: PyUrl = value.extract().map_err(py_err_se_err)?;
            serializer.serialize_str(py_url.__str__())
        }
        ObType::MultiHostUrl => {
            let py_url: PyMultiHostUrl = value.extract().map_err(py_err_se_err)?;
            serializer.serialize_str(&py_url.__str__())
        }
        ObType::Dataclass => serialize_dict!(object_to_dict(value, false, extra).map_err(py_err_se_err)?),
        ObType::PydanticModel => serialize_dict!(object_to_dict(value, true, extra).map_err(py_err_se_err)?),
        ObType::Unknown => return Err(py_err_se_err(unknown_type_error(value))),
    };
    extra.rec_guard.pop(value_id);
    ser_result
}

fn unknown_type_error(value: &PyAny) -> PyErr {
    PydanticSerializationError::new_err(format!("Unable to serialize unknown type: {}", safe_repr(value)))
}

pub(crate) fn fallback_json_key<'py>(key: &'py PyAny, extra: &Extra) -> PyResult<Cow<'py, str>> {
    let ob_type = extra.ob_type_lookup.get_type(key);

    match ob_type {
        ObType::None => Ok(Cow::Borrowed("None")),
        ObType::Bool => {
            let v = if key.is_true().unwrap_or(false) {
                "true"
            } else {
                "false"
            };
            Ok(Cow::Borrowed(v))
        }
        ObType::Str => {
            let py_str: &PyString = key.cast_as()?;
            Ok(Cow::Borrowed(py_str.to_str()?))
        }
        ObType::Bytes => extra.config.bytes_mode.bytes_to_string(key.cast_as()?),
        // perhaps we could do something faster for things like ints and floats?
        ObType::Datetime => {
            let py_dt: &PyDateTime = key.cast_as()?;
            let iso_dt = super::datetime_etc::datetime_to_string(py_dt)?;
            Ok(Cow::Owned(iso_dt))
        }
        ObType::Date => {
            let py_date: &PyDate = key.cast_as()?;
            let iso_date = super::datetime_etc::date_to_string(py_date)?;
            Ok(Cow::Owned(iso_date))
        }
        ObType::Time => {
            let py_time: &PyTime = key.cast_as()?;
            let iso_time = super::datetime_etc::time_to_string(py_time)?;
            Ok(Cow::Owned(iso_time))
        }
        ObType::Timedelta => {
            let py_timedelta: &PyDelta = key.cast_as()?;
            extra.config.timedelta_mode.json_key(py_timedelta)
        }
        ObType::Url => {
            let py_url: PyUrl = key.extract()?;
            Ok(Cow::Owned(py_url.__str__().to_string()))
        }
        ObType::MultiHostUrl => {
            let py_url: PyMultiHostUrl = key.extract()?;
            Ok(Cow::Owned(py_url.__str__()))
        }
        _ => Ok(key.str()?.to_string_lossy()),
    }
}
