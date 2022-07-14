use std::str::from_utf8;

use pyo3::exceptions::{PyAttributeError, PyTypeError};
use pyo3::prelude::*;
use pyo3::types::{
    PyBool, PyByteArray, PyBytes, PyDate, PyDateTime, PyDelta, PyDict, PyFrozenSet, PyInt, PyList, PyMapping,
    PySequence, PySet, PyString, PyTime, PyTuple, PyType,
};
use pyo3::{intern, AsPyPointer};

use crate::errors::{py_err_string, ErrorKind, InputValue, LocItem, ValError, ValResult};

use super::datetime::{
    bytes_as_date, bytes_as_datetime, bytes_as_time, bytes_as_timedelta, date_as_datetime, float_as_datetime,
    float_as_duration, float_as_time, int_as_datetime, int_as_duration, int_as_time, EitherDate, EitherDateTime,
    EitherTime,
};
use super::shared::{float_as_int, int_as_bool, str_as_bool, str_as_int};
use super::{repr_string, EitherBytes, EitherString, EitherTimedelta, GenericMapping, GenericSequence, Input};

impl<'a> Input<'a> for PyAny {
    fn as_loc_item(&'a self) -> LocItem {
        if let Ok(key_str) = self.extract::<String>() {
            key_str.into()
        } else if let Ok(key_int) = self.extract::<usize>() {
            key_int.into()
        } else {
            match repr_string(self) {
                Ok(s) => s.into(),
                Err(_) => format!("{:?}", self).into(),
            }
        }
    }

