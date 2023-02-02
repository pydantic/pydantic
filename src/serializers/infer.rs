use std::borrow::Cow;

use pyo3::exceptions::PyTypeError;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{
    PyByteArray, PyBytes, PyDate, PyDateTime, PyDelta, PyDict, PyFrozenSet, PyIterator, PyList, PySet, PyString,
    PyTime, PyTuple,
};

use serde::ser::{Serialize, SerializeMap, SerializeSeq, Serializer};

use crate::build_tools::{py_err, safe_repr};
use crate::serializers::filter::SchemaFilter;
use crate::url::{PyMultiHostUrl, PyUrl};

use super::errors::{py_err_se_err, PydanticSerializationError};
use super::extra::{Extra, SerMode};
use super::filter::AnyFilter;
use super::ob_type::ObType;
use super::shared::object_to_dict;

pub(crate) fn infer_to_python(
    value: &PyAny,
    include: Option<&PyAny>,
    exclude: Option<&PyAny>,
    extra: &Extra,
) -> PyResult<PyObject> {
    infer_to_python_known(&extra.ob_type_lookup.get_type(value), value, include, exclude, extra)
}

pub(crate) fn infer_to_python_known(
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

    macro_rules! serialize_seq {
        ($t:ty) => {
            value
                .downcast::<$t>()?
                .iter()
                .map(|v| infer_to_python(v, None, None, extra))
                .collect::<PyResult<Vec<PyObject>>>()?
        };
    }

    macro_rules! serialize_seq_filter {
        ($t:ty) => {{
            let py_seq: &$t = value.downcast()?;
            let mut items = Vec::with_capacity(py_seq.len());
            let filter = AnyFilter::new();

            for (index, element) in py_seq.iter().enumerate() {
                let op_next = filter.index_filter(index, include, exclude)?;
                if let Some((next_include, next_exclude)) = op_next {
                    items.push(infer_to_python(element, next_include, next_exclude, extra)?);
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
                let k_str = infer_json_key(k, extra)?;
                let k = PyString::new(py, &k_str);
                let v = infer_to_python(v, next_include, next_exclude, extra)?;
                new_dict.set_item(k, v)?;
            }
        }
        Ok::<PyObject, PyErr>(new_dict.into_py(py))
    };

    let value = match extra.mode {
        SerMode::Json => match ob_type {
            // `bool` and `None` can't be subclasses, `ObType::Int`, `ObType::Float`, `ObType::Str` refer to exact types
            ObType::None | ObType::Bool | ObType::Int | ObType::Float | ObType::Str => value.into_py(py),
            // have to do this to make sure subclasses of for example str are upcast to `str`
            ObType::IntSubclass => value.extract::<i64>()?.into_py(py),
            ObType::FloatSubclass => value.extract::<f64>()?.into_py(py),
            ObType::Decimal => value.to_string().into_py(py),
            ObType::StrSubclass => value.extract::<&str>()?.into_py(py),
            ObType::Bytes => extra
                .config
                .bytes_mode
                .bytes_to_string(py, value.downcast::<PyBytes>()?.as_bytes())
                .map(|s| s.into_py(py))?,
            ObType::Bytearray => {
                let py_byte_array: &PyByteArray = value.downcast()?;
                // see https://docs.rs/pyo3/latest/pyo3/types/struct.PyByteArray.html#method.as_bytes
                // for why this is marked unsafe
                let bytes = unsafe { py_byte_array.as_bytes() };
                extra
                    .config
                    .bytes_mode
                    .bytes_to_string(py, bytes)
                    .map(|s| s.into_py(py))?
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
            ObType::Dict => serialize_dict(value.downcast()?)?,
            ObType::Datetime => {
                let py_dt: &PyDateTime = value.downcast()?;
                let iso_dt = super::type_serializers::datetime_etc::datetime_to_string(py_dt)?;
                iso_dt.into_py(py)
            }
            ObType::Date => {
                let py_date: &PyDate = value.downcast()?;
                let iso_date = super::type_serializers::datetime_etc::date_to_string(py_date)?;
                iso_date.into_py(py)
            }
            ObType::Time => {
                let py_time: &PyTime = value.downcast()?;
                let iso_time = super::type_serializers::datetime_etc::time_to_string(py_time)?;
                iso_time.into_py(py)
            }
            ObType::Timedelta => {
                let py_timedelta: &PyDelta = value.downcast()?;
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
            ObType::Model => serialize_dict(object_to_dict(value, true, extra)?)?,
            ObType::Enum => {
                let v = value.getattr(intern!(py, "value"))?;
                infer_to_python(v, include, exclude, extra)?.into_py(py)
            }
            ObType::Generator => {
                let py_seq: &PyIterator = value.downcast()?;
                let mut items = Vec::new();
                let filter = AnyFilter::new();

                for (index, r) in py_seq.iter()?.enumerate() {
                    let element = r?;
                    let op_next = filter.index_filter(index, include, exclude)?;
                    if let Some((next_include, next_exclude)) = op_next {
                        items.push(infer_to_python(element, next_include, next_exclude, extra)?);
                    }
                }
                PyList::new(py, items).into_py(py)
            }
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
                let dict: &PyDict = value.downcast()?;
                let new_dict = PyDict::new(py);
                let filter = AnyFilter::new();

                for (k, v) in dict {
                    let op_next = filter.key_filter(k, include, exclude)?;
                    if let Some((next_include, next_exclude)) = op_next {
                        let v = infer_to_python(v, next_include, next_exclude, extra)?;
                        new_dict.set_item(k, v)?;
                    }
                }
                new_dict.into_py(py)
            }
            ObType::Dataclass => serialize_dict(object_to_dict(value, false, extra)?)?,
            ObType::Model => serialize_dict(object_to_dict(value, true, extra)?)?,
            ObType::Generator => {
                let iter = super::type_serializers::generator::SerializationIterator::new(
                    value.downcast()?,
                    super::type_serializers::any::AnySerializer::default().into(),
                    SchemaFilter::default(),
                    include,
                    exclude,
                    extra,
                );
                iter.into_py(py)
            }
            _ => value.into_py(py),
        },
    };
    extra.rec_guard.pop(value_id);
    Ok(value)
}

pub(crate) struct SerializeInfer<'py> {
    value: &'py PyAny,
    include: Option<&'py PyAny>,
    exclude: Option<&'py PyAny>,
    extra: &'py Extra<'py>,
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
            include,
            exclude,
            extra,
        }
    }
}

