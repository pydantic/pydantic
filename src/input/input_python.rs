use pyo3::exceptions::PyAttributeError;
use std::str::from_utf8;

use pyo3::prelude::*;
use pyo3::types::{
    PyBool, PyBytes, PyDate, PyDateTime, PyDict, PyFrozenSet, PyInt, PyList, PyMapping, PySequence, PySet, PyString,
    PyTime, PyTuple, PyType,
};

use crate::errors::location::LocItem;
use crate::errors::{as_internal, context, err_val_error, ErrorKind, InputValue, ValResult};
use crate::input::return_enums::EitherString;

use super::datetime::{
    bytes_as_date, bytes_as_datetime, bytes_as_time, date_as_datetime, float_as_datetime, float_as_time,
    int_as_datetime, int_as_time, EitherDate, EitherDateTime, EitherTime,
};
use super::generics::{GenericMapping, GenericSequence};
use super::input_abstract::Input;
use super::repr_string;
use super::return_enums::EitherBytes;
use super::shared::{float_as_int, int_as_bool, str_as_bool, str_as_int};

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

    fn is_none(&self) -> bool {
        self.is_none()
    }

    fn strict_str<'data>(&'data self) -> ValResult<EitherString<'data>> {
        if let Ok(py_str) = self.cast_as::<PyString>() {
            Ok(py_str.into())
        } else {
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::StrType)
        }
    }

    fn lax_str<'data>(&'data self) -> ValResult<EitherString<'data>> {
        if let Ok(py_str) = self.cast_as::<PyString>() {
            Ok(py_str.into())
        } else if let Ok(bytes) = self.cast_as::<PyBytes>() {
            let str = match from_utf8(bytes.as_bytes()) {
                Ok(s) => s,
                Err(_) => return err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::StrUnicode),
            };
            Ok(str.into())
        } else if self.cast_as::<PyBool>().is_ok() {
            // do this before int and float parsing as `False` is cast to `0` and we don't want False to
            // be returned as a string
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::StrType)
        } else if let Ok(int) = self.cast_as::<PyInt>() {
            let int = i64::extract(int).map_err(as_internal)?;
            Ok(int.to_string().into())
        } else if let Ok(float) = f64::extract(self) {
            // don't cast_as here so Decimals are covered - internally f64:extract uses PyFloat_AsDouble
            Ok(float.to_string().into())
        } else {
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::StrType)
        }
    }

    fn strict_bool(&self) -> ValResult<bool> {
        if let Ok(bool) = self.extract::<bool>() {
            Ok(bool)
        } else {
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::BoolType)
        }
    }

    fn lax_bool(&self) -> ValResult<bool> {
        if let Ok(bool) = self.extract::<bool>() {
            Ok(bool)
        } else if let Some(either_str) = maybe_as_string(self, ErrorKind::BoolParsing)? {
            str_as_bool(self, &either_str.as_cow())
        } else if let Ok(int) = self.extract::<i64>() {
            int_as_bool(self, int)
        } else {
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::BoolType)
        }
    }

    fn strict_int(&self) -> ValResult<i64> {
        // bool check has to come before int check as bools would be cast to ints below
        if self.extract::<bool>().is_ok() {
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::IntType)
        } else if let Ok(int) = self.extract::<i64>() {
            Ok(int)
        } else {
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::IntType)
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
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::IntType)
        }
    }

    fn strict_float(&self) -> ValResult<f64> {
        if self.extract::<bool>().is_ok() {
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::FloatType)
        } else if let Ok(float) = self.extract::<f64>() {
            Ok(float)
        } else {
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::FloatType)
        }
    }

    fn lax_float(&self) -> ValResult<f64> {
        if let Ok(float) = self.extract::<f64>() {
            Ok(float)
        } else if let Some(either_str) = maybe_as_string(self, ErrorKind::FloatParsing)? {
            match either_str.as_cow().as_ref().parse() {
                Ok(i) => Ok(i),
                Err(_) => err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::FloatParsing),
            }
        } else {
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::FloatType)
        }
    }

    fn strict_model_check(&self, class: &PyType) -> ValResult<bool> {
        self.get_type().eq(class).map_err(as_internal)
    }

    fn strict_dict<'data>(&'data self) -> ValResult<GenericMapping<'data>> {
        if let Ok(dict) = self.cast_as::<PyDict>() {
            Ok(dict.into())
        } else {
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::DictType)
        }
    }

    fn lax_dict<'data>(&'data self, try_instance: bool) -> ValResult<GenericMapping<'data>> {
        if let Ok(dict) = self.cast_as::<PyDict>() {
            Ok(dict.into())
        } else if let Some(result_dict) = mapping_as_dict(self) {
            match result_dict {
                Ok(dict) => Ok(dict.into()),
                Err(err) => {
                    err_val_error!(
                        input_value = self.as_error_value(),
                        kind = ErrorKind::DictFromMapping,
                        context = context!("error" => err_string(self.py(), err)),
                    )
                }
            }
        } else if try_instance {
            let inner_dict = match instance_as_dict(self) {
                Ok(dict) => dict,
                Err(err) => {
                    return err_val_error!(
                        input_value = self.as_error_value(),
                        kind = ErrorKind::DictFromObject,
                        context = context!("error" => err_string(self.py(), err)),
                    )
                }
            };
            Ok(inner_dict.into())
        } else {
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::DictType)
        }
    }

    fn strict_list<'data>(&'data self) -> ValResult<GenericSequence<'data>> {
        if let Ok(list) = self.cast_as::<PyList>() {
            Ok(list.into())
        } else {
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::ListType)
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
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::ListType)
        }
    }

    fn strict_set<'data>(&'data self) -> ValResult<GenericSequence<'data>> {
        if let Ok(set) = self.cast_as::<PySet>() {
            Ok(set.into())
        } else {
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::SetType)
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
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::SetType)
        }
    }

    fn strict_frozenset<'data>(&'data self) -> ValResult<GenericSequence<'data>> {
        if let Ok(set) = self.cast_as::<PyFrozenSet>() {
            Ok(set.into())
        } else {
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::FrozenSetType)
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
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::FrozenSetType)
        }
    }

    fn strict_bytes<'data>(&'data self) -> ValResult<EitherBytes<'data>> {
        if let Ok(py_bytes) = self.cast_as::<PyBytes>() {
            Ok(py_bytes.into())
        } else {
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::BytesType)
        }
    }

    fn lax_bytes<'data>(&'data self) -> ValResult<EitherBytes<'data>> {
        if let Ok(py_bytes) = self.cast_as::<PyBytes>() {
            Ok(py_bytes.into())
        } else if let Ok(py_str) = self.cast_as::<PyString>() {
            let string = py_str.to_string_lossy().to_string();
            Ok(string.into_bytes().into())
        } else {
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::BytesType)
        }
    }

    fn strict_date(&self) -> ValResult<EitherDate> {
        if self.cast_as::<PyDateTime>().is_ok() {
            // have to check if it's a datetime first, otherwise the line below converts to a date
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::DateType)
        } else if let Ok(date) = self.cast_as::<PyDate>() {
            Ok(date.into())
        } else {
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::DateType)
        }
    }

    fn lax_date(&self) -> ValResult<EitherDate> {
        if self.cast_as::<PyDateTime>().is_ok() {
            // have to check if it's a datetime first, otherwise the line below converts to a date
            // even if we later try coercion from a datetime, we don't want to return a datetime now
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::DateType)
        } else if let Ok(date) = self.cast_as::<PyDate>() {
            Ok(date.into())
        } else if let Ok(str) = self.extract::<String>() {
            bytes_as_date(self, str.as_bytes())
        } else if let Ok(py_bytes) = self.cast_as::<PyBytes>() {
            bytes_as_date(self, py_bytes.as_bytes())
        } else {
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::DateType)
        }
    }

    fn strict_time(&self) -> ValResult<EitherTime> {
        if let Ok(time) = self.cast_as::<PyTime>() {
            Ok(time.into())
        } else {
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::TimeType)
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
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::TimeType)
        } else if let Ok(int) = self.extract::<i64>() {
            int_as_time(self, int, 0)
        } else if let Ok(float) = self.extract::<f64>() {
            float_as_time(self, float)
        } else {
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::TimeType)
        }
    }

    fn strict_datetime(&self) -> ValResult<EitherDateTime> {
        if let Ok(dt) = self.cast_as::<PyDateTime>() {
            Ok(dt.into())
        } else {
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::DateTimeType)
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
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::DateTimeType)
        } else if let Ok(int) = self.extract::<i64>() {
            int_as_datetime(self, int, 0)
        } else if let Ok(float) = self.extract::<f64>() {
            float_as_datetime(self, float)
        } else if let Ok(date) = self.cast_as::<PyDate>() {
            date_as_datetime(date).map_err(as_internal)
        } else {
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::DateTimeType)
        }
    }

    fn strict_tuple<'data>(&'data self) -> ValResult<GenericSequence<'data>> {
        if let Ok(tuple) = self.cast_as::<PyTuple>() {
            Ok(tuple.into())
        } else {
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::TupleType)
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
            err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::TupleType)
        }
    }
}

