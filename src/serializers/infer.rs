use std::borrow::Cow;

use pyo3::exceptions::PyTypeError;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::pybacked::PyBackedStr;
use pyo3::types::PyComplex;
use pyo3::types::{PyByteArray, PyBytes, PyDict, PyFrozenSet, PyIterator, PyList, PySet, PyString, PyTuple};

use serde::ser::{Error, Serialize, SerializeMap, SerializeSeq, Serializer};

use crate::input::{EitherTimedelta, Int};
use crate::serializers::type_serializers;
use crate::tools::{extract_int, py_err, safe_repr};
use crate::url::{PyMultiHostUrl, PyUrl};

use super::config::InfNanMode;
use super::errors::SERIALIZATION_ERR_MARKER;
use super::errors::{py_err_se_err, PydanticSerializationError};
use super::extra::{Extra, SerMode};
use super::filter::{AnyFilter, SchemaFilter};
use super::ob_type::ObType;
use super::shared::{any_dataclass_iter, PydanticSerializer, TypeSerializer};
use super::SchemaSerializer;

pub(crate) fn infer_to_python(
    value: &Bound<'_, PyAny>,
    include: Option<&Bound<'_, PyAny>>,
    exclude: Option<&Bound<'_, PyAny>>,
    extra: &Extra,
) -> PyResult<PyObject> {
    infer_to_python_known(extra.ob_type_lookup.get_type(value), value, include, exclude, extra)
}

// arbitrary ids to identify that we recursed through infer_to_{python,json}_known
// We just need them to be different from definition ref slot ids, which start at 0
const INFER_DEF_REF_ID: usize = usize::MAX;

