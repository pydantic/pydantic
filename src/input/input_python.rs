use std::borrow::Cow;
use std::str::from_utf8;

use pyo3::exceptions::PyAttributeError;
use pyo3::once_cell::GILOnceCell;
use pyo3::prelude::*;
use pyo3::types::{
    PyBool, PyByteArray, PyBytes, PyDate, PyDateTime, PyDelta, PyDict, PyFrozenSet, PyIterator, PyList, PyMapping,
    PySequence, PySet, PyString, PyTime, PyTuple, PyType,
};
#[cfg(not(PyPy))]
use pyo3::types::{PyDictItems, PyDictKeys, PyDictValues};
use pyo3::{ffi, intern, AsPyPointer, PyTypeInfo};

use crate::errors::{py_err_string, ErrorType, InputValue, LocItem, ValError, ValLineError, ValResult};
use crate::PyUrl;

use super::datetime::{
    bytes_as_date, bytes_as_datetime, bytes_as_time, bytes_as_timedelta, date_as_datetime, float_as_datetime,
    float_as_duration, float_as_time, int_as_datetime, int_as_duration, int_as_time, EitherDate, EitherDateTime,
    EitherTime,
};
use super::input_abstract::InputType;
use super::shared::{float_as_int, int_as_bool, map_json_err, str_as_bool, str_as_int};
use super::{
    py_error_on_minusone, py_string_str, repr_string, EitherBytes, EitherString, EitherTimedelta, GenericArguments,
    GenericCollection, GenericIterator, GenericMapping, Input, JsonInput, PyArgs,
};

/// Extract generators and deques into a `GenericCollection`
macro_rules! extract_shared_iter {
    ($type:ty, $obj:ident) => {
        if $obj.cast_as::<PyIterator>().is_ok() {
            Some($obj.into())
        } else if is_deque($obj) {
            Some($obj.into())
        } else {
            None
        }
    };
}

/// Extract dict keys, values and items into a `GenericCollection`, not available on PyPy
#[cfg(not(PyPy))]
macro_rules! extract_dict_iter {
    ($obj:ident) => {
        if $obj.is_instance_of::<PyDictKeys>().unwrap_or(false) {
            Some($obj.into())
        } else if $obj.is_instance_of::<PyDictValues>().unwrap_or(false) {
            Some($obj.into())
        } else if $obj.is_instance_of::<PyDictItems>().unwrap_or(false) {
            Some($obj.into())
        } else {
            None
        }
    };
}

