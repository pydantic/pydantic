use std::borrow::Cow;
use std::str::from_utf8;

use pyo3::prelude::*;
use pyo3::types::{
    PyBool, PyByteArray, PyBytes, PyDate, PyDateTime, PyDict, PyFloat, PyFrozenSet, PyInt, PyIterator, PyList,
    PyMapping, PySequence, PySet, PyString, PyTime, PyTuple, PyType,
};
#[cfg(not(PyPy))]
use pyo3::types::{PyDictItems, PyDictKeys, PyDictValues};
use pyo3::{intern, AsPyPointer, PyTypeInfo};
use speedate::MicrosecondsPrecisionOverflowBehavior;

use crate::errors::{ErrorType, ErrorTypeDefaults, InputValue, LocItem, ValError, ValResult};
use crate::tools::{extract_i64, safe_repr};
use crate::validators::decimal::create_decimal;
use crate::{ArgsKwargs, PyMultiHostUrl, PyUrl};

use super::datetime::{
    bytes_as_date, bytes_as_datetime, bytes_as_time, bytes_as_timedelta, date_as_datetime, float_as_datetime,
    float_as_duration, float_as_time, int_as_datetime, int_as_duration, int_as_time, EitherDate, EitherDateTime,
    EitherTime,
};
use super::shared::{float_as_int, int_as_bool, map_json_err, str_as_bool, str_as_float, str_as_int};
use super::{
    py_string_str, EitherBytes, EitherFloat, EitherInt, EitherString, EitherTimedelta, GenericArguments,
    GenericIterable, GenericIterator, GenericMapping, Input, JsonInput, PyArgs,
};

#[cfg(not(PyPy))]
macro_rules! extract_dict_keys {
    ($py:expr, $obj:ident) => {
        $obj.downcast::<PyDictKeys>()
            .ok()
            .map(|v| PyIterator::from_object($py, v).unwrap())
    };
}

#[cfg(PyPy)]
macro_rules! extract_dict_keys {
    ($py:expr, $obj:ident) => {
        if is_dict_keys_type($obj) {
            Some(PyIterator::from_object($py, $obj).unwrap())
        } else {
            None
        }
    };
}

#[cfg(not(PyPy))]
macro_rules! extract_dict_values {
    ($py:expr, $obj:ident) => {
        $obj.downcast::<PyDictValues>()
            .ok()
            .map(|v| PyIterator::from_object($py, v).unwrap())
    };
}

#[cfg(PyPy)]
macro_rules! extract_dict_values {
    ($py:expr, $obj:ident) => {
        if is_dict_values_type($obj) {
            Some(PyIterator::from_object($py, $obj).unwrap())
        } else {
            None
        }
    };
}

#[cfg(not(PyPy))]
macro_rules! extract_dict_items {
    ($py:expr, $obj:ident) => {
        $obj.downcast::<PyDictItems>()
            .ok()
            .map(|v| PyIterator::from_object($py, v).unwrap())
    };
}

#[cfg(PyPy)]
macro_rules! extract_dict_items {
    ($py:expr, $obj:ident) => {
        if is_dict_items_type($obj) {
            Some(PyIterator::from_object($py, $obj).unwrap())
        } else {
            None
        }
    };
}

impl<'a> Input<'a> for PyAny {
    fn as_loc_item(&self) -> LocItem {
        if let Ok(py_str) = self.downcast::<PyString>() {
            py_str.to_string_lossy().as_ref().into()
        } else if let Ok(key_int) = extract_i64(self) {
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

    fn input_is_instance(&self, class: &PyType) -> Option<&PyAny> {
        if self.is_instance(class).unwrap_or(false) {
            Some(self)
        } else {
            None
        }
    }

    fn is_python(&self) -> bool {
        true
    }

    fn as_kwargs(&'a self, _py: Python<'a>) -> Option<&'a PyDict> {
        self.downcast::<PyDict>().ok()
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
            Ok(PyArgs::new(None, Some(dict)).into())
        } else if let Ok(args_kwargs) = self.extract::<ArgsKwargs>() {
            let args = args_kwargs.args.into_ref(self.py());
            let kwargs = args_kwargs.kwargs.map(|d| d.into_ref(self.py()));
            Ok(PyArgs::new(Some(args), kwargs).into())
        } else if let Ok(tuple) = self.downcast::<PyTuple>() {
            Ok(PyArgs::new(Some(tuple), None).into())
        } else if let Ok(list) = self.downcast::<PyList>() {
            Ok(PyArgs::new(Some(list.to_tuple()), None).into())
        } else {
            Err(ValError::new(ErrorTypeDefaults::ArgumentsType, self))
        }
    }