/// return None if obj is not a mapping (cast_as::<PyMapping> fails or mapping.items returns an AttributeError)
/// otherwise try to covert the mapping to a dict and return an Some(error) if it fails
fn mapping_as_dict(obj: &PyAny) -> Option<PyResult<&PyDict>> {
    let mapping: &PyMapping = match obj.cast_as() {
        Ok(mapping) => mapping,
        Err(_) => return None,
    };
    // see https://github.com/PyO3/pyo3/issues/2072 - the cast_as::<PyMapping> is not entirely accurate
    // and returns some things which are definitely not mappings (e.g. str) as mapping,
    // hence we also require that the object as `items` to consider it a mapping
    match mapping.items() {
        Ok(seq) => Some(mapping_seq_as_dict(seq)),
        Err(err) => {
            if matches!(err.get_type(obj.py()).is_subclass_of::<PyAttributeError>(), Ok(true)) {
                None
            } else {
                Some(Err(err))
            }
        }
    }
}

// creating a temporary dict is slow, we could perhaps use an indexmap instead
fn mapping_seq_as_dict(seq: &PySequence) -> PyResult<&PyDict> {
    let dict = PyDict::new(seq.py());
    for r in seq.iter()? {
        let t: &PyTuple = r?.extract()?;
        let k = t.get_item(0)?;
        let v = t.get_item(1)?;
        dict.set_item(k, v)?;
    }
    Ok(dict)
}