    fn as_error_value(&'a self) -> InputValue<'a> {
        InputValue::PyAny(self)
    }

    fn identity(&'a self) -> Option<usize> {
        Some(self.as_ptr() as usize)
    }

    fn is_none(&self) -> bool {
        self.is_none()
    }

    fn strict_str<'data>(&'data self) -> ValResult<EitherString<'data>> {
        if let Ok(py_str) = self.cast_as::<PyString>() {
            Ok(py_str.into())
        } else {
            Err(ValError::new(ErrorKind::StrType, self))
        }
    }

    fn lax_str<'data>(&'data self) -> ValResult<EitherString<'data>> {
        if let Ok(py_str) = self.cast_as::<PyString>() {
            Ok(py_str.into())
        } else if let Ok(bytes) = self.cast_as::<PyBytes>() {
            let str = match from_utf8(bytes.as_bytes()) {
                Ok(s) => s,
                Err(_) => return Err(ValError::new(ErrorKind::StrUnicode, self)),
            };
            Ok(str.into())
        } else if let Ok(py_byte_array) = self.cast_as::<PyByteArray>() {
            let str = match from_utf8(unsafe { py_byte_array.as_bytes() }) {
                Ok(s) => s,
                Err(_) => return Err(ValError::new(ErrorKind::StrUnicode, self)),
            };
            Ok(str.into())
        } else if self.cast_as::<PyBool>().is_ok() {
            // do this before int and float parsing as `False` is cast to `0` and we don't want False to
            // be returned as a string
            Err(ValError::new(ErrorKind::StrType, self))
        } else if let Ok(int) = self.cast_as::<PyInt>() {
            let int = i64::extract(int).map_err(Into::<ValError>::into)?;
            Ok(int.to_string().into())
        } else if let Ok(float) = f64::extract(self) {
            // don't cast_as here so Decimals are covered - internally f64:extract uses PyFloat_AsDouble
            Ok(float.to_string().into())
        } else {
            Err(ValError::new(ErrorKind::StrType, self))
        }
    }

    fn strict_bool(&self) -> ValResult<bool> {
        if let Ok(bool) = self.extract::<bool>() {
            Ok(bool)
        } else {
            Err(ValError::new(ErrorKind::BoolType, self))
        }
    }

    fn lax_bool(&self) -> ValResult<bool> {
        if let Ok(bool) = self.extract::<bool>() {
            Ok(bool)
        } else if let Some(either_str) = maybe_as_string(self, ErrorKind::BoolParsing)? {
            str_as_bool(self, &either_str.as_cow())
        } else if let Ok(int) = self.extract::<i64>() {
            int_as_bool(self, int)
        } else if let Ok(float) = self.extract::<f64>() {
            match float_as_int(self, float) {
                Ok(int) => int_as_bool(self, int),
                _ => Err(ValError::new(ErrorKind::BoolType, self)),
            }
        } else {
            Err(ValError::new(ErrorKind::BoolType, self))
        }
    }

    fn strict_int(&self) -> ValResult<i64> {
        // bool check has to come before int check as bools would be cast to ints below
        if self.extract::<bool>().is_ok() {
            Err(ValError::new(ErrorKind::IntType, self))
        } else if let Ok(int) = self.extract::<i64>() {
            Ok(int)
        } else {
            Err(ValError::new(ErrorKind::IntType, self))
        }
    }

    fn lax_int(&self) -> ValResult<i64> {
        if let Ok(int) = self.extract::<i64>() {
            Ok(int)
        } else if let Some(either_str) = maybe_as_string(self, ErrorKind::IntParsing)? {
            str_as_int(self, &either_str.as_cow())
        } else if let Ok(float) = self.lax_float() {
            float_as_int(self, float)
        } else {
            Err(ValError::new(ErrorKind::IntType, self))
        }
    }

    fn strict_float(&self) -> ValResult<f64> {
        if self.extract::<bool>().is_ok() {
            Err(ValError::new(ErrorKind::FloatType, self))
        } else if let Ok(float) = self.extract::<f64>() {
            Ok(float)
        } else {
            Err(ValError::new(ErrorKind::FloatType, self))
        }
    }

    fn lax_float(&self) -> ValResult<f64> {
        if let Ok(float) = self.extract::<f64>() {
            Ok(float)
        } else if let Some(either_str) = maybe_as_string(self, ErrorKind::FloatParsing)? {
            match either_str.as_cow().as_ref().parse() {
                Ok(i) => Ok(i),
                Err(_) => Err(ValError::new(ErrorKind::FloatParsing, self)),
            }
        } else {
            Err(ValError::new(ErrorKind::FloatType, self))
        }
    }

    fn strict_model_check(&self, class: &PyType) -> ValResult<bool> {
        self.get_type().eq(class).map_err(Into::<ValError>::into)
    }

    fn strict_dict<'data>(&'data self) -> ValResult<GenericMapping<'data>> {
        if let Ok(dict) = self.cast_as::<PyDict>() {
            Ok(dict.into())
        } else {
            Err(ValError::new(ErrorKind::DictType, self))
        }
    }

    fn lax_dict<'data>(&'data self) -> ValResult<GenericMapping<'data>> {
        if let Ok(dict) = self.cast_as::<PyDict>() {
            Ok(dict.into())
        } else if let Some(generic_mapping) = mapping_as_dict(self) {
            generic_mapping
        } else {
            Err(ValError::new(ErrorKind::DictType, self))
        }
    }

    fn typed_dict<'data>(&'data self, from_attributes: bool, from_mapping: bool) -> ValResult<GenericMapping<'data>> {
        if from_attributes {
            // if from_attributes, first try a dict, then mapping then from_attributes
            if let Ok(dict) = self.cast_as::<PyDict>() {
                return Ok(dict.into());
            } else if from_mapping {
                // we can't do this in one set of if/else because we need to check from_mapping before doing this
                if let Some(generic_mapping) = mapping_as_dict(self) {
                    return generic_mapping;
                }
            }

            if from_attributes_applicable(self) {
                Ok(self.into())
            } else {
                // note the error here gives a hint about from_attributes
                Err(ValError::new(ErrorKind::DictAttributesType, self))
            }
        } else if from_mapping {
            // otherwise we just call back to lax_dict if from_mapping is allowed, not there error in this
            // case (correctly) won't hint about from_attributes
            self.lax_dict()
        } else {
            self.strict_dict()
        }
    }

    fn strict_list<'data>(&'data self) -> ValResult<GenericSequence<'data>> {
        if let Ok(list) = self.cast_as::<PyList>() {
            Ok(list.into())
        } else {
            Err(ValError::new(ErrorKind::ListType, self))
        }
    }

    fn lax_list<'data>(&'data self) -> ValResult<GenericSequence<'data>> {
        if let Ok(list) = self.cast_as::<PyList>() {
            Ok(list.into())
        } else if let Ok(tuple) = self.cast_as::<PyTuple>() {
            Ok(tuple.into())
        } else if let Ok(set) = self.cast_as::<PySet>() {
            Ok(set.into())
        } else if let Ok(frozen_set) = self.cast_as::<PyFrozenSet>() {
            Ok(frozen_set.into())
        } else {
            Err(ValError::new(ErrorKind::ListType, self))
        }
    }

    fn strict_set<'data>(&'data self) -> ValResult<GenericSequence<'data>> {
        if let Ok(set) = self.cast_as::<PySet>() {
            Ok(set.into())
        } else {
            Err(ValError::new(ErrorKind::SetType, self))
        }
    }

    fn lax_set<'data>(&'data self) -> ValResult<GenericSequence<'data>> {
        if let Ok(set) = self.cast_as::<PySet>() {
            Ok(set.into())
        } else if let Ok(list) = self.cast_as::<PyList>() {
            Ok(list.into())
        } else if let Ok(tuple) = self.cast_as::<PyTuple>() {
            Ok(tuple.into())
        } else if let Ok(frozen_set) = self.cast_as::<PyFrozenSet>() {
            Ok(frozen_set.into())
        } else {
            Err(ValError::new(ErrorKind::SetType, self))
        }
    }

    fn strict_frozenset<'data>(&'data self) -> ValResult<GenericSequence<'data>> {
        if let Ok(set) = self.cast_as::<PyFrozenSet>() {
            Ok(set.into())
        } else {
            Err(ValError::new(ErrorKind::FrozenSetType, self))
        }
    }

    fn lax_frozenset<'data>(&'data self) -> ValResult<GenericSequence<'data>> {
        if let Ok(frozen_set) = self.cast_as::<PyFrozenSet>() {
            Ok(frozen_set.into())
        } else if let Ok(set) = self.cast_as::<PySet>() {
            Ok(set.into())
        } else if let Ok(list) = self.cast_as::<PyList>() {
            Ok(list.into())
        } else if let Ok(tuple) = self.cast_as::<PyTuple>() {
            Ok(tuple.into())
        } else {
            Err(ValError::new(ErrorKind::FrozenSetType, self))
        }
    }

    fn strict_bytes<'data>(&'data self) -> ValResult<EitherBytes<'data>> {
        if let Ok(py_bytes) = self.cast_as::<PyBytes>() {
            Ok(py_bytes.into())
        } else {
            Err(ValError::new(ErrorKind::BytesType, self))
        }
    }

    fn lax_bytes<'data>(&'data self) -> ValResult<EitherBytes<'data>> {
        if let Ok(py_bytes) = self.cast_as::<PyBytes>() {
            Ok(py_bytes.into())
        } else if let Ok(py_str) = self.cast_as::<PyString>() {
            let string = py_str.to_string_lossy().to_string();
            Ok(string.into_bytes().into())
        } else if let Ok(py_byte_array) = self.cast_as::<PyByteArray>() {
            Ok(py_byte_array.to_vec().into())
        } else {
            Err(ValError::new(ErrorKind::BytesType, self))
        }
    }

    fn strict_date(&self) -> ValResult<EitherDate> {
        if self.cast_as::<PyDateTime>().is_ok() {
            // have to check if it's a datetime first, otherwise the line below converts to a date
            Err(ValError::new(ErrorKind::DateType, self))
        } else if let Ok(date) = self.cast_as::<PyDate>() {
            Ok(date.into())
        } else {
            Err(ValError::new(ErrorKind::DateType, self))
        }
    }

    fn lax_date(&self) -> ValResult<EitherDate> {
        if self.cast_as::<PyDateTime>().is_ok() {
            // have to check if it's a datetime first, otherwise the line below converts to a date
            // even if we later try coercion from a datetime, we don't want to return a datetime now
            Err(ValError::new(ErrorKind::DateType, self))
        } else if let Ok(date) = self.cast_as::<PyDate>() {
            Ok(date.into())
        } else if let Ok(str) = self.extract::<String>() {
            bytes_as_date(self, str.as_bytes())
        } else if let Ok(py_bytes) = self.cast_as::<PyBytes>() {
            bytes_as_date(self, py_bytes.as_bytes())
        } else {
            Err(ValError::new(ErrorKind::DateType, self))
        }
    }

    fn strict_time(&self) -> ValResult<EitherTime> {
        if let Ok(time) = self.cast_as::<PyTime>() {
            Ok(time.into())
        } else {
            Err(ValError::new(ErrorKind::TimeType, self))
        }
    }

    fn lax_time(&self) -> ValResult<EitherTime> {
        if let Ok(time) = self.cast_as::<PyTime>() {
            Ok(time.into())
        } else if let Ok(str) = self.extract::<String>() {
            bytes_as_time(self, str.as_bytes())
        } else if let Ok(py_bytes) = self.cast_as::<PyBytes>() {
            bytes_as_time(self, py_bytes.as_bytes())
        } else if self.cast_as::<PyBool>().is_ok() {
            Err(ValError::new(ErrorKind::TimeType, self))
        } else if let Ok(int) = self.extract::<i64>() {
            int_as_time(self, int, 0)
        } else if let Ok(float) = self.extract::<f64>() {
            float_as_time(self, float)
        } else {
            Err(ValError::new(ErrorKind::TimeType, self))
        }
    }

    fn strict_datetime(&self) -> ValResult<EitherDateTime> {
        if let Ok(dt) = self.cast_as::<PyDateTime>() {
            Ok(dt.into())
        } else {
            Err(ValError::new(ErrorKind::DateTimeType, self))
        }
    }

    fn lax_datetime(&self) -> ValResult<EitherDateTime> {
        if let Ok(dt) = self.cast_as::<PyDateTime>() {
            Ok(dt.into())
        } else if let Ok(str) = self.extract::<String>() {
            bytes_as_datetime(self, str.as_bytes())
        } else if let Ok(py_bytes) = self.cast_as::<PyBytes>() {
            bytes_as_datetime(self, py_bytes.as_bytes())
        } else if self.cast_as::<PyBool>().is_ok() {
            Err(ValError::new(ErrorKind::DateTimeType, self))
        } else if let Ok(int) = self.extract::<i64>() {
            int_as_datetime(self, int, 0)
        } else if let Ok(float) = self.extract::<f64>() {
            float_as_datetime(self, float)
        } else if let Ok(date) = self.cast_as::<PyDate>() {
            date_as_datetime(date).map_err(Into::<ValError>::into)
        } else {
            Err(ValError::new(ErrorKind::DateTimeType, self))
        }
    }

    fn strict_tuple<'data>(&'data self) -> ValResult<GenericSequence<'data>> {
        if let Ok(tuple) = self.cast_as::<PyTuple>() {
            Ok(tuple.into())
        } else {
            Err(ValError::new(ErrorKind::TupleType, self))
        }
    }

    fn lax_tuple<'data>(&'data self) -> ValResult<GenericSequence<'data>> {
        if let Ok(tuple) = self.cast_as::<PyTuple>() {
            Ok(tuple.into())
        } else if let Ok(list) = self.cast_as::<PyList>() {
            Ok(list.into())
        } else if let Ok(set) = self.cast_as::<PySet>() {
            Ok(set.into())
        } else if let Ok(frozen_set) = self.cast_as::<PyFrozenSet>() {
            Ok(frozen_set.into())
        } else {
            Err(ValError::new(ErrorKind::TupleType, self))
        }
    }

    fn strict_timedelta(&self) -> ValResult<EitherTimedelta> {
        if let Ok(dt) = self.cast_as::<PyDelta>() {
            Ok(dt.into())
        } else {
            Err(ValError::new(ErrorKind::TimeDeltaType, self))
        }
    }

    fn lax_timedelta(&self) -> ValResult<EitherTimedelta> {
        if let Ok(dt) = self.cast_as::<PyDelta>() {
            Ok(dt.into())
        } else if let Ok(py_str) = self.cast_as::<PyString>() {
            bytes_as_timedelta(self, py_str.to_string_lossy().as_bytes())
        } else if let Ok(py_bytes) = self.cast_as::<PyBytes>() {
            bytes_as_timedelta(self, py_bytes.as_bytes())
        } else if let Ok(int) = self.extract::<i64>() {
            Ok(int_as_duration(int).into())
        } else if let Ok(float) = self.extract::<f64>() {
            Ok(float_as_duration(float).into())
        } else {
            Err(ValError::new(ErrorKind::TimeDeltaType, self))
        }
    }

    fn is_instance(&self, class: &PyType) -> PyResult<bool> {
        self.is_instance(class)
    }

    fn callable(&self) -> bool {
        self.is_callable()
    }
}