pub(crate) fn infer_to_python_known(
    ob_type: ObType,
    value: &Bound<'_, PyAny>,
    include: Option<&Bound<'_, PyAny>>,
    exclude: Option<&Bound<'_, PyAny>>,
    mut extra: &Extra,
) -> PyResult<PyObject> {
    let py = value.py();

    let mode = extra.mode;
    let mut guard = match extra.recursion_guard(value, INFER_DEF_REF_ID) {
        Ok(v) => v,
        Err(e) => {
            return match mode {
                SerMode::Json => Err(e),
                // if recursion is detected by we're serializing to python, we just return the value
                _ => Ok(value.into_py(py)),
            };
        }
    };
    let extra = guard.state();

    macro_rules! serialize_seq {
        ($t:ty) => {
            value
                .downcast::<$t>()?
                .iter()
                .map(|v| infer_to_python(&v, None, None, extra))
                .collect::<PyResult<Vec<PyObject>>>()?
        };
    }

    macro_rules! serialize_seq_filter {
        ($t:ty) => {{
            let py_seq = value.downcast::<$t>()?;
            let mut items = Vec::with_capacity(py_seq.len());
            let filter = AnyFilter::new();
            let len = value.len().ok();

            for (index, element) in py_seq.iter().enumerate() {
                let op_next = filter.index_filter(index, include, exclude, len)?;
                if let Some((next_include, next_exclude)) = op_next {
                    items.push(infer_to_python(
                        &element,
                        next_include.as_ref(),
                        next_exclude.as_ref(),
                        extra,
                    )?);
                }
            }
            items
        }};
    }

    let serialize_with_serializer = || {
        let py_serializer = value.getattr(intern!(py, "__pydantic_serializer__"))?;
        let serializer: PyRef<SchemaSerializer> = py_serializer.extract()?;
        let extra = serializer.build_extra(
            py,
            extra.mode,
            extra.by_alias,
            extra.warnings,
            extra.exclude_unset,
            extra.exclude_defaults,
            extra.exclude_none,
            extra.round_trip,
            extra.rec_guard,
            extra.serialize_unknown,
            extra.fallback,
            extra.duck_typing_ser_mode,
            extra.context,
        );
        serializer.serializer.to_python(value, include, exclude, &extra)
    };

    let value = match extra.mode {
        SerMode::Json => match ob_type {
            // `bool` and `None` can't be subclasses, `ObType::Int`, `ObType::Float`, `ObType::Str` refer to exact types
            ObType::None | ObType::Bool | ObType::Int | ObType::Str => value.into_py(py),
            // have to do this to make sure subclasses of for example str are upcast to `str`
            ObType::IntSubclass => {
                if let Some(i) = extract_int(value) {
                    i.into_py(py)
                } else {
                    return py_err!(PyTypeError; "Expected int, got {}", safe_repr(value));
                }
            }
            ObType::Float | ObType::FloatSubclass => {
                let v = value.extract::<f64>()?;
                if (v.is_nan() || v.is_infinite()) && extra.config.inf_nan_mode == InfNanMode::Null {
                    return Ok(py.None().into_py(py));
                }
                v.into_py(py)
            }
            ObType::Decimal => value.to_string().into_py(py),
            ObType::StrSubclass => value.downcast::<PyString>()?.to_str()?.into_py(py),
            ObType::Bytes => extra
                .config
                .bytes_mode
                .bytes_to_string(py, value.downcast::<PyBytes>()?.as_bytes())
                .map(|s| s.into_py(py))?,
            ObType::Bytearray => {
                let py_byte_array = value.downcast::<PyByteArray>()?;
                // Safety: the GIL is held while bytes_to_string is running; it doesn't run
                // arbitrary Python code, so py_byte_array cannot be mutated.
                let bytes = unsafe { py_byte_array.as_bytes() };
                extra
                    .config
                    .bytes_mode
                    .bytes_to_string(py, bytes)
                    .map(|s| s.into_py(py))?
            }
            ObType::Tuple => {
                let elements = serialize_seq_filter!(PyTuple);
                PyList::new_bound(py, elements).into_py(py)
            }
            ObType::List => {
                let elements = serialize_seq_filter!(PyList);
                PyList::new_bound(py, elements).into_py(py)
            }
            ObType::Set => {
                let elements = serialize_seq!(PySet);
                PyList::new_bound(py, elements).into_py(py)
            }
            ObType::Frozenset => {
                let elements = serialize_seq!(PyFrozenSet);
                PyList::new_bound(py, elements).into_py(py)
            }
            ObType::Dict => {
                let dict = value.downcast::<PyDict>()?;
                serialize_pairs_python(py, dict.iter().map(Ok), include, exclude, extra, |k| {
                    Ok(PyString::new_bound(py, &infer_json_key(&k, extra)?).into_any())
                })?
            }
            ObType::Datetime => {
                let iso_dt = super::type_serializers::datetime_etc::datetime_to_string(value.downcast()?)?;
                iso_dt.into_py(py)
            }
            ObType::Date => {
                let iso_date = super::type_serializers::datetime_etc::date_to_string(value.downcast()?)?;
                iso_date.into_py(py)
            }
            ObType::Time => {
                let iso_time = super::type_serializers::datetime_etc::time_to_string(value.downcast()?)?;
                iso_time.into_py(py)
            }
            ObType::Timedelta => {
                let either_delta = EitherTimedelta::try_from(value)?;
                extra
                    .config
                    .timedelta_mode
                    .either_delta_to_json(value.py(), &either_delta)?
            }
            ObType::Url => {
                let py_url: PyUrl = value.extract()?;
                py_url.__str__().into_py(py)
            }
            ObType::MultiHostUrl => {
                let py_url: PyMultiHostUrl = value.extract()?;
                py_url.__str__().into_py(py)
            }
            ObType::Uuid => {
                let uuid = super::type_serializers::uuid::uuid_to_string(value)?;
                uuid.into_py(py)
            }
            ObType::PydanticSerializable => serialize_with_serializer()?,
            ObType::Dataclass => {
                serialize_pairs_python(py, any_dataclass_iter(value)?.0, include, exclude, extra, |k| {
                    Ok(PyString::new_bound(py, &infer_json_key(&k, extra)?).into_any())
                })?
            }
            ObType::Enum => {
                let v = value.getattr(intern!(py, "value"))?;
                infer_to_python(&v, include, exclude, extra)?.into_py(py)
            }
            ObType::Generator => {
                let py_seq = value.downcast::<PyIterator>()?;
                let mut items = Vec::new();
                let filter = AnyFilter::new();

                for (index, r) in py_seq.iter()?.enumerate() {
                    let element = r?;
                    let op_next = filter.index_filter(index, include, exclude, None)?;
                    if let Some((next_include, next_exclude)) = op_next {
                        items.push(infer_to_python(
                            &element,
                            next_include.as_ref(),
                            next_exclude.as_ref(),
                            extra,
                        )?);
                    }
                }
                PyList::new_bound(py, items).into_py(py)
            }
            ObType::Complex => {
                let dict = value.downcast::<PyDict>()?;
                let new_dict = PyDict::new_bound(py);
                let _ = new_dict.set_item("real", dict.get_item("real")?);
                let _ = new_dict.set_item("imag", dict.get_item("imag")?);
                new_dict.into_py(py)
            }
            ObType::Path => value.str()?.into_py(py),
            ObType::Pattern => value.getattr(intern!(py, "pattern"))?.into_py(py),
            ObType::Unknown => {
                if let Some(fallback) = extra.fallback {
                    let next_value = fallback.call1((value,))?;
                    let next_result = infer_to_python(&next_value, include, exclude, extra);
                    return next_result;
                } else if extra.serialize_unknown {
                    serialize_unknown(value).into_py(py)
                } else {
                    return Err(unknown_type_error(value));
                }
            }
        },
        _ => match ob_type {
            ObType::Tuple => {
                let elements = serialize_seq_filter!(PyTuple);
                PyTuple::new_bound(py, elements).into_py(py)
            }
            ObType::List => {
                let elements = serialize_seq_filter!(PyList);
                PyList::new_bound(py, elements).into_py(py)
            }
            ObType::Set => {
                let elements = serialize_seq!(PySet);
                PySet::new_bound(py, &elements)?.into_py(py)
            }
            ObType::Frozenset => {
                let elements = serialize_seq!(PyFrozenSet);
                PyFrozenSet::new_bound(py, &elements)?.into_py(py)
            }
            ObType::Dict => {
                let dict = value.downcast::<PyDict>()?;
                serialize_pairs_python(py, dict.iter().map(Ok), include, exclude, extra, Ok)?
            }
            ObType::PydanticSerializable => serialize_with_serializer()?,
            ObType::Dataclass => serialize_pairs_python(py, any_dataclass_iter(value)?.0, include, exclude, extra, Ok)?,
            ObType::Generator => {
                let iter = super::type_serializers::generator::SerializationIterator::new(
                    value.downcast()?,
                    super::type_serializers::any::AnySerializer::get(),
                    SchemaFilter::default(),
                    include,
                    exclude,
                    extra,
                );
                iter.into_py(py)
            }
            ObType::Complex => {
                let dict = value.downcast::<PyDict>()?;
                let new_dict = PyDict::new_bound(py);
                let _ = new_dict.set_item("real", dict.get_item("real")?);
                let _ = new_dict.set_item("imag", dict.get_item("imag")?);
                new_dict.into_py(py)
            }
            ObType::Unknown => {
                if let Some(fallback) = extra.fallback {
                    let next_value = fallback.call1((value,))?;
                    let next_result = infer_to_python(&next_value, include, exclude, extra);
                    return next_result;
                }
                value.into_py(py)
            }
            _ => value.into_py(py),
        },
    };
    Ok(value)
}