impl<'py> Serialize for SerializeInfer<'py> {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        let ob_type = self.extra.ob_type_lookup.get_type(self.value);
        infer_serialize_known(&ob_type, self.value, serializer, self.include, self.exclude, self.extra)
    }
}

pub(crate) fn infer_serialize<S: Serializer>(
    value: &PyAny,
    serializer: S,
    include: Option<&PyAny>,
    exclude: Option<&PyAny>,
    extra: &Extra,
) -> Result<S::Ok, S::Error> {
    infer_serialize_known(
        &extra.ob_type_lookup.get_type(value),
        value,
        serializer,
        include,
        exclude,
        extra,
    )
}

pub(crate) fn infer_serialize_known<S: Serializer>(
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
            let py_seq: &$t = value.downcast().map_err(py_err_se_err)?;
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
            let py_seq: &$t = value.downcast().map_err(py_err_se_err)?;
            let mut seq = serializer.serialize_seq(Some(py_seq.len()))?;
            let filter = AnyFilter::new();
            for (index, element) in py_seq.iter().enumerate() {
                let op_next = filter.index_filter(index, include, exclude).map_err(py_err_se_err)?;
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
                    let key = infer_json_key(key, extra).map_err(py_err_se_err)?;
                    let value_serializer = SerializeInfer::new(value, next_include, next_exclude, extra);
                    map.serialize_entry(&key, &value_serializer)?;
                }
            }
            map.end()
        }};
    }

    let ser_result = match ob_type {
        ObType::None => serializer.serialize_none(),
        ObType::Int | ObType::IntSubclass => serialize!(i64),
        ObType::Bool => serialize!(bool),
        ObType::Float | ObType::FloatSubclass => serialize!(f64),
        ObType::Decimal => value.to_string().serialize(serializer),
        ObType::Str | ObType::StrSubclass => {
            let py_str: &PyString = value.downcast().map_err(py_err_se_err)?;
            super::type_serializers::string::serialize_py_str(py_str, serializer)
        }
        ObType::Bytes => {
            let py_bytes: &PyBytes = value.downcast().map_err(py_err_se_err)?;
            extra.config.bytes_mode.serialize_bytes(py_bytes.as_bytes(), serializer)
        }
        ObType::Bytearray => {
            let py_byte_array: &PyByteArray = value.downcast().map_err(py_err_se_err)?;
            let bytes = unsafe { py_byte_array.as_bytes() };
            extra.config.bytes_mode.serialize_bytes(bytes, serializer)
        }
        ObType::Dict => serialize_dict!(value.downcast::<PyDict>().map_err(py_err_se_err)?),
        ObType::List => serialize_seq_filter!(PyList),
        ObType::Tuple => serialize_seq_filter!(PyTuple),
        ObType::Set => serialize_seq!(PySet),
        ObType::Frozenset => serialize_seq!(PyFrozenSet),
        ObType::Datetime => {
            let py_dt: &PyDateTime = value.downcast().map_err(py_err_se_err)?;
            let iso_dt = super::type_serializers::datetime_etc::datetime_to_string(py_dt).map_err(py_err_se_err)?;
            serializer.serialize_str(&iso_dt)
        }
        ObType::Date => {
            let py_date: &PyDate = value.downcast().map_err(py_err_se_err)?;
            let iso_date = super::type_serializers::datetime_etc::date_to_string(py_date).map_err(py_err_se_err)?;
            serializer.serialize_str(&iso_date)
        }
        ObType::Time => {
            let py_time: &PyTime = value.downcast().map_err(py_err_se_err)?;
            let iso_time = super::type_serializers::datetime_etc::time_to_string(py_time).map_err(py_err_se_err)?;
            serializer.serialize_str(&iso_time)
        }
        ObType::Timedelta => {
            let py_timedelta: &PyDelta = value.downcast().map_err(py_err_se_err)?;
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
        ObType::Model => serialize_dict!(object_to_dict(value, true, extra).map_err(py_err_se_err)?),
        ObType::Enum => {
            let v = value.getattr(intern!(value.py(), "value")).map_err(py_err_se_err)?;
            infer_serialize(v, serializer, include, exclude, extra)
        }
        ObType::Generator => {
            let py_seq: &PyIterator = value.downcast().map_err(py_err_se_err)?;
            let mut seq = serializer.serialize_seq(None)?;
            let filter = AnyFilter::new();
            for (index, r) in py_seq.iter().map_err(py_err_se_err)?.enumerate() {
                let element = r.map_err(py_err_se_err)?;
                let op_next = filter.index_filter(index, include, exclude).map_err(py_err_se_err)?;
                if let Some((next_include, next_exclude)) = op_next {
                    let item_serializer = SerializeInfer::new(element, next_include, next_exclude, extra);
                    seq.serialize_element(&item_serializer)?
                }
            }
            seq.end()
        }
        ObType::Unknown => return Err(py_err_se_err(unknown_type_error(value))),
    };
    extra.rec_guard.pop(value_id);
    ser_result
}