/// return None if obj is not a mapping (cast_as::<PyMapping> fails or mapping.items returns an AttributeError)
/// otherwise try to covert the mapping to a dict and return an Some(error) if it fails
fn mapping_as_dict(obj: &PyAny) -> Option<ValResult<GenericMapping>> {
    let mapping: &PyMapping = match obj.cast_as() {
        Ok(mapping) => mapping,
        Err(_) => return None,
    };
    // see https://github.com/PyO3/pyo3/issues/2072 - the cast_as::<PyMapping> is not entirely accurate
    // and returns some things which are definitely not mappings (e.g. str) as mapping,
    // hence we also require that the object as `items` to consider it a mapping
    let result_dict = match mapping.items() {
        Ok(seq) => mapping_seq_as_dict(seq),
        Err(err) => {
            if matches!(err.get_type(obj.py()).is_subclass_of::<PyAttributeError>(), Ok(true)) {
                return None;
            } else {
                Err(err)
            }
        }
    };
    match result_dict {
        Ok(dict) => Some(Ok(dict.into())),
        Err(err) => Some(Err(ValError::new(
            ErrorKind::DictFromMapping {
                error: py_err_string(obj.py(), err),
            },
            obj,
        ))),
    }
}

// creating a temporary dict is slow, we could perhaps use an indexmap instead
fn mapping_seq_as_dict(seq: &PySequence) -> PyResult<&PyDict> {
    let dict = PyDict::new(seq.py());
    for r in seq.iter()? {
        let t: &PyTuple = r?.extract()?;

        if t.len() != 2 {
            return Err(PyTypeError::new_err("mapping items must be a tuple with 2 elements"));
        }

        #[cfg(PyPy)]
        let k = t.get_item(0)?;
        #[cfg(PyPy)]
        let v = t.get_item(1)?;

        #[cfg(not(PyPy))]
        let k = unsafe { t.get_item_unchecked(0) };
        #[cfg(not(PyPy))]
        let v = unsafe { t.get_item_unchecked(1) };
        dict.set_item(k, v)?;
    }
    Ok(dict)
}

