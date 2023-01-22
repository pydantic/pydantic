use std::borrow::Cow;
use std::str::from_utf8;

use pyo3::once_cell::GILOnceCell;
use pyo3::prelude::*;
use pyo3::types::{
    PyBool, PyByteArray, PyBytes, PyDate, PyDateTime, PyDelta, PyDict, PyFrozenSet, PyIterator, PyList, PyMapping,
    PySet, PyString, PyTime, PyTuple, PyType,
};
#[cfg(not(PyPy))]
use pyo3::types::{PyDictItems, PyDictKeys, PyDictValues};
use pyo3::{ffi, intern, AsPyPointer, PyTypeInfo};

use crate::build_tools::safe_repr;
use crate::errors::{ErrorType, InputValue, LocItem, ValError, ValLineError, ValResult};
use crate::{PyMultiHostUrl, PyUrl};

use super::datetime::{
    bytes_as_date, bytes_as_datetime, bytes_as_time, bytes_as_timedelta, date_as_datetime, float_as_datetime,
    float_as_duration, float_as_time, int_as_datetime, int_as_duration, int_as_time, EitherDate, EitherDateTime,
    EitherTime,
};
use super::input_abstract::InputType;
use super::shared::{float_as_int, int_as_bool, map_json_err, str_as_bool, str_as_int};
use super::{
    py_error_on_minusone, py_string_str, EitherBytes, EitherString, EitherTimedelta, GenericArguments,
    GenericCollection, GenericIterator, GenericMapping, Input, JsonInput, PyArgs,
};