pub(crate) struct SerializeInfer<'py> {
    value: &'py Bound<'py, PyAny>,
    include: Option<&'py Bound<'py, PyAny>>,
    exclude: Option<&'py Bound<'py, PyAny>>,
    extra: &'py Extra<'py>,
}

impl<'py> SerializeInfer<'py> {
    pub(crate) fn new(
        value: &'py Bound<'py, PyAny>,
        include: Option<&'py Bound<'py, PyAny>>,
        exclude: Option<&'py Bound<'py, PyAny>>,
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
        infer_serialize_known(ob_type, self.value, serializer, self.include, self.exclude, self.extra)
    }
}

pub(crate) fn infer_serialize<S: Serializer>(
    value: &Bound<'_, PyAny>,
    serializer: S,
    include: Option<&Bound<'_, PyAny>>,
    exclude: Option<&Bound<'_, PyAny>>,
    extra: &Extra,
) -> Result<S::Ok, S::Error> {
    infer_serialize_known(
        extra.ob_type_lookup.get_type(value),
        value,
        serializer,
        include,
        exclude,
        extra,
    )
}

pub(crate) fn infer_serialize_known<S: Serializer>(
    ob_type: ObType,
    value: &Bound<'_, PyAny>,
    serializer: S,
    include: Option<&Bound<'_, PyAny>>,
    exclude: Option<&Bound<'_, PyAny>>,
    mut extra: &Extra,
) -> Result<S::Ok, S::Error> {
    let extra_serialize_unknown = extra.serialize_unknown;
    let mut guard = match extra.recursion_guard(value, INFER_DEF_REF_ID) {
        Ok(v) => v,
        Err(e) => {
            return if extra_serialize_unknown {
                serializer.serialize_str("...")
            } else {
                Err(py_err_se_err(e))
            };
        }
    };
    let extra = guard.state();

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
            let py_seq = value.downcast::<$t>().map_err(py_err_se_err)?;
            let mut seq = serializer.serialize_seq(Some(py_seq.len()))?;
            for element in py_seq.iter() {
                let item_serializer = SerializeInfer::new(&element, include, exclude, extra);
                seq.serialize_element(&item_serializer)?
            }
            seq.end()
        }};
    }

    macro_rules! serialize_seq_filter {
        ($t:ty) => {{
            let py_seq = value.downcast::<$t>().map_err(py_err_se_err)?;
            let mut seq = serializer.serialize_seq(Some(py_seq.len()))?;
            let filter = AnyFilter::new();
            let len = value.len().ok();

            for (index, element) in py_seq.iter().enumerate() {
                let op_next = filter
                    .index_filter(index, include, exclude, len)
                    .map_err(py_err_se_err)?;
                if let Some((next_include, next_exclude)) = op_next {
                    let item_serializer =
                        SerializeInfer::new(&element, next_include.as_ref(), next_exclude.as_ref(), extra);
                    seq.serialize_element(&item_serializer)?
                }
            }
            seq.end()
        }};
    }

    let ser_result = match ob_type {
        ObType::None => serializer.serialize_none(),
        ObType::Int | ObType::IntSubclass => serialize!(Int),
        ObType::Bool => serialize!(bool),
        ObType::Complex => {
            let v = value.downcast::<PyComplex>().map_err(py_err_se_err)?;
            let mut map = serializer.serialize_map(Some(2))?;
            map.serialize_entry(&"real", &v.real())?;
            map.serialize_entry(&"imag", &v.imag())?;
            map.end()
        }
        ObType::Float | ObType::FloatSubclass => {
            let v = value.extract::<f64>().map_err(py_err_se_err)?;
            type_serializers::float::serialize_f64(v, serializer, extra.config.inf_nan_mode)
        }
        ObType::Decimal => value.to_string().serialize(serializer),
        ObType::Str | ObType::StrSubclass => {
            let py_str = value.downcast::<PyString>().map_err(py_err_se_err)?;
            super::type_serializers::string::serialize_py_str(py_str, serializer)
        }
        ObType::Bytes => {
            let py_bytes = value.downcast::<PyBytes>().map_err(py_err_se_err)?;
            extra.config.bytes_mode.serialize_bytes(py_bytes.as_bytes(), serializer)
        }
        ObType::Bytearray => {
            let py_byte_array = value.downcast::<PyByteArray>().map_err(py_err_se_err)?;
            // Safety: the GIL is held while serialize_bytes is running; it doesn't run
            // arbitrary Python code, so py_byte_array cannot be mutated.
            extra
                .config
                .bytes_mode
                .serialize_bytes(unsafe { py_byte_array.as_bytes() }, serializer)
        }
        ObType::Dict => {
            let dict = value.downcast::<PyDict>().map_err(py_err_se_err)?;
            serialize_pairs_json(dict.iter().map(Ok), dict.len(), serializer, include, exclude, extra)
        }
        ObType::List => serialize_seq_filter!(PyList),
        ObType::Tuple => serialize_seq_filter!(PyTuple),
        ObType::Set => serialize_seq!(PySet),
        ObType::Frozenset => serialize_seq!(PyFrozenSet),
        ObType::Datetime => {
            let py_dt = value.downcast().map_err(py_err_se_err)?;
            let iso_dt = super::type_serializers::datetime_etc::datetime_to_string(py_dt).map_err(py_err_se_err)?;
            serializer.serialize_str(&iso_dt)
        }
        ObType::Date => {
            let py_date = value.downcast().map_err(py_err_se_err)?;
            let iso_date = super::type_serializers::datetime_etc::date_to_string(py_date).map_err(py_err_se_err)?;
            serializer.serialize_str(&iso_date)
        }
        ObType::Time => {
            let py_time = value.downcast().map_err(py_err_se_err)?;
            let iso_time = super::type_serializers::datetime_etc::time_to_string(py_time).map_err(py_err_se_err)?;
            serializer.serialize_str(&iso_time)
        }
        ObType::Timedelta => {
            let either_delta = EitherTimedelta::try_from(value).map_err(py_err_se_err)?;
            extra
                .config
                .timedelta_mode
                .timedelta_serialize(value.py(), &either_delta, serializer)
        }
        ObType::Url => {
            let py_url: PyUrl = value.extract().map_err(py_err_se_err)?;
            serializer.serialize_str(py_url.__str__())
        }
        ObType::MultiHostUrl => {
            let py_url: PyMultiHostUrl = value.extract().map_err(py_err_se_err)?;
            serializer.serialize_str(&py_url.__str__())
        }
        ObType::PydanticSerializable => {
            let py = value.py();
            let py_serializer = value
                .getattr(intern!(py, "__pydantic_serializer__"))
                .map_err(py_err_se_err)?;
            let extracted_serializer: PyRef<SchemaSerializer> = py_serializer.extract().map_err(py_err_se_err)?;
            let extra = extracted_serializer.build_extra(
                py,
                extra.mode,
                extra.by_alias,
                extra.warnings,
                extra.exclude_unset,
                extra.exclude_defaults,
                extra.exclude_none,
                extra.round_trip,
                extra.rec_guard,
                extra.serialize_unknown,
                extra.fallback,
                extra.duck_typing_ser_mode,
                extra.context,
            );
            let pydantic_serializer =
                PydanticSerializer::new(value, &extracted_serializer.serializer, include, exclude, &extra);
            pydantic_serializer.serialize(serializer)
        }
        ObType::Dataclass => {
            let (pairs_iter, fields_dict) = any_dataclass_iter(value).map_err(py_err_se_err)?;
            serialize_pairs_json(pairs_iter, fields_dict.len(), serializer, include, exclude, extra)
        }
        ObType::Uuid => {
            let uuid = super::type_serializers::uuid::uuid_to_string(value).map_err(py_err_se_err)?;
            serializer.serialize_str(&uuid)
        }
        ObType::Enum => {
            let v = value.getattr(intern!(value.py(), "value")).map_err(py_err_se_err)?;
            infer_serialize(&v, serializer, include, exclude, extra)
        }
        ObType::Generator => {
            let py_seq = value.downcast::<PyIterator>().map_err(py_err_se_err)?;
            let mut seq = serializer.serialize_seq(None)?;
            let filter = AnyFilter::new();
            for (index, r) in py_seq.iter().map_err(py_err_se_err)?.enumerate() {
                let element = r.map_err(py_err_se_err)?;
                let op_next = filter
                    .index_filter(index, include, exclude, None)
                    .map_err(py_err_se_err)?;
                if let Some((next_include, next_exclude)) = op_next {
                    let item_serializer =
                        SerializeInfer::new(&element, next_include.as_ref(), next_exclude.as_ref(), extra);
                    seq.serialize_element(&item_serializer)?;
                }
            }
            seq.end()
        }
        ObType::Path => {
            let s: PyBackedStr = value
                .str()
                .and_then(|value_str| value_str.extract())
                .map_err(py_err_se_err)?;
            serializer.serialize_str(&s)
        }
        ObType::Pattern => {
            let s: PyBackedStr = value
                .getattr(intern!(value.py(), "pattern"))
                .and_then(|pattern| pattern.str()?.extract())
                .map_err(py_err_se_err)?;
            serializer.serialize_str(&s)
        }
        ObType::Unknown => {
            if let Some(fallback) = extra.fallback {
                let next_value = fallback.call1((value,)).map_err(py_err_se_err)?;
                let next_result = infer_serialize(&next_value, serializer, include, exclude, extra);
                return next_result;
            } else if extra.serialize_unknown {
                serializer.serialize_str(&serialize_unknown(value))
            } else {
                let msg = format!(
                    "{}Unable to serialize unknown type: {}",
                    SERIALIZATION_ERR_MARKER,
                    safe_repr(&value.get_type()),
                );
                return Err(S::Error::custom(msg));
            }
        }
    };
    ser_result
}

