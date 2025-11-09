use std::borrow::Cow;
use std::cell::RefCell;

use pyo3::exceptions::PyTypeError;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyComplex;
use pyo3::types::{PyByteArray, PyBytes, PyDict, PyFrozenSet, PyIterator, PyList, PySet, PyString, PyTuple};

use pyo3::IntoPyObjectExt;
use serde::ser::{Error, Serialize, SerializeMap, SerializeSeq, Serializer};

use crate::input::{EitherTimedelta, Int};
use crate::serializers::errors::unwrap_ser_error;
use crate::serializers::shared::serialize_to_json;
use crate::serializers::shared::serialize_to_python;
use crate::serializers::shared::DoSerialize;
use crate::serializers::type_serializers;
use crate::serializers::type_serializers::format::serialize_via_str;
use crate::serializers::SerializationState;
use crate::tools::{py_err, safe_repr};

use super::config::InfNanMode;
use super::errors::SERIALIZATION_ERR_MARKER;
use super::errors::{py_err_se_err, PydanticSerializationError};
use super::extra::SerMode;
use super::filter::{AnyFilter, SchemaFilter};
use super::ob_type::ObType;
use super::shared::any_dataclass_iter;
use super::SchemaSerializer;

pub(crate) fn infer_to_python<'py>(
    value: &Bound<'py, PyAny>,
    state: &mut SerializationState<'_, 'py>,
) -> PyResult<Py<PyAny>> {
    infer_to_python_known(state.extra.ob_type_lookup.get_type(value), value, state)
}

// arbitrary ids to identify that we recursed through infer_to_{python,json}_known
// We just need them to be different from definition ref slot ids, which start at 0
const INFER_DEF_REF_ID: usize = usize::MAX;