/// This is equivalent to `GetterDict` in pydantic v1
fn instance_as_dict(instance: &PyAny) -> PyResult<&PyDict> {
    let dict = PyDict::new(instance.py());
    for k_any in instance.dir() {
        let k_str: &str = k_any.extract()?;
        if !k_str.starts_with('_') {
            let v = instance.getattr(k_any)?;
            dict.set_item(k_any, v)?;
        }
    }
    Ok(dict)
}

/// Utility for extracting a string from a PyAny, if possible.
fn maybe_as_string(v: &PyAny, unicode_error: ErrorKind) -> ValResult<Option<EitherString>> {
    if let Ok(py_string) = v.cast_as::<PyString>() {
        Ok(Some(py_string.into()))
    } else if let Ok(bytes) = v.cast_as::<PyBytes>() {
        match from_utf8(bytes.as_bytes()) {
            Ok(s) => Ok(Some(s.into())),
            Err(_) => err_val_error!(input_value = v.as_error_value(), kind = unicode_error),
        }
    } else {
        Ok(None)
    }
}

fn err_string(py: Python, err: PyErr) -> String {
    let value = err.value(py);
    match value.get_type().name() {
        Ok(type_name) => match value.str() {
            Ok(py_str) => {
                let str_cow = py_str.to_string_lossy();
                let str = str_cow.as_ref();
                if !str.is_empty() {
                    format!("{}: {}", type_name, str)
                } else {
                    type_name.to_string()
                }
            }
            Err(_) => format!("{}: <exception str() failed>", type_name),
        },
        Err(_) => "Unknown Error".to_string(),
    }
}