fn unknown_type_error(value: &Bound<'_, PyAny>) -> PyErr {
    PydanticSerializationError::new_err(format!(
        "Unable to serialize unknown type: {}",
        safe_repr(&value.get_type())
    ))
}

fn serialize_unknown<'py>(value: &Bound<'py, PyAny>) -> Cow<'py, str> {
    if let Ok(s) = value.str() {
        s.to_string_lossy().into_owned().into()
    } else if let Ok(name) = value.get_type().qualname() {
        format!("<Unserializable {name} object>").into()
    } else {
        "<Unserializable object>".into()
    }
}

pub(crate) fn infer_json_key<'a>(key: &'a Bound<'_, PyAny>, extra: &Extra) -> PyResult<Cow<'a, str>> {
    let ob_type = extra.ob_type_lookup.get_type(key);
    infer_json_key_known(ob_type, key, extra)
}

pub(crate) fn infer_json_key_known<'a>(
    ob_type: ObType,
    key: &'a Bound<'_, PyAny>,
    extra: &Extra,
) -> PyResult<Cow<'a, str>> {
    match ob_type {
        ObType::None => super::type_serializers::simple::none_json_key(),
        ObType::Int | ObType::IntSubclass => super::type_serializers::simple::to_str_json_key(key),
        ObType::Float | ObType::FloatSubclass => {
            let v = key.extract::<f64>()?;
            if (v.is_nan() || v.is_infinite()) && extra.config.inf_nan_mode == InfNanMode::Null {
                super::type_serializers::simple::none_json_key()
            } else {
                super::type_serializers::simple::to_str_json_key(key)
            }
        }
        ObType::Decimal => Ok(Cow::Owned(key.to_string())),
        ObType::Bool => super::type_serializers::simple::bool_json_key(key),
        ObType::Str | ObType::StrSubclass => {
            let py_str = key.downcast::<PyString>()?;
            Ok(Cow::Owned(py_str.to_str()?.to_string()))
        }
        ObType::Bytes => extra
            .config
            .bytes_mode
            .bytes_to_string(key.py(), key.downcast::<PyBytes>()?.as_bytes())
            // FIXME it would be nice to have a "PyCow" which carries ownership of the Python type too
            .map(|s| Cow::Owned(s.into_owned())),
        ObType::Bytearray => {
            let py_byte_array = key.downcast::<PyByteArray>()?;
            // Safety: the GIL is held while serialize_bytes is running; it doesn't run
            // arbitrary Python code, so py_byte_array cannot be mutated during the call.
            //
            // We copy the bytes into a new buffer immediately afterwards
            extra
                .config
                .bytes_mode
                .bytes_to_string(key.py(), unsafe { py_byte_array.as_bytes() })
                .map(|cow| Cow::Owned(cow.into_owned()))
        }
        ObType::Datetime => {
            let iso_dt = super::type_serializers::datetime_etc::datetime_to_string(key.downcast()?)?;
            Ok(Cow::Owned(iso_dt))
        }
        ObType::Date => {
            let iso_date = super::type_serializers::datetime_etc::date_to_string(key.downcast()?)?;
            Ok(Cow::Owned(iso_date))
        }
        ObType::Time => {
            let iso_time = super::type_serializers::datetime_etc::time_to_string(key.downcast()?)?;
            Ok(Cow::Owned(iso_time))
        }
        ObType::Uuid => {
            let uuid = super::type_serializers::uuid::uuid_to_string(key)?;
            Ok(Cow::Owned(uuid))
        }
        ObType::Timedelta => {
            let either_delta = EitherTimedelta::try_from(key)?;
            extra.config.timedelta_mode.json_key(key.py(), &either_delta)
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
            for element in key.downcast::<PyTuple>()?.iter_borrowed() {
                key_build.push(&infer_json_key(&element, extra)?);
            }
            Ok(Cow::Owned(key_build.finish()))
        }
        ObType::List | ObType::Set | ObType::Frozenset | ObType::Dict | ObType::Generator | ObType::Complex => {
            py_err!(PyTypeError; "`{}` not valid as object key", ob_type)
        }
        ObType::Dataclass | ObType::PydanticSerializable => {
            // check that the instance is hashable
            key.hash()?;
            let key = key.str()?.to_string();
            Ok(Cow::Owned(key))
        }
        ObType::Enum => {
            let k = key.getattr(intern!(key.py(), "value"))?;
            infer_json_key(&k, extra).map(|cow| Cow::Owned(cow.into_owned()))
        }
        ObType::Path => {
            // FIXME it would be nice to have a "PyCow" which carries ownership of the Python type too
            Ok(Cow::Owned(key.str()?.to_string_lossy().into_owned()))
        }
        ObType::Pattern => Ok(Cow::Owned(
            key.getattr(intern!(key.py(), "pattern"))?
                .str()?
                .to_string_lossy()
                .into_owned(),
        )),
        ObType::Unknown => {
            if let Some(fallback) = extra.fallback {
                let next_key = fallback.call1((key,))?;
                infer_json_key(&next_key, extra).map(|cow| Cow::Owned(cow.into_owned()))
            } else if extra.serialize_unknown {
                Ok(serialize_unknown(key))
            } else {
                Err(unknown_type_error(key))
            }
        }
    }
}