impl<'a> Input<'a> for PyAny {
    fn get_type(&self) -> &'static InputType {
        &InputType::Python
    }

    fn as_loc_item(&self) -> LocItem {
        if let Ok(py_str) = self.cast_as::<PyString>() {
            py_str.to_string_lossy().as_ref().into()
        } else if let Ok(key_int) = self.extract::<usize>() {
            key_int.into()
        } else {
            match repr_string(self) {
                Ok(s) => s.into(),
                Err(_) => format!("{self:?}").into(),
            }
        }
    }

    fn as_error_value(&'a self) -> InputValue<'a> {
        InputValue::PyAny(self)
    }

    fn identity(&self) -> Option<usize> {
        Some(self.as_ptr() as usize)
    }

    fn is_none(&self) -> bool {
        self.is_none()
    }

    fn get_attr(&self, name: &PyString) -> Option<&PyAny> {
        self.getattr(name).ok()
    }

    fn input_is_instance(&self, class: &PyAny, _json_mask: u8) -> PyResult<bool> {
        // See PyO3/pyo3#2694 - we can't use `is_instance` here since it requires PyType,
        // and some check objects are not types, this logic is lifted from `is_instance` in PyO3
        let result = unsafe { ffi::PyObject_IsInstance(self.as_ptr(), class.as_ptr()) };
        py_error_on_minusone(self.py(), result)?;
        Ok(result == 1)
    }

    fn is_exact_instance(&self, class: &PyType) -> PyResult<bool> {
        self.get_type().eq(class)
    }

    fn input_is_subclass(&self, class: &PyType) -> PyResult<bool> {
        match self.cast_as::<PyType>() {
            Ok(py_type) => py_type.is_subclass(class),
            Err(_) => Ok(false),
        }
    }

    fn input_as_url(&self) -> Option<PyUrl> {
        self.extract::<PyUrl>().ok()
    }

    fn callable(&self) -> bool {
        self.is_callable()
    }

    fn validate_args(&'a self) -> ValResult<'a, GenericArguments<'a>> {
        if let Ok(dict) = self.cast_as::<PyDict>() {
            if let Some(args) = dict.get_item("__args__") {
                if let Some(kwargs) = dict.get_item("__kwargs__") {
                    // we only try this logic if there are only these two items in the dict
                    if dict.len() == 2 {
                        let args = if let Ok(tuple) = args.cast_as::<PyTuple>() {
                            Ok(Some(tuple))
                        } else if args.is_none() {
                            Ok(None)
                        } else if let Ok(list) = args.cast_as::<PyList>() {
                            Ok(Some(PyTuple::new(self.py(), list.iter())))
                        } else {
                            Err(ValLineError::new_with_loc(
                                ErrorType::PositionalArgumentsType,
                                args,
                                "__args__",
                            ))
                        };

                        let kwargs = if let Ok(dict) = kwargs.cast_as::<PyDict>() {
                            Ok(Some(dict))
                        } else if kwargs.is_none() {
                            Ok(None)
                        } else {
                            Err(ValLineError::new_with_loc(
                                ErrorType::KeywordArgumentsType,
                                kwargs,
                                "__kwargs__",
                            ))
                        };

                        return match (args, kwargs) {
                            (Ok(args), Ok(kwargs)) => Ok(PyArgs::new(args, kwargs).into()),
                            (Err(args_error), Err(kwargs_error)) => {
                                Err(ValError::LineErrors(vec![args_error, kwargs_error]))
                            }
                            (Err(error), _) => Err(ValError::LineErrors(vec![error])),
                            (_, Err(error)) => Err(ValError::LineErrors(vec![error])),
                        };
                    }
                }
            }
            Ok(PyArgs::new(None, Some(dict)).into())
        } else if let Ok(tuple) = self.cast_as::<PyTuple>() {
            Ok(PyArgs::new(Some(tuple), None).into())
        } else if let Ok(list) = self.cast_as::<PyList>() {
            let tuple = PyTuple::new(self.py(), list.iter());
            Ok(PyArgs::new(Some(tuple), None).into())
        } else {
            Err(ValError::new(ErrorType::ArgumentsType, self))
        }
    }

    fn parse_json(&'a self) -> ValResult<'a, JsonInput> {
        if let Ok(py_bytes) = self.cast_as::<PyBytes>() {
            serde_json::from_slice(py_bytes.as_bytes()).map_err(|e| map_json_err(self, e))
        } else if let Ok(py_str) = self.cast_as::<PyString>() {
            let str = py_str.to_str()?;
            serde_json::from_str(str).map_err(|e| map_json_err(self, e))
        } else if let Ok(py_byte_array) = self.cast_as::<PyByteArray>() {
            serde_json::from_slice(unsafe { py_byte_array.as_bytes() }).map_err(|e| map_json_err(self, e))
        } else {
            Err(ValError::new(ErrorType::JsonType, self))
        }
    }

    fn strict_str(&'a self) -> ValResult<EitherString<'a>> {
        if let Ok(py_str) = self.cast_as::<PyString>() {
            if is_builtin_str(py_str) {
                Ok(py_str.into())
            } else {
                Err(ValError::new(ErrorType::StringSubType, self))
            }
        } else {
            Err(ValError::new(ErrorType::StringType, self))
        }
    }

    fn lax_str(&'a self) -> ValResult<EitherString<'a>> {
        if let Ok(py_str) = self.cast_as::<PyString>() {
            if is_builtin_str(py_str) {
                Ok(py_str.into())
            } else {
                // force to a rust string to make sure behaviour is consistent whether or not we go via a
                // rust string in StrConstrainedValidator - e.g. to_lower
                Ok(py_string_str(py_str)?.into())
            }
        } else if let Ok(bytes) = self.cast_as::<PyBytes>() {
            let str = match from_utf8(bytes.as_bytes()) {
                Ok(s) => s,
                Err(_) => return Err(ValError::new(ErrorType::StringUnicode, self)),
            };
            Ok(str.into())
        } else if let Ok(py_byte_array) = self.cast_as::<PyByteArray>() {
            let str = match from_utf8(unsafe { py_byte_array.as_bytes() }) {
                Ok(s) => s,
                Err(_) => return Err(ValError::new(ErrorType::StringUnicode, self)),
            };
            Ok(str.into())
        } else {
            Err(ValError::new(ErrorType::StringType, self))
        }
    }

    fn strict_bytes(&'a self) -> ValResult<EitherBytes<'a>> {
        if let Ok(py_bytes) = self.cast_as::<PyBytes>() {
            Ok(py_bytes.into())
        } else {
            Err(ValError::new(ErrorType::BytesType, self))
        }
    }

    fn lax_bytes(&'a self) -> ValResult<EitherBytes<'a>> {
        if let Ok(py_bytes) = self.cast_as::<PyBytes>() {
            Ok(py_bytes.into())
        } else if let Ok(py_str) = self.cast_as::<PyString>() {
            let str = py_string_str(py_str)?;
            Ok(str.as_bytes().into())
        } else if let Ok(py_byte_array) = self.cast_as::<PyByteArray>() {
            Ok(py_byte_array.to_vec().into())
        } else {
            Err(ValError::new(ErrorType::BytesType, self))
        }
    }

    fn strict_bool(&self) -> ValResult<bool> {
        if let Ok(bool) = self.extract::<bool>() {
            Ok(bool)
        } else {
            Err(ValError::new(ErrorType::BoolType, self))
        }
    }

    fn lax_bool(&self) -> ValResult<bool> {
        if let Ok(bool) = self.extract::<bool>() {
            Ok(bool)
        } else if let Some(cow_str) = maybe_as_string(self, ErrorType::BoolParsing)? {
            str_as_bool(self, &cow_str)
        } else if let Ok(int) = self.extract::<i64>() {
            int_as_bool(self, int)
        } else if let Ok(float) = self.extract::<f64>() {
            match float_as_int(self, float) {
                Ok(int) => int_as_bool(self, int),
                _ => Err(ValError::new(ErrorType::BoolType, self)),
            }
        } else {
            Err(ValError::new(ErrorType::BoolType, self))
        }
    }

    fn strict_int(&self) -> ValResult<i64> {
        // bool check has to come before int check as bools would be cast to ints below
        if self.extract::<bool>().is_ok() {
            Err(ValError::new(ErrorType::IntType, self))
        } else if let Ok(int) = self.extract::<i64>() {
            Ok(int)
        } else {
            Err(ValError::new(ErrorType::IntType, self))
        }
    }

    fn lax_int(&self) -> ValResult<i64> {
        if let Ok(int) = self.extract::<i64>() {
            Ok(int)
        } else if let Some(cow_str) = maybe_as_string(self, ErrorType::IntParsing)? {
            str_as_int(self, &cow_str)
        } else if let Ok(float) = self.extract::<f64>() {
            float_as_int(self, float)
        } else {
            Err(ValError::new(ErrorType::IntType, self))
        }
    }

    fn strict_float(&self) -> ValResult<f64> {
        if self.extract::<bool>().is_ok() {
            Err(ValError::new(ErrorType::FloatType, self))
        } else if let Ok(float) = self.extract::<f64>() {
            Ok(float)
        } else {
            Err(ValError::new(ErrorType::FloatType, self))
        }
    }

    fn lax_float(&self) -> ValResult<f64> {
        if let Ok(float) = self.extract::<f64>() {
            Ok(float)
        } else if let Some(cow_str) = maybe_as_string(self, ErrorType::FloatParsing)? {
            match cow_str.as_ref().parse::<f64>() {
                Ok(i) => Ok(i),
                Err(_) => Err(ValError::new(ErrorType::FloatParsing, self)),
            }
        } else {
            Err(ValError::new(ErrorType::FloatType, self))
        }
    }

    fn strict_dict(&'a self) -> ValResult<GenericMapping<'a>> {
        if let Ok(dict) = self.cast_as::<PyDict>() {
            Ok(dict.into())
        } else {
            Err(ValError::new(ErrorType::DictType, self))
        }
    }

    fn lax_dict(&'a self) -> ValResult<GenericMapping<'a>> {
        if let Ok(dict) = self.cast_as::<PyDict>() {
            Ok(dict.into())
        } else if let Some(generic_mapping) = mapping_as_dict(self) {
            generic_mapping
        } else {
            Err(ValError::new(ErrorType::DictType, self))
        }
    }

    fn validate_typed_dict(&'a self, strict: bool, from_attributes: bool) -> ValResult<GenericMapping<'a>> {
        if from_attributes {
            // if from_attributes, first try a dict, then mapping then from_attributes
            if let Ok(dict) = self.cast_as::<PyDict>() {
                return Ok(dict.into());
            } else if !strict {
                // we can't do this in one set of if/else because we need to check from_mapping before doing this
                if let Some(generic_mapping) = mapping_as_dict(self) {
                    return generic_mapping;
                }
            }

            if from_attributes_applicable(self) {
                Ok(self.into())
            } else {
                // note the error here gives a hint about from_attributes
                Err(ValError::new(ErrorType::DictAttributesType, self))
            }
        } else {
            // otherwise we just call back to lax_dict if from_mapping is allowed, not there error in this
            // case (correctly) won't hint about from_attributes
            self.validate_dict(strict)
        }
    }

    fn strict_list(&'a self) -> ValResult<GenericCollection<'a>> {
        if let Ok(list) = self.cast_as::<PyList>() {
            Ok(list.into())
        } else {
            Err(ValError::new(ErrorType::ListType, self))
        }
    }

    #[cfg(not(PyPy))]
    fn lax_list(&'a self, allow_any_iter: bool) -> ValResult<GenericCollection<'a>> {
        if let Ok(list) = self.cast_as::<PyList>() {
            Ok(list.into())
        } else if let Ok(tuple) = self.cast_as::<PyTuple>() {
            Ok(tuple.into())
        } else if let Some(collection) = extract_dict_iter!(self) {
            Ok(collection)
        } else if allow_any_iter && self.iter().is_ok() {
            Ok(self.into())
        } else if let Some(collection) = extract_shared_iter!(PyList, self) {
            Ok(collection)
        } else {
            Err(ValError::new(ErrorType::ListType, self))
        }
    }

    #[cfg(PyPy)]
    fn lax_list(&'a self, allow_any_iter: bool) -> ValResult<GenericCollection<'a>> {
        if let Ok(list) = self.cast_as::<PyList>() {
            Ok(list.into())
        } else if let Ok(tuple) = self.cast_as::<PyTuple>() {
            Ok(tuple.into())
        } else if allow_any_iter && self.iter().is_ok() {
            Ok(self.into())
        } else if let Some(collection) = extract_shared_iter!(PyList, self) {
            Ok(collection)
        } else {
            Err(ValError::new(ErrorType::ListType, self))
        }
    }

    fn strict_tuple(&'a self) -> ValResult<GenericCollection<'a>> {
        if let Ok(tuple) = self.cast_as::<PyTuple>() {
            Ok(tuple.into())
        } else {
            Err(ValError::new(ErrorType::TupleType, self))
        }
    }

    #[cfg(not(PyPy))]
    fn lax_tuple(&'a self) -> ValResult<GenericCollection<'a>> {
        if let Ok(tuple) = self.cast_as::<PyTuple>() {
            Ok(tuple.into())
        } else if let Ok(list) = self.cast_as::<PyList>() {
            Ok(list.into())
        } else if let Some(collection) = extract_dict_iter!(self) {
            Ok(collection)
        } else if let Some(collection) = extract_shared_iter!(PyTuple, self) {
            Ok(collection)
        } else {
            Err(ValError::new(ErrorType::TupleType, self))
        }
    }

    #[cfg(PyPy)]
    fn lax_tuple(&'a self) -> ValResult<GenericCollection<'a>> {
        if let Ok(tuple) = self.cast_as::<PyTuple>() {
            Ok(tuple.into())
        } else if let Ok(list) = self.cast_as::<PyList>() {
            Ok(list.into())
        } else if let Some(collection) = extract_shared_iter!(PyTuple, self) {
            Ok(collection)
        } else {
            Err(ValError::new(ErrorType::TupleType, self))
        }
    }

    fn strict_set(&'a self) -> ValResult<GenericCollection<'a>> {
        if let Ok(set) = self.cast_as::<PySet>() {
            Ok(set.into())
        } else {
            Err(ValError::new(ErrorType::SetType, self))
        }
    }

    #[cfg(not(PyPy))]
    fn lax_set(&'a self) -> ValResult<GenericCollection<'a>> {
        if let Ok(set) = self.cast_as::<PySet>() {
            Ok(set.into())
        } else if let Ok(list) = self.cast_as::<PyList>() {
            Ok(list.into())
        } else if let Ok(tuple) = self.cast_as::<PyTuple>() {
            Ok(tuple.into())
        } else if let Ok(frozen_set) = self.cast_as::<PyFrozenSet>() {
            Ok(frozen_set.into())
        } else if let Some(collection) = extract_dict_iter!(self) {
            Ok(collection)
        } else if let Some(collection) = extract_shared_iter!(PyTuple, self) {
            Ok(collection)
        } else {
            Err(ValError::new(ErrorType::SetType, self))
        }
    }

    #[cfg(PyPy)]
    fn lax_set(&'a self) -> ValResult<GenericCollection<'a>> {
        if let Ok(set) = self.cast_as::<PySet>() {
            Ok(set.into())
        } else if let Ok(list) = self.cast_as::<PyList>() {
            Ok(list.into())
        } else if let Ok(tuple) = self.cast_as::<PyTuple>() {
            Ok(tuple.into())
        } else if let Ok(frozen_set) = self.cast_as::<PyFrozenSet>() {
            Ok(frozen_set.into())
        } else if let Some(collection) = extract_shared_iter!(PyTuple, self) {
            Ok(collection)
        } else {
            Err(ValError::new(ErrorType::SetType, self))
        }
    }

    fn strict_frozenset(&'a self) -> ValResult<GenericCollection<'a>> {
        if let Ok(set) = self.cast_as::<PyFrozenSet>() {
            Ok(set.into())
        } else {
            Err(ValError::new(ErrorType::FrozenSetType, self))
        }
    }

    #[cfg(not(PyPy))]
    fn lax_frozenset(&'a self) -> ValResult<GenericCollection<'a>> {
        if let Ok(frozen_set) = self.cast_as::<PyFrozenSet>() {
            Ok(frozen_set.into())
        } else if let Ok(set) = self.cast_as::<PySet>() {
            Ok(set.into())
        } else if let Ok(list) = self.cast_as::<PyList>() {
            Ok(list.into())
        } else if let Ok(tuple) = self.cast_as::<PyTuple>() {
            Ok(tuple.into())
        } else if let Some(collection) = extract_dict_iter!(self) {
            Ok(collection)
        } else if let Some(collection) = extract_shared_iter!(PyTuple, self) {
            Ok(collection)
        } else {
            Err(ValError::new(ErrorType::FrozenSetType, self))
        }
    }

    #[cfg(PyPy)]
    fn lax_frozenset(&'a self) -> ValResult<GenericCollection<'a>> {
        if let Ok(frozen_set) = self.cast_as::<PyFrozenSet>() {
            Ok(frozen_set.into())
        } else if let Ok(set) = self.cast_as::<PySet>() {
            Ok(set.into())
        } else if let Ok(list) = self.cast_as::<PyList>() {
            Ok(list.into())
        } else if let Ok(tuple) = self.cast_as::<PyTuple>() {
            Ok(tuple.into())
        } else if let Some(collection) = extract_shared_iter!(PyTuple, self) {
            Ok(collection)
        } else {
            Err(ValError::new(ErrorType::FrozenSetType, self))
        }
    }

    fn validate_iter(&self) -> ValResult<GenericIterator> {
        if self.iter().is_ok() {
            Ok(self.into())
        } else {
            Err(ValError::new(ErrorType::IterableType, self))
        }
    }

    fn strict_date(&self) -> ValResult<EitherDate> {
        if self.cast_as::<PyDateTime>().is_ok() {
            // have to check if it's a datetime first, otherwise the line below converts to a date
            Err(ValError::new(ErrorType::DateType, self))
        } else if let Ok(date) = self.cast_as::<PyDate>() {
            Ok(date.into())
        } else {
            Err(ValError::new(ErrorType::DateType, self))
        }
    }

    fn lax_date(&self) -> ValResult<EitherDate> {
        if self.cast_as::<PyDateTime>().is_ok() {
            // have to check if it's a datetime first, otherwise the line below converts to a date
            // even if we later try coercion from a datetime, we don't want to return a datetime now
            Err(ValError::new(ErrorType::DateType, self))
        } else if let Ok(date) = self.cast_as::<PyDate>() {
            Ok(date.into())
        } else if let Ok(py_str) = self.cast_as::<PyString>() {
            let str = py_string_str(py_str)?;
            bytes_as_date(self, str.as_bytes())
        } else if let Ok(py_bytes) = self.cast_as::<PyBytes>() {
            bytes_as_date(self, py_bytes.as_bytes())
        } else {
            Err(ValError::new(ErrorType::DateType, self))
        }
    }

    fn strict_time(&self) -> ValResult<EitherTime> {
        if let Ok(time) = self.cast_as::<PyTime>() {
            Ok(time.into())
        } else {
            Err(ValError::new(ErrorType::TimeType, self))
        }
    }

    fn lax_time(&self) -> ValResult<EitherTime> {
        if let Ok(time) = self.cast_as::<PyTime>() {
            Ok(time.into())
        } else if let Ok(py_str) = self.cast_as::<PyString>() {
            let str = py_string_str(py_str)?;
            bytes_as_time(self, str.as_bytes())
        } else if let Ok(py_bytes) = self.cast_as::<PyBytes>() {
            bytes_as_time(self, py_bytes.as_bytes())
        } else if self.cast_as::<PyBool>().is_ok() {
            Err(ValError::new(ErrorType::TimeType, self))
        } else if let Ok(int) = self.extract::<i64>() {
            int_as_time(self, int, 0)
        } else if let Ok(float) = self.extract::<f64>() {
            float_as_time(self, float)
        } else {
            Err(ValError::new(ErrorType::TimeType, self))
        }
    }

    fn strict_datetime(&self) -> ValResult<EitherDateTime> {
        if let Ok(dt) = self.cast_as::<PyDateTime>() {
            Ok(dt.into())
        } else {
            Err(ValError::new(ErrorType::DatetimeType, self))
        }
    }

    fn lax_datetime(&self) -> ValResult<EitherDateTime> {
        if let Ok(dt) = self.cast_as::<PyDateTime>() {
            Ok(dt.into())
        } else if let Ok(py_str) = self.cast_as::<PyString>() {
            let str = py_string_str(py_str)?;
            bytes_as_datetime(self, str.as_bytes())
        } else if let Ok(py_bytes) = self.cast_as::<PyBytes>() {
            bytes_as_datetime(self, py_bytes.as_bytes())
        } else if self.cast_as::<PyBool>().is_ok() {
            Err(ValError::new(ErrorType::DatetimeType, self))
        } else if let Ok(int) = self.extract::<i64>() {
            int_as_datetime(self, int, 0)
        } else if let Ok(float) = self.extract::<f64>() {
            float_as_datetime(self, float)
        } else if let Ok(date) = self.cast_as::<PyDate>() {
            Ok(date_as_datetime(date)?)
        } else {
            Err(ValError::new(ErrorType::DatetimeType, self))
        }
    }

    fn strict_timedelta(&self) -> ValResult<EitherTimedelta> {
        if let Ok(dt) = self.cast_as::<PyDelta>() {
            Ok(dt.into())
        } else {
            Err(ValError::new(ErrorType::TimeDeltaType, self))
        }
    }

    fn lax_timedelta(&self) -> ValResult<EitherTimedelta> {
        if let Ok(dt) = self.cast_as::<PyDelta>() {
            Ok(dt.into())
        } else if let Ok(py_str) = self.cast_as::<PyString>() {
            let str = py_string_str(py_str)?;
            bytes_as_timedelta(self, str.as_bytes())
        } else if let Ok(py_bytes) = self.cast_as::<PyBytes>() {
            bytes_as_timedelta(self, py_bytes.as_bytes())
        } else if let Ok(int) = self.extract::<i64>() {
            Ok(int_as_duration(self, int)?.into())
        } else if let Ok(float) = self.extract::<f64>() {
            Ok(float_as_duration(self, float)?.into())
        } else {
            Err(ValError::new(ErrorType::TimeDeltaType, self))
        }
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
            ErrorType::DictFromMapping {
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
        let (key, value): (&PyAny, &PyAny) = r?.extract()?;
        dict.set_item(key, value)?;
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
fn maybe_as_string(v: &PyAny, unicode_error: ErrorType) -> ValResult<Option<Cow<str>>> {
    if let Ok(py_string) = v.cast_as::<PyString>() {
        let str = py_string_str(py_string)?;
        Ok(Some(Cow::Borrowed(str)))
    } else if let Ok(bytes) = v.cast_as::<PyBytes>() {
        match from_utf8(bytes.as_bytes()) {
            Ok(s) => Ok(Some(Cow::Owned(s.to_string()))),
            Err(_) => Err(ValError::new(unicode_error, v)),
        }
    } else {
        Ok(None)
    }
}

static DEQUE_TYPE: GILOnceCell<Py<PyType>> = GILOnceCell::new();

fn is_deque(v: &PyAny) -> bool {
    let py = v.py();
    let deque_type = DEQUE_TYPE
        .get_or_init(py, || import_type(py, "collections", "deque").unwrap())
        .as_ref(py);
    v.is_instance(deque_type).unwrap_or(false)
}

fn import_type(py: Python, module: &str, attr: &str) -> PyResult<Py<PyType>> {
    let obj = py.import(module)?.getattr(attr)?;
    Ok(obj.cast_as::<PyType>()?.into())
}

fn is_builtin_str(py_str: &PyString) -> bool {
    py_str.get_type().is(PyString::type_object(py_str.py()))
}