fn unknown_type_error(value: &PyAny) -> PyErr {
    PydanticSerializationError::new_err(format!("Unable to serialize unknown type: {}", safe_repr(value)))
}

pub(crate) fn infer_json_key<'py>(key: &'py PyAny, extra: &Extra) -> PyResult<Cow<'py, str>> {
    let ob_type = extra.ob_type_lookup.get_type(key);
    infer_json_key_known(&ob_type, key, extra)
}

pub(crate) fn infer_json_key_known<'py>(ob_type: &ObType, key: &'py PyAny, extra: &Extra) -> PyResult<Cow<'py, str>> {
    match ob_type {
        ObType::None => super::type_serializers::simple::none_json_key(),
        ObType::Int | ObType::IntSubclass | ObType::Float | ObType::FloatSubclass => {
            super::type_serializers::simple::to_str_json_key(key)
        }
        ObType::Decimal => Ok(Cow::Owned(key.to_string())),
        ObType::Bool => super::type_serializers::simple::bool_json_key(key),
        ObType::Str | ObType::StrSubclass => {
            let py_str: &PyString = key.downcast()?;
            Ok(Cow::Borrowed(py_str.to_str()?))
        }
        ObType::Bytes => extra
            .config
            .bytes_mode
            .bytes_to_string(key.py(), key.downcast::<PyBytes>()?.as_bytes()),
        ObType::Bytearray => {
            let py_byte_array: &PyByteArray = key.downcast()?;
            let bytes = unsafe { py_byte_array.as_bytes() };
            extra.config.bytes_mode.bytes_to_string(key.py(), bytes)
        }
        ObType::Datetime => {
            let py_dt: &PyDateTime = key.downcast()?;
            let iso_dt = super::type_serializers::datetime_etc::datetime_to_string(py_dt)?;
            Ok(Cow::Owned(iso_dt))
        }
        ObType::Date => {
            let py_date: &PyDate = key.downcast()?;
            let iso_date = super::type_serializers::datetime_etc::date_to_string(py_date)?;
            Ok(Cow::Owned(iso_date))
        }
        ObType::Time => {
            let py_time: &PyTime = key.downcast()?;
            let iso_time = super::type_serializers::datetime_etc::time_to_string(py_time)?;
            Ok(Cow::Owned(iso_time))
        }
        ObType::Timedelta => {
            let py_timedelta: &PyDelta = key.downcast()?;
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
        ObType::Tuple => {
            let mut key_build = super::type_serializers::tuple::KeyBuilder::new();
            for element in key.downcast::<PyTuple>()?.iter() {
                key_build.push(&infer_json_key(element, extra)?);
            }
            Ok(Cow::Owned(key_build.finish()))
        }
        ObType::List | ObType::Set | ObType::Frozenset | ObType::Dict | ObType::Generator => {
            py_err!(PyTypeError; "`{}` not valid as object key", ob_type)
        }
        ObType::Dataclass | ObType::Model => {
            // check that the instance is hashable
            key.hash()?;
            let key = key.str()?.to_string();
            Ok(Cow::Owned(key))
        }
        ObType::Enum => {
            let k = key.getattr(intern!(key.py(), "value"))?;
            infer_json_key(k, extra)
        }
        ObType::Unknown => Err(unknown_type_error(key)),
    }
}