fn serialize_pairs_python<'py>(
    py: Python,
    pairs_iter: impl Iterator<Item = PyResult<(Bound<'py, PyAny>, Bound<'py, PyAny>)>>,
    include: Option<&Bound<'_, PyAny>>,
    exclude: Option<&Bound<'_, PyAny>>,
    extra: &Extra,
    key_transform: impl Fn(Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>>,
) -> PyResult<PyObject> {
    let new_dict = PyDict::new_bound(py);
    let filter = AnyFilter::new();

    for result in pairs_iter {
        let (k, v) = result?;
        let op_next = filter.key_filter(&k, include, exclude)?;
        if let Some((next_include, next_exclude)) = op_next {
            let k = key_transform(k)?;
            let v = infer_to_python(&v, next_include.as_ref(), next_exclude.as_ref(), extra)?;
            new_dict.set_item(k, v)?;
        }
    }
    Ok(new_dict.into_py(py))
}

fn serialize_pairs_json<'py, S: Serializer>(
    pairs_iter: impl Iterator<Item = PyResult<(Bound<'py, PyAny>, Bound<'py, PyAny>)>>,
    iter_size: usize,
    serializer: S,
    include: Option<&Bound<'_, PyAny>>,
    exclude: Option<&Bound<'_, PyAny>>,
    extra: &Extra,
) -> Result<S::Ok, S::Error> {
    let mut map = serializer.serialize_map(Some(iter_size))?;
    let filter = AnyFilter::new();

    for result in pairs_iter {
        let (key, value) = result.map_err(py_err_se_err)?;

        let op_next = filter.key_filter(&key, include, exclude).map_err(py_err_se_err)?;
        if let Some((next_include, next_exclude)) = op_next {
            let key = infer_json_key(&key, extra).map_err(py_err_se_err)?;
            let value_serializer = SerializeInfer::new(&value, next_include.as_ref(), next_exclude.as_ref(), extra);
            map.serialize_entry(&key, &value_serializer)?;
        }
    }
    map.end()
}