pub(crate) fn infer_to_python_known<'py>(
    ob_type: ObType,
    value: &Bound<'py, PyAny>,
    state: &mut SerializationState<'_, 'py>,
) -> PyResult<Py<PyAny>> {
    let py = value.py();

    let mode = state.extra.mode;
    let mut guard = match state.recursion_guard(value, INFER_DEF_REF_ID) {
        Ok(v) => v,
        Err(e) => {
            return match mode {
                SerMode::Json => Err(e),
                // if recursion is detected by we're serializing to python, we just return the value
                _ => Ok(value.clone().unbind()),
            };
        }
    };
    let state = guard.state();

    macro_rules! serialize_seq {
        ($t:ty) => {{
            let state = &mut state.scoped_include_exclude(None, None);
            value
                .cast::<$t>()?
                .iter()
                .map(|v| infer_to_python(&v, state))
                .collect::<PyResult<Vec<Py<PyAny>>>>()?
        }};
    }

    macro_rules! serialize_seq_filter {
        ($t:ty) => {{
            let py_seq = value.cast::<$t>()?;
            let mut items = Vec::with_capacity(py_seq.len());
            let filter = AnyFilter::new();
            let len = value.len().ok();

            for (index, element) in py_seq.iter().enumerate() {
                let op_next = filter.index_filter(index, state, len)?;
                if let Some((next_include, next_exclude)) = op_next {
                    let state = &mut state.scoped_include_exclude(next_include, next_exclude);
                    items.push(infer_to_python(&element, state)?);
                }
            }
            items
        }};
    }

    let value = match state.extra.mode {
        SerMode::Json => match ob_type {
            // `bool` and `None` can't be subclasses, `ObType::Int`, `ObType::Float`, `ObType::Str` refer to exact types
            ObType::None | ObType::Bool | ObType::Int | ObType::Str => value.clone().unbind(),
            // have to do this to make sure subclasses of for example str are upcast to `str`
            ObType::IntSubclass => {
                if let Ok(i) = value.extract::<Int>() {
                    i.into_py_any(py)?
                } else {
                    return py_err!(PyTypeError; "Expected int, got {}", safe_repr(value));
                }
            }
            ObType::Float | ObType::FloatSubclass => {
                let v = value.extract::<f64>()?;
                if (v.is_nan() || v.is_infinite()) && state.config.inf_nan_mode == InfNanMode::Null {
                    return Ok(py.None());
                }
                v.into_py_any(py)?
            }
            ObType::Decimal => value.to_string().into_py_any(py)?,
            ObType::StrSubclass => PyString::new(py, value.cast::<PyString>()?.to_str()?).into(),
            ObType::Bytes => state
                .config
                .bytes_mode
                .bytes_to_string(py, value.cast::<PyBytes>()?.as_bytes())?
                .into_py_any(py)?,
            ObType::Bytearray => {
                let py_byte_array = value.cast::<PyByteArray>()?;
                pyo3::sync::with_critical_section(py_byte_array, || {
                    // SAFETY: `py_byte_array` is protected by a critical section,
                    // which guarantees no mutation, and `bytes_to_string` does not
                    // run any code which could cause the critical section to be
                    // released.
                    let bytes = unsafe { py_byte_array.as_bytes() };
                    state.config.bytes_mode.bytes_to_string(py, bytes)?.into_py_any(py)
                })?
            }
            ObType::Tuple => {
                let elements = serialize_seq_filter!(PyTuple);
                PyList::new(py, elements)?.into()
            }
            ObType::List => {
                let elements = serialize_seq_filter!(PyList);
                PyList::new(py, elements)?.into()
            }
            ObType::Set => {
                let elements = serialize_seq!(PySet);
                PyList::new(py, elements)?.into()
            }
            ObType::Frozenset => {
                let elements = serialize_seq!(PyFrozenSet);
                PyList::new(py, elements)?.into()
            }
            ObType::Dict => {
                let dict = value.cast::<PyDict>()?;
                serialize_pairs_python(py, dict.iter().map(Ok), state, |k, state| {
                    Ok(PyString::new(py, &infer_json_key(&k, state)?).into_any())
                })?
            }
            ObType::Datetime => {
                let datetime = state.config.temporal_mode.datetime_to_json(value.py(), value.cast()?)?;
                datetime.into_py_any(py)?
            }
            ObType::Date => {
                let date = state.config.temporal_mode.date_to_json(value.py(), value.cast()?)?;
                date.into_py_any(py)?
            }
            ObType::Time => {
                let time = state.config.temporal_mode.time_to_json(value.py(), value.cast()?)?;
                time.into_py_any(py)?
            }
            ObType::Timedelta => {
                let either_delta = EitherTimedelta::try_from(value)?;
                state.config.temporal_mode.timedelta_to_json(value.py(), either_delta)?
            }
            ObType::Url
            | ObType::MultiHostUrl
            | ObType::Path
            | ObType::Ipv4Address
            | ObType::Ipv6Address
            | ObType::Ipv4Network
            | ObType::Ipv6Network => serialize_via_str(value, serialize_to_python())?,
            ObType::Uuid => {
                let uuid = super::type_serializers::uuid::uuid_to_string(value)?;
                uuid.into_py_any(py)?
            }
            ObType::PydanticSerializable => call_pydantic_serializer(value, state, serialize_to_python())?,
            ObType::Dataclass => serialize_pairs_python(py, any_dataclass_iter(value)?.0, state, |k, state| {
                Ok(PyString::new(py, &infer_json_key(&k, state)?).into_any())
            })?,
            ObType::Enum => {
                let v = value.getattr(intern!(py, "value"))?;
                infer_to_python(&v, state)?
            }
            ObType::Generator => {
                let py_seq = value.cast::<PyIterator>()?;
                let mut items = Vec::new();
                let filter = AnyFilter::new();

                for (index, r) in py_seq.try_iter()?.enumerate() {
                    let element = r?;
                    let op_next = filter.index_filter(index, state, None)?;
                    if let Some((next_include, next_exclude)) = op_next {
                        let state = &mut state.scoped_include_exclude(next_include, next_exclude);
                        items.push(infer_to_python(&element, state)?);
                    }
                }
                PyList::new(py, items)?.into()
            }
            ObType::Complex => {
                let v = value.cast::<PyComplex>()?;
                let complex_str = type_serializers::complex::complex_to_str(v);
                complex_str.into_py_any(py)?
            }
            ObType::Pattern => serialize_pattern(value, serialize_to_python())?,
            ObType::Unknown => {
                if let Some(fallback) = state.extra.fallback {
                    let next_value = fallback.call1((value,))?;
                    let next_result = infer_to_python(&next_value, state);
                    return next_result;
                } else if state.extra.serialize_unknown {
                    serialize_unknown(value).into_py_any(py)?
                } else {
                    return Err(unknown_type_error(value));
                }
            }
        },
        _ => match ob_type {
            ObType::Tuple => {
                let elements = serialize_seq_filter!(PyTuple);
                PyTuple::new(py, elements)?.into()
            }
            ObType::List => {
                let elements = serialize_seq_filter!(PyList);
                PyList::new(py, elements)?.into()
            }
            ObType::Set => {
                let elements = serialize_seq!(PySet);
                PySet::new(py, &elements)?.into()
            }
            ObType::Frozenset => {
                let elements = serialize_seq!(PyFrozenSet);
                PyFrozenSet::new(py, &elements)?.into()
            }
            ObType::Dict => {
                let dict = value.cast::<PyDict>()?;
                serialize_pairs_python(py, dict.iter().map(Ok), state, |k, _| Ok(k))?
            }
            ObType::PydanticSerializable => call_pydantic_serializer(value, state, serialize_to_python())?,
            ObType::Dataclass => serialize_pairs_python(py, any_dataclass_iter(value)?.0, state, |k, _| Ok(k))?,
            ObType::Generator => {
                let iter = super::type_serializers::generator::SerializationIterator::new(
                    value.cast()?,
                    super::type_serializers::any::AnySerializer::get(),
                    SchemaFilter::default(),
                    state,
                );
                iter.into_py_any(py)?
            }
            ObType::Complex => {
                let v = value.cast::<PyComplex>()?;
                v.into_py_any(py)?
            }
            ObType::Unknown => {
                if let Some(fallback) = state.extra.fallback {
                    let next_value = fallback.call1((value,))?;
                    let next_result = infer_to_python(&next_value, state);
                    return next_result;
                }
                value.clone().unbind()
            }
            _ => value.clone().unbind(),
        },
    };
    Ok(value)
}