/// Best effort check of whether it's likely to make sense to inspect obj for attributes and iterate over it
/// with `obj.dir()`
fn from_attributes_applicable(obj: &PyAny) -> bool {
    let module_name = match obj.get_type().getattr(intern!(obj.py(), "__module__")) {
        Ok(module) => match module.extract::<&str>() {
            Ok(s) => s,
            Err(_) => return false,
        },
        Err(_) => return false,
    };
    // I don't think it's a very good list at all! But it doesn't have to be at perfect, it just needs to avoid
    // the most egregious foot guns, it's mostly just to catch "builtins"
    // still happy to add more or do something completely different if anyone has a better idea???
    // dbg!(obj, module_name);
    !matches!(module_name, "builtins" | "datetime" | "collections")
}

/// Utility for extracting a string from a PyAny, if possible.
fn maybe_as_string(v: &PyAny, unicode_error: ErrorKind) -> ValResult<Option<EitherString>> {
    if let Ok(py_string) = v.cast_as::<PyString>() {
        Ok(Some(py_string.into()))
    } else if let Ok(bytes) = v.cast_as::<PyBytes>() {
        match from_utf8(bytes.as_bytes()) {
            Ok(s) => Ok(Some(s.into())),
            Err(_) => Err(ValError::new(unicode_error, v)),
        }
    } else {
        Ok(None)
    }
}