    fn validate_dataclass_args(&'a self, class_name: &str) -> ValResult<'a, GenericArguments<'a>> {
        if let Ok(dict) = self.downcast::<PyDict>() {
            Ok(PyArgs::new(None, Some(dict)).into())
        } else if let Ok(args_kwargs) = self.extract::<ArgsKwargs>() {
            let args = args_kwargs.args.into_ref(self.py());
            let kwargs = args_kwargs.kwargs.map(|d| d.into_ref(self.py()));
            Ok(PyArgs::new(Some(args), kwargs).into())
        } else {
            let class_name = class_name.to_string();
            Err(ValError::new(
                ErrorType::DataclassType {
                    class_name,
                    context: None,
                },
                self,
            ))
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
            Err(ValError::new(ErrorTypeDefaults::JsonType, self))
        }
    }

    fn strict_str(&'a self) -> ValResult<EitherString<'a>> {
        if let Ok(py_str) = <PyString as PyTryFrom>::try_from_exact(self) {
            Ok(py_str.into())
        } else if let Ok(py_str) = self.downcast::<PyString>() {
            // force to a rust string to make sure behavior is consistent whether or not we go via a
            // rust string in StrConstrainedValidator - e.g. to_lower
            Ok(py_string_str(py_str)?.into())
        } else {
            Err(ValError::new(ErrorTypeDefaults::StringType, self))
        }
    }

    fn exact_str(&'a self) -> ValResult<EitherString<'a>> {
        if let Ok(py_str) = <PyString as PyTryFrom>::try_from_exact(self) {
            Ok(EitherString::Py(py_str))
        } else {
            Err(ValError::new(ErrorTypeDefaults::IntType, self))
        }
    }

    fn exact_int(&'a self) -> ValResult<EitherInt<'a>> {
        if PyInt::is_exact_type_of(self) {
            Ok(EitherInt::Py(self))
        } else {
            Err(ValError::new(ErrorTypeDefaults::IntType, self))
        }
    }

    fn lax_str(&'a self) -> ValResult<EitherString<'a>> {
        if let Ok(py_str) = <PyString as PyTryFrom>::try_from_exact(self) {
            Ok(py_str.into())
        } else if let Ok(py_str) = self.downcast::<PyString>() {
            // force to a rust string to make sure behaviour is consistent whether or not we go via a
            // rust string in StrConstrainedValidator - e.g. to_lower
            Ok(py_string_str(py_str)?.into())
        } else if let Ok(bytes) = self.downcast::<PyBytes>() {
            let str = match from_utf8(bytes.as_bytes()) {
                Ok(s) => s,
                Err(_) => return Err(ValError::new(ErrorTypeDefaults::StringUnicode, self)),
            };
            Ok(str.into())
        } else if let Ok(py_byte_array) = self.downcast::<PyByteArray>() {
            // see https://docs.rs/pyo3/latest/pyo3/types/struct.PyByteArray.html#method.as_bytes
            // for why this is marked unsafe
            let str = match from_utf8(unsafe { py_byte_array.as_bytes() }) {
                Ok(s) => s,
                Err(_) => return Err(ValError::new(ErrorTypeDefaults::StringUnicode, self)),
            };
            Ok(str.into())
        } else {
            Err(ValError::new(ErrorTypeDefaults::StringType, self))
        }
    }

    fn strict_bytes(&'a self) -> ValResult<EitherBytes<'a>> {
        if let Ok(py_bytes) = self.downcast::<PyBytes>() {
            Ok(py_bytes.into())
        } else {
            Err(ValError::new(ErrorTypeDefaults::BytesType, self))
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
            Err(ValError::new(ErrorTypeDefaults::BytesType, self))
        }
    }

    fn strict_bool(&self) -> ValResult<bool> {
        if let Ok(bool) = self.downcast::<PyBool>() {
            Ok(bool.is_true())
        } else {
            Err(ValError::new(ErrorTypeDefaults::BoolType, self))
        }
    }

    fn lax_bool(&self) -> ValResult<bool> {
        if let Ok(bool) = self.downcast::<PyBool>() {
            Ok(bool.is_true())
        } else if let Some(cow_str) = maybe_as_string(self, ErrorTypeDefaults::BoolParsing)? {
            str_as_bool(self, &cow_str)
        } else if let Ok(int) = extract_i64(self) {
            int_as_bool(self, int)
        } else if let Ok(float) = self.extract::<f64>() {
            match float_as_int(self, float) {
                Ok(int) => int
                    .as_bool()
                    .ok_or_else(|| ValError::new(ErrorTypeDefaults::BoolParsing, self)),
                _ => Err(ValError::new(ErrorTypeDefaults::BoolType, self)),
            }
        } else {
            Err(ValError::new(ErrorTypeDefaults::BoolType, self))
        }
    }

    fn strict_int(&'a self) -> ValResult<EitherInt<'a>> {
        if PyInt::is_exact_type_of(self) {
            Ok(EitherInt::Py(self))
        } else if PyInt::is_type_of(self) {
            // bools are a subclass of int, so check for bool type in this specific case
            if PyBool::is_exact_type_of(self) {
                Err(ValError::new(ErrorTypeDefaults::IntType, self))
            } else {
                // force to an int to upcast to a pure python int
                EitherInt::upcast(self)
            }
        } else {
            Err(ValError::new(ErrorTypeDefaults::IntType, self))
        }
    }

    fn lax_int(&'a self) -> ValResult<EitherInt<'a>> {
        if PyInt::is_exact_type_of(self) {
            Ok(EitherInt::Py(self))
        } else if let Some(cow_str) = maybe_as_string(self, ErrorTypeDefaults::IntParsing)? {
            // Try strings before subclasses of int as that will be far more common
            str_as_int(self, &cow_str)
        } else if PyInt::is_type_of(self) {
            // force to an int to upcast to a pure python int to maintain current behaviour
            EitherInt::upcast(self)
        } else if let Ok(float) = self.extract::<f64>() {
            float_as_int(self, float)
        } else {
            Err(ValError::new(ErrorTypeDefaults::IntType, self))
        }
    }

    fn ultra_strict_float(&'a self) -> ValResult<EitherFloat<'a>> {
        if self.is_instance_of::<PyInt>() {
            Err(ValError::new(ErrorTypeDefaults::FloatType, self))
        } else if let Ok(float) = self.downcast::<PyFloat>() {
            Ok(EitherFloat::Py(float))
        } else {
            Err(ValError::new(ErrorTypeDefaults::FloatType, self))
        }
    }
    fn strict_float(&'a self) -> ValResult<EitherFloat<'a>> {
        if PyFloat::is_exact_type_of(self) {
            // Safety: self is PyFloat
            Ok(EitherFloat::Py(unsafe { self.downcast_unchecked::<PyFloat>() }))
        } else if let Ok(float) = self.extract::<f64>() {
            // bools are cast to floats as either 0.0 or 1.0, so check for bool type in this specific case
            if (float == 0.0 || float == 1.0) && PyBool::is_exact_type_of(self) {
                Err(ValError::new(ErrorTypeDefaults::FloatType, self))
            } else {
                Ok(EitherFloat::F64(float))
            }
        } else {
            Err(ValError::new(ErrorTypeDefaults::FloatType, self))
        }
    }

    fn lax_float(&'a self) -> ValResult<EitherFloat<'a>> {
        if PyFloat::is_exact_type_of(self) {
            // Safety: self is PyFloat
            Ok(EitherFloat::Py(unsafe { self.downcast_unchecked::<PyFloat>() }))
        } else if let Some(cow_str) = maybe_as_string(self, ErrorTypeDefaults::FloatParsing)? {
            str_as_float(self, &cow_str)
        } else if let Ok(float) = self.extract::<f64>() {
            Ok(EitherFloat::F64(float))
        } else {
            Err(ValError::new(ErrorTypeDefaults::FloatType, self))
        }
    }

    fn strict_decimal(&'a self, decimal_type: &'a PyType) -> ValResult<&'a PyAny> {
        // Fast path for existing decimal objects
        if self.is_exact_instance(decimal_type) {
            return Ok(self);
        }

        // Try subclasses of decimals, they will be upcast to Decimal
        if self.is_instance(decimal_type)? {
            return create_decimal(self, self, decimal_type);
        }

        Err(ValError::new(
            ErrorType::IsInstanceOf {
                class: decimal_type.name().unwrap_or("Decimal").to_string(),
                context: None,
            },
            self,
        ))
    }

    fn lax_decimal(&'a self, decimal_type: &'a PyType) -> ValResult<&'a PyAny> {
        // Fast path for existing decimal objects
        if self.is_exact_instance(decimal_type) {
            return Ok(self);
        }

        if self.is_instance_of::<PyString>() || (self.is_instance_of::<PyInt>() && !self.is_instance_of::<PyBool>()) {
            // checking isinstance for str / int / bool is fast compared to decimal / float
            create_decimal(self, self, decimal_type)
        } else if self.is_instance(decimal_type)? {
            // upcast subclasses to decimal
            return create_decimal(self, self, decimal_type);
        } else if self.is_instance_of::<PyFloat>() {
            create_decimal(self.str()?, self, decimal_type)
        } else {
            Err(ValError::new(ErrorTypeDefaults::DecimalType, self))
        }
    }

    fn strict_dict(&'a self) -> ValResult<GenericMapping<'a>> {
        if let Ok(dict) = self.downcast::<PyDict>() {
            Ok(dict.into())
        } else {
            Err(ValError::new(ErrorTypeDefaults::DictType, self))
        }
    }

    fn lax_dict(&'a self) -> ValResult<GenericMapping<'a>> {
        if let Ok(dict) = self.downcast::<PyDict>() {
            Ok(dict.into())
        } else if let Ok(mapping) = self.downcast::<PyMapping>() {
            Ok(mapping.into())
        } else {
            Err(ValError::new(ErrorTypeDefaults::DictType, self))
        }
    }

    fn validate_model_fields(&'a self, strict: bool, from_attributes: bool) -> ValResult<GenericMapping<'a>> {
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
                    Err(ValError::new(ErrorTypeDefaults::ModelAttributesType, self))
                }
            } else {
                // note the error here gives a hint about from_attributes
                Err(ValError::new(ErrorTypeDefaults::ModelAttributesType, self))
            }
        } else {
            // otherwise we just call back to validate_dict if from_mapping is allowed, note that errors in this
            // case (correctly) won't hint about from_attributes
            self.validate_dict(strict)
        }
    }

    fn strict_list(&'a self) -> ValResult<GenericIterable<'a>> {
        match self.lax_list()? {
            GenericIterable::List(iter) => Ok(GenericIterable::List(iter)),
            _ => Err(ValError::new(ErrorTypeDefaults::ListType, self)),
        }
    }

    fn lax_list(&'a self) -> ValResult<GenericIterable<'a>> {
        match self
            .extract_generic_iterable()
            .map_err(|_| ValError::new(ErrorTypeDefaults::ListType, self))?
        {
            GenericIterable::PyString(_)
            | GenericIterable::Bytes(_)
            | GenericIterable::Dict(_)
            | GenericIterable::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::ListType, self)),
            other => Ok(other),
        }
    }

    fn strict_tuple(&'a self) -> ValResult<GenericIterable<'a>> {
        match self.lax_tuple()? {
            GenericIterable::Tuple(iter) => Ok(GenericIterable::Tuple(iter)),
            _ => Err(ValError::new(ErrorTypeDefaults::TupleType, self)),
        }
    }

    fn lax_tuple(&'a self) -> ValResult<GenericIterable<'a>> {
        match self
            .extract_generic_iterable()
            .map_err(|_| ValError::new(ErrorTypeDefaults::TupleType, self))?
        {
            GenericIterable::PyString(_)
            | GenericIterable::Bytes(_)
            | GenericIterable::Dict(_)
            | GenericIterable::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::TupleType, self)),
            other => Ok(other),
        }
    }

    fn strict_set(&'a self) -> ValResult<GenericIterable<'a>> {
        match self.lax_set()? {
            GenericIterable::Set(iter) => Ok(GenericIterable::Set(iter)),
            _ => Err(ValError::new(ErrorTypeDefaults::SetType, self)),
        }
    }

    fn lax_set(&'a self) -> ValResult<GenericIterable<'a>> {
        match self
            .extract_generic_iterable()
            .map_err(|_| ValError::new(ErrorTypeDefaults::SetType, self))?
        {
            GenericIterable::PyString(_)
            | GenericIterable::Bytes(_)
            | GenericIterable::Dict(_)
            | GenericIterable::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::SetType, self)),
            other => Ok(other),
        }
    }

    fn strict_frozenset(&'a self) -> ValResult<GenericIterable<'a>> {
        match self.lax_frozenset()? {
            GenericIterable::FrozenSet(iter) => Ok(GenericIterable::FrozenSet(iter)),
            _ => Err(ValError::new(ErrorTypeDefaults::FrozenSetType, self)),
        }
    }

    fn lax_frozenset(&'a self) -> ValResult<GenericIterable<'a>> {
        match self
            .extract_generic_iterable()
            .map_err(|_| ValError::new(ErrorTypeDefaults::FrozenSetType, self))?
        {
            GenericIterable::PyString(_)
            | GenericIterable::Bytes(_)
            | GenericIterable::Dict(_)
            | GenericIterable::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::FrozenSetType, self)),
            other => Ok(other),
        }
    }

    fn extract_generic_iterable(&'a self) -> ValResult<GenericIterable<'a>> {
        // Handle concrete non-overlapping types first, then abstract types
        if let Ok(iterable) = self.downcast::<PyList>() {
            Ok(GenericIterable::List(iterable))
        } else if let Ok(iterable) = self.downcast::<PyTuple>() {
            Ok(GenericIterable::Tuple(iterable))
        } else if let Ok(iterable) = self.downcast::<PySet>() {
            Ok(GenericIterable::Set(iterable))
        } else if let Ok(iterable) = self.downcast::<PyFrozenSet>() {
            Ok(GenericIterable::FrozenSet(iterable))
        } else if let Ok(iterable) = self.downcast::<PyDict>() {
            Ok(GenericIterable::Dict(iterable))
        } else if let Some(iterable) = extract_dict_keys!(self.py(), self) {
            Ok(GenericIterable::DictKeys(iterable))
        } else if let Some(iterable) = extract_dict_values!(self.py(), self) {
            Ok(GenericIterable::DictValues(iterable))
        } else if let Some(iterable) = extract_dict_items!(self.py(), self) {
            Ok(GenericIterable::DictItems(iterable))
        } else if let Ok(iterable) = self.downcast::<PyMapping>() {
            Ok(GenericIterable::Mapping(iterable))
        } else if let Ok(iterable) = self.downcast::<PyString>() {
            Ok(GenericIterable::PyString(iterable))
        } else if let Ok(iterable) = self.downcast::<PyBytes>() {
            Ok(GenericIterable::Bytes(iterable))
        } else if let Ok(iterable) = self.downcast::<PyByteArray>() {
            Ok(GenericIterable::PyByteArray(iterable))
        } else if let Ok(iterable) = self.downcast::<PySequence>() {
            Ok(GenericIterable::Sequence(iterable))
        } else if let Ok(iterable) = self.iter() {
            Ok(GenericIterable::Iterator(iterable))
        } else {
            Err(ValError::new(ErrorTypeDefaults::IterableType, self))
        }
    }

    fn validate_iter(&self) -> ValResult<GenericIterator> {
        if self.iter().is_ok() {
            Ok(self.into())
        } else {
            Err(ValError::new(ErrorTypeDefaults::IterableType, self))
        }
    }

    fn strict_date(&self) -> ValResult<EitherDate> {
        if PyDateTime::is_type_of(self) {
            // have to check if it's a datetime first, otherwise the line below converts to a date
            Err(ValError::new(ErrorTypeDefaults::DateType, self))
        } else if let Ok(date) = self.downcast::<PyDate>() {
            Ok(date.into())
        } else {
            Err(ValError::new(ErrorTypeDefaults::DateType, self))
        }
    }

    fn lax_date(&self) -> ValResult<EitherDate> {
        if PyDateTime::is_type_of(self) {
            // have to check if it's a datetime first, otherwise the line below converts to a date
            // even if we later try coercion from a datetime, we don't want to return a datetime now
            Err(ValError::new(ErrorTypeDefaults::DateType, self))
        } else if let Ok(date) = self.downcast::<PyDate>() {
            Ok(date.into())
        } else if let Ok(py_str) = self.downcast::<PyString>() {
            let str = py_string_str(py_str)?;
            bytes_as_date(self, str.as_bytes())
        } else if let Ok(py_bytes) = self.downcast::<PyBytes>() {
            bytes_as_date(self, py_bytes.as_bytes())
        } else {
            Err(ValError::new(ErrorTypeDefaults::DateType, self))
        }
    }

    fn strict_time(
        &self,
        _microseconds_overflow_behavior: MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<EitherTime> {
        if let Ok(time) = self.downcast::<PyTime>() {
            Ok(time.into())
        } else {
            Err(ValError::new(ErrorTypeDefaults::TimeType, self))
        }
    }

    fn lax_time(&self, microseconds_overflow_behavior: MicrosecondsPrecisionOverflowBehavior) -> ValResult<EitherTime> {
        if let Ok(time) = self.downcast::<PyTime>() {
            Ok(time.into())
        } else if let Ok(py_str) = self.downcast::<PyString>() {
            let str = py_string_str(py_str)?;
            bytes_as_time(self, str.as_bytes(), microseconds_overflow_behavior)
        } else if let Ok(py_bytes) = self.downcast::<PyBytes>() {
            bytes_as_time(self, py_bytes.as_bytes(), microseconds_overflow_behavior)
        } else if PyBool::is_exact_type_of(self) {
            Err(ValError::new(ErrorTypeDefaults::TimeType, self))
        } else if let Ok(int) = extract_i64(self) {
            int_as_time(self, int, 0)
        } else if let Ok(float) = self.extract::<f64>() {
            float_as_time(self, float)
        } else {
            Err(ValError::new(ErrorTypeDefaults::TimeType, self))
        }
    }

    fn strict_datetime(
        &self,
        _microseconds_overflow_behavior: MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<EitherDateTime> {
        if let Ok(dt) = self.downcast::<PyDateTime>() {
            Ok(dt.into())
        } else {
            Err(ValError::new(ErrorTypeDefaults::DatetimeType, self))
        }
    }

    fn lax_datetime(
        &self,
        microseconds_overflow_behavior: MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<EitherDateTime> {
        if let Ok(dt) = self.downcast::<PyDateTime>() {
            Ok(dt.into())
        } else if let Ok(py_str) = self.downcast::<PyString>() {
            let str = py_string_str(py_str)?;
            bytes_as_datetime(self, str.as_bytes(), microseconds_overflow_behavior)
        } else if let Ok(py_bytes) = self.downcast::<PyBytes>() {
            bytes_as_datetime(self, py_bytes.as_bytes(), microseconds_overflow_behavior)
        } else if PyBool::is_exact_type_of(self) {
            Err(ValError::new(ErrorTypeDefaults::DatetimeType, self))
        } else if let Ok(int) = extract_i64(self) {
            int_as_datetime(self, int, 0)
        } else if let Ok(float) = self.extract::<f64>() {
            float_as_datetime(self, float)
        } else if let Ok(date) = self.downcast::<PyDate>() {
            Ok(date_as_datetime(date)?)
        } else {
            Err(ValError::new(ErrorTypeDefaults::DatetimeType, self))
        }
    }

    fn strict_timedelta(
        &self,
        _microseconds_overflow_behavior: MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<EitherTimedelta> {
        if let Ok(either_dt) = EitherTimedelta::try_from(self) {
            Ok(either_dt)
        } else {
            Err(ValError::new(ErrorTypeDefaults::TimeDeltaType, self))
        }
    }

    fn lax_timedelta(
        &self,
        microseconds_overflow_behavior: MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<EitherTimedelta> {
        if let Ok(either_dt) = EitherTimedelta::try_from(self) {
            Ok(either_dt)
        } else if let Ok(py_str) = self.downcast::<PyString>() {
            let str = py_string_str(py_str)?;
            bytes_as_timedelta(self, str.as_bytes(), microseconds_overflow_behavior)
        } else if let Ok(py_bytes) = self.downcast::<PyBytes>() {
            bytes_as_timedelta(self, py_bytes.as_bytes(), microseconds_overflow_behavior)
        } else if let Ok(int) = extract_i64(self) {
            Ok(int_as_duration(self, int)?.into())
        } else if let Ok(float) = self.extract::<f64>() {
            Ok(float_as_duration(self, float)?.into())
        } else {
            Err(ValError::new(ErrorTypeDefaults::TimeDeltaType, self))
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

#[cfg(PyPy)]
static DICT_KEYS_TYPE: pyo3::once_cell::GILOnceCell<Py<PyType>> = pyo3::once_cell::GILOnceCell::new();

#[cfg(PyPy)]
fn is_dict_keys_type(v: &PyAny) -> bool {
    let py = v.py();
    let keys_type = DICT_KEYS_TYPE
        .get_or_init(py, || {
            py.eval("type({}.keys())", None, None)
                .unwrap()
                .extract::<&PyType>()
                .unwrap()
                .into()
        })
        .as_ref(py);
    v.is_instance(keys_type).unwrap_or(false)
}

#[cfg(PyPy)]
static DICT_VALUES_TYPE: pyo3::once_cell::GILOnceCell<Py<PyType>> = pyo3::once_cell::GILOnceCell::new();

#[cfg(PyPy)]
fn is_dict_values_type(v: &PyAny) -> bool {
    let py = v.py();
    let values_type = DICT_VALUES_TYPE
        .get_or_init(py, || {
            py.eval("type({}.values())", None, None)
                .unwrap()
                .extract::<&PyType>()
                .unwrap()
                .into()
        })
        .as_ref(py);
    v.is_instance(values_type).unwrap_or(false)
}

#[cfg(PyPy)]
static DICT_ITEMS_TYPE: pyo3::once_cell::GILOnceCell<Py<PyType>> = pyo3::once_cell::GILOnceCell::new();

#[cfg(PyPy)]
fn is_dict_items_type(v: &PyAny) -> bool {
    let py = v.py();
    let items_type = DICT_ITEMS_TYPE
        .get_or_init(py, || {
            py.eval("type({}.items())", None, None)
                .unwrap()
                .extract::<&PyType>()
                .unwrap()
                .into()
        })
        .as_ref(py);
    v.is_instance(items_type).unwrap_or(false)
}