pub(crate) struct SerializeInfer<'slf, 'a, 'py> {
    value: &'slf Bound<'py, PyAny>,
    state: RefCell<&'slf mut SerializationState<'a, 'py>>,
}

impl<'slf, 'a, 'py> SerializeInfer<'slf, 'a, 'py> {
    pub(crate) fn new(value: &'slf Bound<'py, PyAny>, state: &'slf mut SerializationState<'a, 'py>) -> Self {
        Self {
            value,
            state: RefCell::new(state),
        }
    }
}

impl Serialize for SerializeInfer<'_, '_, '_> {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        let state = &mut self.state.borrow_mut();
        let ob_type = state.extra.ob_type_lookup.get_type(self.value);
        infer_serialize_known(ob_type, self.value, serializer, state)
    }
}

pub(crate) fn infer_serialize<'py, S: Serializer>(
    value: &Bound<'py, PyAny>,
    serializer: S,
    state: &mut SerializationState<'_, 'py>,
) -> Result<S::Ok, S::Error> {
    infer_serialize_known(state.extra.ob_type_lookup.get_type(value), value, serializer, state)
}

pub(crate) fn infer_serialize_known<'py, S: Serializer>(
    ob_type: ObType,
    value: &Bound<'py, PyAny>,
    serializer: S,
    state: &mut SerializationState<'_, 'py>,
) -> Result<S::Ok, S::Error> {
    let extra_serialize_unknown = state.extra.serialize_unknown;
    let mut guard = match state.recursion_guard(value, INFER_DEF_REF_ID) {
        Ok(v) => v,
        Err(e) => {
            return if extra_serialize_unknown {
                serializer.serialize_str("...")
            } else {
                Err(py_err_se_err(e))
            };
        }
    };
    let state = guard.state();

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
            let state = &mut state.scoped_include_exclude(None, None);
            let py_seq = value.cast::<$t>().map_err(py_err_se_err)?;
            let mut seq = serializer.serialize_seq(Some(py_seq.len()))?;
            for element in py_seq.iter() {
                let item_serializer = SerializeInfer::new(&element, state);
                seq.serialize_element(&item_serializer)?
            }
            seq.end()
        }};
    }

    macro_rules! serialize_seq_filter {
        ($t:ty) => {{
            let py_seq = value.cast::<$t>().map_err(py_err_se_err)?;
            let mut seq = serializer.serialize_seq(Some(py_seq.len()))?;
            let filter = AnyFilter::new();
            let len = value.len().ok();

            for (index, element) in py_seq.iter().enumerate() {
                let op_next = filter.index_filter(index, state, len).map_err(py_err_se_err)?;
                if let Some((next_include, next_exclude)) = op_next {
                    let state = &mut state.scoped_include_exclude(next_include, next_exclude);
                    let item_serializer = SerializeInfer::new(&element, state);
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
            let v = value.cast::<PyComplex>().map_err(py_err_se_err)?;
            let complex_str = type_serializers::complex::complex_to_str(v);
            Ok(serializer.collect_str::<String>(&complex_str)?)
        }
        ObType::Float | ObType::FloatSubclass => {
            let v = value.extract::<f64>().map_err(py_err_se_err)?;
            type_serializers::float::serialize_f64(v, serializer, state.config.inf_nan_mode)
        }
        ObType::Decimal => value.to_string().serialize(serializer),
        ObType::Str | ObType::StrSubclass => {
            let py_str = value.cast::<PyString>().map_err(py_err_se_err)?;
            serialize_to_json(serializer)
                .serialize_str(py_str)
                .map_err(unwrap_ser_error)
        }
        ObType::Bytes => {
            let py_bytes = value.cast::<PyBytes>().map_err(py_err_se_err)?;
            state.config.bytes_mode.serialize_bytes(py_bytes.as_bytes(), serializer)
        }
        ObType::Bytearray => {
            let py_byte_array = value.cast::<PyByteArray>().map_err(py_err_se_err)?;
            pyo3::sync::with_critical_section(py_byte_array, || {
                // SAFETY: `py_byte_array` is protected by a critical section,
                // which guarantees no mutation, and `serialize_bytes` does not
                // run any code which could cause the critical section to be
                // released.
                let bytes = unsafe { py_byte_array.as_bytes() };
                state.config.bytes_mode.serialize_bytes(bytes, serializer)
            })
        }
        ObType::Dict => {
            let dict = value.cast::<PyDict>().map_err(py_err_se_err)?;
            serialize_pairs_json(dict.iter().map(Ok), dict.len(), serializer, state)
        }
        ObType::List => serialize_seq_filter!(PyList),
        ObType::Tuple => serialize_seq_filter!(PyTuple),
        ObType::Set => serialize_seq!(PySet),
        ObType::Frozenset => serialize_seq!(PyFrozenSet),
        ObType::Datetime => {
            let py_datetime = value.cast().map_err(py_err_se_err)?;
            state.config.temporal_mode.datetime_serialize(py_datetime, serializer)
        }
        ObType::Date => {
            let py_date = value.cast().map_err(py_err_se_err)?;
            state.config.temporal_mode.date_serialize(py_date, serializer)
        }
        ObType::Time => {
            let py_time = value.cast().map_err(py_err_se_err)?;
            state.config.temporal_mode.time_serialize(py_time, serializer)
        }
        ObType::Timedelta => {
            let either_delta = EitherTimedelta::try_from(value).map_err(py_err_se_err)?;
            state.config.temporal_mode.timedelta_serialize(either_delta, serializer)
        }
        ObType::Url
        | ObType::MultiHostUrl
        | ObType::Path
        | ObType::Ipv4Address
        | ObType::Ipv6Address
        | ObType::Ipv4Network
        | ObType::Ipv6Network => serialize_via_str(value, serialize_to_json(serializer)).map_err(unwrap_ser_error),
        ObType::PydanticSerializable => {
            call_pydantic_serializer(value, state, serialize_to_json(serializer)).map_err(unwrap_ser_error)
        }
        ObType::Dataclass => {
            let (pairs_iter, fields_dict) = any_dataclass_iter(value).map_err(py_err_se_err)?;
            serialize_pairs_json(pairs_iter, fields_dict.len(), serializer, state)
        }
        ObType::Uuid => {
            let uuid = super::type_serializers::uuid::uuid_to_string(value).map_err(py_err_se_err)?;
            serializer.serialize_str(&uuid)
        }
        ObType::Enum => {
            let v = value.getattr(intern!(value.py(), "value")).map_err(py_err_se_err)?;
            infer_serialize(&v, serializer, state)
        }
        ObType::Generator => {
            let py_seq = value.cast::<PyIterator>().map_err(py_err_se_err)?;
            let mut seq = serializer.serialize_seq(None)?;
            let filter = AnyFilter::new();
            for (index, r) in py_seq.try_iter().map_err(py_err_se_err)?.enumerate() {
                let element = r.map_err(py_err_se_err)?;
                let op_next = filter.index_filter(index, state, None).map_err(py_err_se_err)?;
                if let Some((next_include, next_exclude)) = op_next {
                    let state = &mut state.scoped_include_exclude(next_include, next_exclude);
                    let item_serializer = SerializeInfer::new(&element, state);
                    seq.serialize_element(&item_serializer)?;
                }
            }
            seq.end()
        }
        ObType::Pattern => serialize_pattern(value, serialize_to_json(serializer)).map_err(unwrap_ser_error),
        ObType::Unknown => {
            if let Some(fallback) = state.extra.fallback {
                let next_value = fallback.call1((value,)).map_err(py_err_se_err)?;
                let next_result = infer_serialize(&next_value, serializer, state);
                return next_result;
            } else if state.extra.serialize_unknown {
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

fn serialize_pattern<'py, T, E: From<PyErr>>(
    value: &Bound<'py, PyAny>,
    do_serialize: impl DoSerialize<'py, T, E>,
) -> Result<T, E> {
    let pattern = value.getattr(intern!(value.py(), "pattern"))?;
    serialize_via_str(&pattern, do_serialize)
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

pub(crate) fn infer_json_key<'a, 'py>(
    key: &'a Bound<'py, PyAny>,
    state: &mut SerializationState<'_, 'py>,
) -> PyResult<Cow<'a, str>> {
    let ob_type = state.extra.ob_type_lookup.get_type(key);
    infer_json_key_known(ob_type, key, state)
}

pub(crate) fn infer_json_key_known<'a, 'py>(
    ob_type: ObType,
    key: &'a Bound<'py, PyAny>,
    state: &mut SerializationState<'_, 'py>,
) -> PyResult<Cow<'a, str>> {
    match ob_type {
        ObType::None => super::type_serializers::simple::none_json_key(),
        ObType::Int | ObType::IntSubclass => super::type_serializers::simple::to_str_json_key(key),
        ObType::Float | ObType::FloatSubclass => {
            let v = key.extract::<f64>()?;
            if (v.is_nan() || v.is_infinite()) && state.config.inf_nan_mode == InfNanMode::Null {
                super::type_serializers::simple::none_json_key()
            } else {
                super::type_serializers::simple::to_str_json_key(key)
            }
        }
        ObType::Decimal => Ok(Cow::Owned(key.to_string())),
        ObType::Bool => super::type_serializers::simple::bool_json_key(key),
        ObType::Str | ObType::StrSubclass => key.cast::<PyString>()?.to_cow(),
        ObType::Bytes => state
            .config
            .bytes_mode
            .bytes_to_string(key.py(), key.cast::<PyBytes>()?.as_bytes()),
        ObType::Bytearray => {
            let py_byte_array = key.cast::<PyByteArray>()?;
            pyo3::sync::with_critical_section(py_byte_array, || {
                // SAFETY: `py_byte_array` is protected by a critical section,
                // which guarantees no mutation, and `bytes_to_string` does not
                // run any code which could cause the critical section to be
                // released.
                let bytes = unsafe { py_byte_array.as_bytes() };
                state.config.bytes_mode.bytes_to_string(key.py(), bytes)
            })
            .map(|cow| Cow::Owned(cow.into_owned()))
        }
        ObType::Datetime => state.config.temporal_mode.datetime_json_key(key.cast()?),
        ObType::Date => state.config.temporal_mode.date_json_key(key.cast()?),
        ObType::Time => state.config.temporal_mode.time_json_key(key.cast()?),
        ObType::Uuid => {
            let uuid = super::type_serializers::uuid::uuid_to_string(key)?;
            Ok(Cow::Owned(uuid))
        }
        ObType::Timedelta => {
            let either_delta = EitherTimedelta::try_from(key)?;
            state.config.temporal_mode.timedelta_json_key(&either_delta)
        }
        ObType::Url
        | ObType::MultiHostUrl
        | ObType::Path
        | ObType::Ipv4Address
        | ObType::Ipv6Address
        | ObType::Ipv4Network
        | ObType::Ipv6Network => {
            // FIXME it would be nice to have a "PyCow" which carries ownership of the Python type too
            Ok(Cow::Owned(key.str()?.to_string_lossy().into_owned()))
        }
        ObType::Tuple => {
            let mut key_build = super::type_serializers::tuple::KeyBuilder::new();
            for element in key.cast::<PyTuple>()?.iter_borrowed() {
                key_build.push(&infer_json_key(&element, state)?);
            }
            Ok(Cow::Owned(key_build.finish()))
        }
        ObType::List | ObType::Set | ObType::Frozenset | ObType::Dict | ObType::Generator => {
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
            infer_json_key(&k, state).map(|cow| Cow::Owned(cow.into_owned()))
        }
        ObType::Complex => {
            let v = key.cast::<PyComplex>()?;
            Ok(type_serializers::complex::complex_to_str(v).into())
        }
        ObType::Pattern => Ok(Cow::Owned(
            key.getattr(intern!(key.py(), "pattern"))?
                .str()?
                .to_string_lossy()
                .into_owned(),
        )),
        ObType::Unknown => {
            if let Some(fallback) = state.extra.fallback {
                let next_key = fallback.call1((key,))?;
                infer_json_key(&next_key, state).map(|cow| Cow::Owned(cow.into_owned()))
            } else if state.extra.serialize_unknown {
                Ok(serialize_unknown(key))
            } else {
                Err(unknown_type_error(key))
            }
        }
    }
}

/// Serialize `value` as if it had a `__pydantic_serializer__` attribute
///
/// `do_serialize` should be a closure which performs serialization without type inference
pub(crate) fn call_pydantic_serializer<'py, T, E: From<PyErr>>(
    value: &Bound<'py, PyAny>,
    state: &mut SerializationState<'_, 'py>,
    do_serialize: impl DoSerialize<'py, T, E>,
) -> Result<T, E> {
    let py = value.py();
    let py_serializer = value.getattr(intern!(py, "__pydantic_serializer__"))?;
    let extracted_serializer: PyRef<SchemaSerializer> = py_serializer.extract().map_err(Into::into)?;
    let mut state = SerializationState {
        warnings: state.warnings.clone(),
        rec_guard: state.rec_guard.clone(),
        config: extracted_serializer.config,
        model: state.model.clone(),
        field_name: state.field_name.clone(),
        include_exclude: state.include_exclude.clone(),
        check: state.check,
        extra: state.extra.clone(),
    };

    // Avoid falling immediately back into inference because we need to use the serializer
    // to drive the next step of serialization
    do_serialize.serialize_no_infer(&extracted_serializer.serializer, value, &mut state)
}

fn serialize_pairs_python<'py>(
    py: Python,
    pairs_iter: impl Iterator<Item = PyResult<(Bound<'py, PyAny>, Bound<'py, PyAny>)>>,
    state: &mut SerializationState<'_, 'py>,
    key_transform: impl Fn(Bound<'py, PyAny>, &mut SerializationState<'_, 'py>) -> PyResult<Bound<'py, PyAny>>,
) -> PyResult<Py<PyAny>> {
    let new_dict = PyDict::new(py);
    let filter = AnyFilter::new();

    for result in pairs_iter {
        let (k, v) = result?;
        let op_next = filter.key_filter(&k, state)?;
        if let Some((next_include, next_exclude)) = op_next {
            let state = &mut state.scoped_include_exclude(next_include, next_exclude);
            let k = key_transform(k, state)?;
            let v = infer_to_python(&v, state)?;
            new_dict.set_item(k, v)?;
        }
    }
    Ok(new_dict.into())
}

fn serialize_pairs_json<'py, S: Serializer>(
    pairs_iter: impl Iterator<Item = PyResult<(Bound<'py, PyAny>, Bound<'py, PyAny>)>>,
    iter_size: usize,
    serializer: S,
    state: &mut SerializationState<'_, 'py>,
) -> Result<S::Ok, S::Error> {
    let mut map = serializer.serialize_map(Some(iter_size))?;
    let filter = AnyFilter::new();

    for result in pairs_iter {
        let (key, value) = result.map_err(py_err_se_err)?;

        let op_next = filter.key_filter(&key, state).map_err(py_err_se_err)?;
        if let Some((next_include, next_exclude)) = op_next {
            let state = &mut state.scoped_include_exclude(next_include, next_exclude);
            let key = infer_json_key(&key, state).map_err(py_err_se_err)?;
            let value_serializer = SerializeInfer::new(&value, state);
            map.serialize_entry(&key, &value_serializer)?;
        }
    }
    map.end()
}