/// Extract generators and deques into a `GenericCollection`
macro_rules! extract_shared_iter {
    ($type:ty, $obj:ident) => {
        if $obj.downcast::<PyIterator>().is_ok() {
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
        if let Ok(py_str) = self.downcast::<PyString>() {
            py_str.to_string_lossy().as_ref().into()
        } else if let Ok(key_int) = self.extract::<usize>() {
            key_int.into()
        } else {
            safe_repr(self).to_string().into()
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
        match self.downcast::<PyType>() {
            Ok(py_type) => py_type.is_subclass(class),
            Err(_) => Ok(false),
        }
    }

    fn input_as_url(&self) -> Option<PyUrl> {
        self.extract::<PyUrl>().ok()
    }

    fn input_as_multi_host_url(&self) -> Option<PyMultiHostUrl> {
        self.extract::<PyMultiHostUrl>().ok()
    }

    fn callable(&self) -> bool {
        self.is_callable()
    }

    fn validate_args(&'a self) -> ValResult<'a, GenericArguments<'a>> {
        if let Ok(dict) = self.downcast::<PyDict>() {
            if let Some(args) = dict.get_item("__args__") {
                if let Some(kwargs) = dict.get_item("__kwargs__") {
                    // we only try this logic if there are only these two items in the dict
                    if dict.len() == 2 {
                        let args = if let Ok(tuple) = args.downcast::<PyTuple>() {
                            Ok(Some(tuple))
                        } else if args.is_none() {
                            Ok(None)
                        } else if let Ok(list) = args.downcast::<PyList>() {
                            Ok(Some(PyTuple::new(self.py(), list.iter())))
                        } else {
                            Err(ValLineError::new_with_loc(
                                ErrorType::PositionalArgumentsType,
                                args,
                                "__args__",
                            ))
                        };

                        let kwargs = if let Ok(dict) = kwargs.downcast::<PyDict>() {
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
        } else if let Ok(tuple) = self.downcast::<PyTuple>() {
            Ok(PyArgs::new(Some(tuple), None).into())
        } else if let Ok(list) = self.downcast::<PyList>() {
            let tuple = PyTuple::new(self.py(), list.iter());
            Ok(PyArgs::new(Some(tuple), None).into())
        } else {
            Err(ValError::new(ErrorType::ArgumentsType, self))
        }
    }

    fn parse_json(&'a self) -> ValResult<'a, JsonInput> {
        if let Ok(py_bytes) = self.downcast::<PyBytes>() {
            serde_json::from_slice(py_bytes.as_bytes()).map_err(|e| map_json_err(self, e))
        } else if let Ok(py_str) = self.downcast::<PyString>() {
            let str = py_str.to_str()?;
            serde_json::from_str(str).map_err(|e| map_json_err(self, e))
        } else if let Ok(py_byte_array) = self.downcast::<PyByteArray>() {
            serde_json::from_slice(unsafe { py_byte_array.as_bytes() }).map_err(|e| map_json_err(self, e))
        } else {
            Err(ValError::new(ErrorType::JsonType, self))
        }
    }

    fn strict_str(&'a self) -> ValResult<EitherString<'a>> {
        if let Ok(py_str) = self.downcast::<PyString>() {
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
        if let Ok(py_str) = self.downcast::<PyString>() {
            if is_builtin_str(py_str) {
                Ok(py_str.into())
            } else {
                // force to a rust string to make sure behaviour is consistent whether or not we go via a
                // rust string in StrConstrainedValidator - e.g. to_lower
                Ok(py_string_str(py_str)?.into())
            }
        } else if let Ok(bytes) = self.downcast::<PyBytes>() {
            let str = match from_utf8(bytes.as_bytes()) {
                Ok(s) => s,
                Err(_) => return Err(ValError::new(ErrorType::StringUnicode, self)),
            };
            Ok(str.into())
        } else if let Ok(py_byte_array) = self.downcast::<PyByteArray>() {
            // see https://docs.rs/pyo3/latest/pyo3/types/struct.PyByteArray.html#method.as_bytes
            // for why this is marked unsafe
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
        if let Ok(py_bytes) = self.downcast::<PyBytes>() {
            Ok(py_bytes.into())
        } else {
            Err(ValError::new(ErrorType::BytesType, self))
        }
    }

    fn lax_bytes(&'a self) -> ValResult<EitherBytes<'a>> {
        if let Ok(py_bytes) = self.downcast::<PyBytes>() {
            Ok(py_bytes.into())
        } else if let Ok(py_str) = self.downcast::<PyString>() {
            let str = py_string_str(py_str)?;
            Ok(str.as_bytes().into())
        } else if let Ok(py_byte_array) = self.downcast::<PyByteArray>() {
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
        if let Ok(dict) = self.downcast::<PyDict>() {
            Ok(dict.into())
        } else {
            Err(ValError::new(ErrorType::DictType, self))
        }
    }

    fn lax_dict(&'a self) -> ValResult<GenericMapping<'a>> {
        if let Ok(dict) = self.downcast::<PyDict>() {
            Ok(dict.into())
        } else if let Ok(mapping) = self.downcast::<PyMapping>() {
            Ok(mapping.into())
        } else {
            Err(ValError::new(ErrorType::DictType, self))
        }
    }

    fn validate_typed_dict(&'a self, strict: bool, from_attributes: bool) -> ValResult<GenericMapping<'a>> {
        if from_attributes {
            // if from_attributes, first try a dict, then mapping then from_attributes
            if let Ok(dict) = self.downcast::<PyDict>() {
                return Ok(dict.into());
            } else if !strict {
                if let Ok(mapping) = self.downcast::<PyMapping>() {
                    return Ok(mapping.into());
                }
            }

            if from_attributes_applicable(self) {
                Ok(self.into())
            } else if let Ok((obj, kwargs)) = self.extract::<(&PyAny, &PyDict)>() {
                if from_attributes_applicable(obj) {
                    Ok(GenericMapping::PyGetAttr(obj, Some(kwargs)))
                } else {
                    Err(ValError::new(ErrorType::DictAttributesType, self))
                }
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
        if let Ok(list) = self.downcast::<PyList>() {
            Ok(list.into())
        } else {
            Err(ValError::new(ErrorType::ListType, self))
        }
    }

    #[cfg(not(PyPy))]
    fn lax_list(&'a self, allow_any_iter: bool) -> ValResult<GenericCollection<'a>> {
        if let Ok(list) = self.downcast::<PyList>() {
            Ok(list.into())
        } else if let Ok(tuple) = self.downcast::<PyTuple>() {
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
        if let Ok(list) = self.downcast::<PyList>() {
            Ok(list.into())
        } else if let Ok(tuple) = self.downcast::<PyTuple>() {
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
        if let Ok(tuple) = self.downcast::<PyTuple>() {
            Ok(tuple.into())
        } else {
            Err(ValError::new(ErrorType::TupleType, self))
        }
    }

    #[cfg(not(PyPy))]
    fn lax_tuple(&'a self) -> ValResult<GenericCollection<'a>> {
        if let Ok(tuple) = self.downcast::<PyTuple>() {
            Ok(tuple.into())
        } else if let Ok(list) = self.downcast::<PyList>() {
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
        if let Ok(tuple) = self.downcast::<PyTuple>() {
            Ok(tuple.into())
        } else if let Ok(list) = self.downcast::<PyList>() {
            Ok(list.into())
        } else if let Some(collection) = extract_shared_iter!(PyTuple, self) {
            Ok(collection)
        } else {
            Err(ValError::new(ErrorType::TupleType, self))
        }
    }

    fn strict_set(&'a self) -> ValResult<GenericCollection<'a>> {
        if let Ok(set) = self.downcast::<PySet>() {
            Ok(set.into())
        } else {
            Err(ValError::new(ErrorType::SetType, self))
        }
    }

    #[cfg(not(PyPy))]
    fn lax_set(&'a self) -> ValResult<GenericCollection<'a>> {
        if let Ok(set) = self.downcast::<PySet>() {
            Ok(set.into())
        } else if let Ok(list) = self.downcast::<PyList>() {
            Ok(list.into())
        } else if let Ok(tuple) = self.downcast::<PyTuple>() {
            Ok(tuple.into())
        } else if let Ok(frozen_set) = self.downcast::<PyFrozenSet>() {
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
        if let Ok(set) = self.downcast::<PySet>() {
            Ok(set.into())
        } else if let Ok(list) = self.downcast::<PyList>() {
            Ok(list.into())
        } else if let Ok(tuple) = self.downcast::<PyTuple>() {
            Ok(tuple.into())
        } else if let Ok(frozen_set) = self.downcast::<PyFrozenSet>() {
            Ok(frozen_set.into())
        } else if let Some(collection) = extract_shared_iter!(PyTuple, self) {
            Ok(collection)
        } else {
            Err(ValError::new(ErrorType::SetType, self))
        }
    }

    fn strict_frozenset(&'a self) -> ValResult<GenericCollection<'a>> {
        if let Ok(set) = self.downcast::<PyFrozenSet>() {
            Ok(set.into())
        } else {
            Err(ValError::new(ErrorType::FrozenSetType, self))
        }
    }

    #[cfg(not(PyPy))]
    fn lax_frozenset(&'a self) -> ValResult<GenericCollection<'a>> {
        if let Ok(frozen_set) = self.downcast::<PyFrozenSet>() {
            Ok(frozen_set.into())
        } else if let Ok(set) = self.downcast::<PySet>() {
            Ok(set.into())
        } else if let Ok(list) = self.downcast::<PyList>() {
            Ok(list.into())
        } else if let Ok(tuple) = self.downcast::<PyTuple>() {
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
        if let Ok(frozen_set) = self.downcast::<PyFrozenSet>() {
            Ok(frozen_set.into())
        } else if let Ok(set) = self.downcast::<PySet>() {
            Ok(set.into())
        } else if let Ok(list) = self.downcast::<PyList>() {
            Ok(list.into())
        } else if let Ok(tuple) = self.downcast::<PyTuple>() {
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
        if self.downcast::<PyDateTime>().is_ok() {
            // have to check if it's a datetime first, otherwise the line below converts to a date
            Err(ValError::new(ErrorType::DateType, self))
        } else if let Ok(date) = self.downcast::<PyDate>() {
            Ok(date.into())
        } else {
            Err(ValError::new(ErrorType::DateType, self))
        }
    }

    fn lax_date(&self) -> ValResult<EitherDate> {
        if self.downcast::<PyDateTime>().is_ok() {
            // have to check if it's a datetime first, otherwise the line below converts to a date
            // even if we later try coercion from a datetime, we don't want to return a datetime now
            Err(ValError::new(ErrorType::DateType, self))
        } else if let Ok(date) = self.downcast::<PyDate>() {
            Ok(date.into())
        } else if let Ok(py_str) = self.downcast::<PyString>() {
            let str = py_string_str(py_str)?;
            bytes_as_date(self, str.as_bytes())
        } else if let Ok(py_bytes) = self.downcast::<PyBytes>() {
            bytes_as_date(self, py_bytes.as_bytes())
        } else {
            Err(ValError::new(ErrorType::DateType, self))
        }
    }

    fn strict_time(&self) -> ValResult<EitherTime> {
        if let Ok(time) = self.downcast::<PyTime>() {
            Ok(time.into())
        } else {
            Err(ValError::new(ErrorType::TimeType, self))
        }
    }

    fn lax_time(&self) -> ValResult<EitherTime> {
        if let Ok(time) = self.downcast::<PyTime>() {
            Ok(time.into())
        } else if let Ok(py_str) = self.downcast::<PyString>() {
            let str = py_string_str(py_str)?;
            bytes_as_time(self, str.as_bytes())
        } else if let Ok(py_bytes) = self.downcast::<PyBytes>() {
            bytes_as_time(self, py_bytes.as_bytes())
        } else if self.downcast::<PyBool>().is_ok() {
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
        if let Ok(dt) = self.downcast::<PyDateTime>() {
            Ok(dt.into())
        } else {
            Err(ValError::new(ErrorType::DatetimeType, self))
        }
    }

    fn lax_datetime(&self) -> ValResult<EitherDateTime> {
        if let Ok(dt) = self.downcast::<PyDateTime>() {
            Ok(dt.into())
        } else if let Ok(py_str) = self.downcast::<PyString>() {
            let str = py_string_str(py_str)?;
            bytes_as_datetime(self, str.as_bytes())
        } else if let Ok(py_bytes) = self.downcast::<PyBytes>() {
            bytes_as_datetime(self, py_bytes.as_bytes())
        } else if self.downcast::<PyBool>().is_ok() {
            Err(ValError::new(ErrorType::DatetimeType, self))
        } else if let Ok(int) = self.extract::<i64>() {
            int_as_datetime(self, int, 0)
        } else if let Ok(float) = self.extract::<f64>() {
            float_as_datetime(self, float)
        } else if let Ok(date) = self.downcast::<PyDate>() {
            Ok(date_as_datetime(date)?)
        } else {
            Err(ValError::new(ErrorType::DatetimeType, self))
        }
    }

    fn strict_timedelta(&self) -> ValResult<EitherTimedelta> {
        if let Ok(dt) = self.downcast::<PyDelta>() {
            Ok(dt.into())
        } else {
            Err(ValError::new(ErrorType::TimeDeltaType, self))
        }
    }

    fn lax_timedelta(&self) -> ValResult<EitherTimedelta> {
        if let Ok(dt) = self.downcast::<PyDelta>() {
            Ok(dt.into())
        } else if let Ok(py_str) = self.downcast::<PyString>() {
            let str = py_string_str(py_str)?;
            bytes_as_timedelta(self, str.as_bytes())
        } else if let Ok(py_bytes) = self.downcast::<PyBytes>() {
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
    if let Ok(py_string) = v.downcast::<PyString>() {
        let str = py_string_str(py_string)?;
        Ok(Some(Cow::Borrowed(str)))
    } else if let Ok(bytes) = v.downcast::<PyBytes>() {
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
    Ok(obj.downcast::<PyType>()?.into())
}

fn is_builtin_str(py_str: &PyString) -> bool {
    py_str.get_type().is(PyString::type_object(py_str.py()))
}
