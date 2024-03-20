use std::borrow::Cow;
use std::str::from_utf8;

use pyo3::intern;
use pyo3::prelude::*;

use pyo3::types::{
    PyBool, PyByteArray, PyBytes, PyDate, PyDateTime, PyDict, PyFloat, PyFrozenSet, PyInt, PyIterator, PyList,
    PyMapping, PySet, PyString, PyTime, PyTuple, PyType,
};

use speedate::MicrosecondsPrecisionOverflowBehavior;

use crate::errors::{ErrorType, ErrorTypeDefaults, InputValue, LocItem, ValError, ValResult};
use crate::tools::{extract_i64, safe_repr};
use crate::validators::decimal::{create_decimal, get_decimal_type};
use crate::validators::Exactness;
use crate::{ArgsKwargs, PyMultiHostUrl, PyUrl};

use super::datetime::{
    bytes_as_date, bytes_as_datetime, bytes_as_time, bytes_as_timedelta, date_as_datetime, float_as_datetime,
    float_as_duration, float_as_time, int_as_datetime, int_as_duration, int_as_time, EitherDate, EitherDateTime,
    EitherTime,
};
use super::input_abstract::ValMatch;
use super::return_enums::{iterate_attributes, iterate_mapping_items, ValidationMatch};
use super::shared::{
    decimal_as_int, float_as_int, get_enum_meta_object, int_as_bool, str_as_bool, str_as_float, str_as_int,
};
use super::Arguments;
use super::ConsumeIterator;
use super::KeywordArgs;
use super::PositionalArgs;
use super::ValidatedDict;
use super::ValidatedList;
use super::ValidatedSet;
use super::ValidatedTuple;
use super::{
    py_string_str, BorrowInput, EitherBytes, EitherFloat, EitherInt, EitherString, EitherTimedelta, GenericIterator,
    Input,
};

impl From<&Bound<'_, PyAny>> for LocItem {
    fn from(py_any: &Bound<'_, PyAny>) -> Self {
        if let Ok(py_str) = py_any.downcast::<PyString>() {
            py_str.to_string_lossy().as_ref().into()
        } else if let Some(key_int) = extract_i64(py_any) {
            key_int.into()
        } else {
            safe_repr(py_any).to_string().into()
        }
    }
}

impl From<Bound<'_, PyAny>> for LocItem {
    fn from(py_any: Bound<'_, PyAny>) -> Self {
        (&py_any).into()
    }
}

impl<'py> Input<'py> for Bound<'py, PyAny> {
    fn as_error_value(&self) -> InputValue {
        InputValue::Python(self.clone().into())
    }

    fn identity(&self) -> Option<usize> {
        Some(self.as_ptr() as usize)
    }

    fn is_none(&self) -> bool {
        PyAnyMethods::is_none(self)
    }

    fn input_is_instance(&self, class: &Bound<'py, PyType>) -> Option<&Bound<'py, PyAny>> {
        if self.is_instance(class).unwrap_or(false) {
            Some(self)
        } else {
            None
        }
    }

    fn input_is_exact_instance(&self, class: &Bound<'py, PyType>) -> bool {
        self.is_exact_instance(class)
    }

    fn is_python(&self) -> bool {
        true
    }

    fn as_kwargs(&self, py: Python<'py>) -> Option<Bound<'py, PyDict>> {
        self.downcast::<PyDict>()
            .ok()
            .map(|dict| dict.to_owned().unbind().into_bound(py))
    }

    fn input_is_subclass(&self, class: &Bound<'_, PyType>) -> PyResult<bool> {
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

    type Arguments<'a> = PyArgs<'py> where Self: 'a;

    fn validate_args(&self) -> ValResult<PyArgs<'py>> {
        if let Ok(dict) = self.downcast::<PyDict>() {
            Ok(PyArgs::new(None, Some(dict.clone())))
        } else if let Ok(args_kwargs) = self.extract::<ArgsKwargs>() {
            let args = args_kwargs.args.into_bound(self.py());
            let kwargs = args_kwargs.kwargs.map(|d| d.into_bound(self.py()));
            Ok(PyArgs::new(Some(args), kwargs))
        } else if let Ok(tuple) = self.downcast::<PyTuple>() {
            Ok(PyArgs::new(Some(tuple.clone()), None))
        } else if let Ok(list) = self.downcast::<PyList>() {
            Ok(PyArgs::new(Some(list.to_tuple()), None))
        } else {
            Err(ValError::new(ErrorTypeDefaults::ArgumentsType, self))
        }
    }

    fn validate_dataclass_args<'a>(&'a self, class_name: &str) -> ValResult<PyArgs<'py>> {
        if let Ok(dict) = self.downcast::<PyDict>() {
            Ok(PyArgs::new(None, Some(dict.clone())))
        } else if let Ok(args_kwargs) = self.extract::<ArgsKwargs>() {
            let args = args_kwargs.args.into_bound(self.py());
            let kwargs = args_kwargs.kwargs.map(|d| d.into_bound(self.py()));
            Ok(PyArgs::new(Some(args), kwargs))
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

    fn validate_str(&self, strict: bool, coerce_numbers_to_str: bool) -> ValResult<ValidationMatch<EitherString<'_>>> {
        if let Ok(py_str) = self.downcast_exact::<PyString>() {
            return Ok(ValidationMatch::exact(py_str.clone().into()));
        } else if let Ok(py_str) = self.downcast::<PyString>() {
            // force to a rust string to make sure behavior is consistent whether or not we go via a
            // rust string in StrConstrainedValidator - e.g. to_lower
            return Ok(ValidationMatch::strict(py_string_str(py_str)?.into()));
        }

        'lax: {
            if !strict {
                return if let Ok(bytes) = self.downcast::<PyBytes>() {
                    match from_utf8(bytes.as_bytes()) {
                        Ok(str) => Ok(str.into()),
                        Err(_) => Err(ValError::new(ErrorTypeDefaults::StringUnicode, self)),
                    }
                } else if let Ok(py_byte_array) = self.downcast::<PyByteArray>() {
                    // Safety: the gil is held while from_utf8 is running so py_byte_array is not mutated,
                    // and we immediately copy the bytes into a new Python string
                    match from_utf8(unsafe { py_byte_array.as_bytes() }) {
                        // Why Python not Rust? to avoid an unnecessary allocation on the Rust side, the
                        // final output needs to be Python anyway.
                        Ok(s) => Ok(PyString::new_bound(self.py(), s).into()),
                        Err(_) => Err(ValError::new(ErrorTypeDefaults::StringUnicode, self)),
                    }
                } else if coerce_numbers_to_str && !self.is_exact_instance_of::<PyBool>() && {
                    let py = self.py();
                    let decimal_type = get_decimal_type(py);

                    // only allow int, float, and decimal (not bool)
                    self.is_instance_of::<PyInt>()
                        || self.is_instance_of::<PyFloat>()
                        || self.is_instance(decimal_type).unwrap_or_default()
                } {
                    Ok(self.str()?.into())
                } else if let Some(enum_val) = maybe_as_enum(self) {
                    Ok(enum_val.str()?.into())
                } else {
                    break 'lax;
                }
                .map(ValidationMatch::lax);
            }
        }

        Err(ValError::new(ErrorTypeDefaults::StringType, self))
    }

    fn validate_bytes<'a>(&'a self, strict: bool) -> ValResult<ValidationMatch<EitherBytes<'a, 'py>>> {
        if let Ok(py_bytes) = self.downcast_exact::<PyBytes>() {
            return Ok(ValidationMatch::exact(py_bytes.into()));
        } else if let Ok(py_bytes) = self.downcast::<PyBytes>() {
            return Ok(ValidationMatch::strict(py_bytes.into()));
        }

        'lax: {
            if !strict {
                return if let Ok(py_str) = self.downcast::<PyString>() {
                    let str = py_string_str(py_str)?;
                    Ok(str.as_bytes().into())
                } else if let Ok(py_byte_array) = self.downcast::<PyByteArray>() {
                    Ok(py_byte_array.to_vec().into())
                } else {
                    break 'lax;
                }
                .map(ValidationMatch::lax);
            }
        }

        Err(ValError::new(ErrorTypeDefaults::BytesType, self))
    }

    fn validate_bool(&self, strict: bool) -> ValResult<ValidationMatch<bool>> {
        if let Ok(bool) = self.downcast::<PyBool>() {
            return Ok(ValidationMatch::exact(bool.is_true()));
        }

        if !strict {
            if let Some(cow_str) = maybe_as_string(self, ErrorTypeDefaults::BoolParsing)? {
                return str_as_bool(self, &cow_str).map(ValidationMatch::lax);
            } else if let Some(int) = extract_i64(self) {
                return int_as_bool(self, int).map(ValidationMatch::lax);
            } else if let Ok(float) = self.extract::<f64>() {
                if let Ok(int) = float_as_int(self, float) {
                    return int
                        .as_bool()
                        .ok_or_else(|| ValError::new(ErrorTypeDefaults::BoolParsing, self))
                        .map(ValidationMatch::lax);
                };
            }
        }

        Err(ValError::new(ErrorTypeDefaults::BoolType, self))
    }

    fn validate_int(&self, strict: bool) -> ValResult<ValidationMatch<EitherInt<'_>>> {
        if self.is_exact_instance_of::<PyInt>() {
            return Ok(ValidationMatch::exact(EitherInt::Py(self.clone())));
        } else if self.is_instance_of::<PyInt>() {
            // bools are a subclass of int, so check for bool type in this specific case
            let exactness = if self.is_instance_of::<PyBool>() {
                if strict {
                    return Err(ValError::new(ErrorTypeDefaults::IntType, self));
                }
                Exactness::Lax
            } else {
                Exactness::Strict
            };

            // force to an int to upcast to a pure python int
            return EitherInt::upcast(self).map(|either_int| ValidationMatch::new(either_int, exactness));
        }

        'lax: {
            if !strict {
                return if let Some(cow_str) = maybe_as_string(self, ErrorTypeDefaults::IntParsing)? {
                    str_as_int(self, &cow_str)
                } else if self.is_exact_instance_of::<PyFloat>() {
                    float_as_int(self, self.extract::<f64>()?)
                } else if let Ok(decimal) = self.strict_decimal(self.py()) {
                    decimal_as_int(self, &decimal)
                } else if let Ok(float) = self.extract::<f64>() {
                    float_as_int(self, float)
                } else if let Some(enum_val) = maybe_as_enum(self) {
                    Ok(EitherInt::Py(enum_val))
                } else {
                    break 'lax;
                }
                .map(ValidationMatch::lax);
            }
        }

        Err(ValError::new(ErrorTypeDefaults::IntType, self))
    }

    fn exact_int(&self) -> ValResult<EitherInt<'_>> {
        if self.is_exact_instance_of::<PyInt>() {
            Ok(EitherInt::Py(self.clone()))
        } else {
            Err(ValError::new(ErrorTypeDefaults::IntType, self))
        }
    }

    fn exact_str(&self) -> ValResult<EitherString<'_>> {
        if let Ok(py_str) = self.downcast_exact() {
            Ok(EitherString::Py(py_str.clone()))
        } else {
            Err(ValError::new(ErrorTypeDefaults::IntType, self))
        }
    }

    fn validate_float(&self, strict: bool) -> ValResult<ValidationMatch<EitherFloat<'_>>> {
        if let Ok(float) = self.downcast_exact::<PyFloat>() {
            return Ok(ValidationMatch::exact(EitherFloat::Py(float.clone())));
        }

        if !strict {
            if let Some(cow_str) = maybe_as_string(self, ErrorTypeDefaults::FloatParsing)? {
                // checking for bytes and string is fast, so do this before isinstance(float)
                return str_as_float(self, &cow_str).map(ValidationMatch::lax);
            }
        }

        if let Ok(float) = self.extract::<f64>() {
            let exactness = if self.is_instance_of::<PyBool>() {
                if strict {
                    return Err(ValError::new(ErrorTypeDefaults::FloatType, self));
                }
                Exactness::Lax
            } else {
                Exactness::Strict
            };
            return Ok(ValidationMatch::new(EitherFloat::F64(float), exactness));
        }

        Err(ValError::new(ErrorTypeDefaults::FloatType, self))
    }

    fn strict_decimal(&self, py: Python<'py>) -> ValResult<Bound<'py, PyAny>> {
        let decimal_type = get_decimal_type(py);
        // Fast path for existing decimal objects
        if self.is_exact_instance(decimal_type) {
            return Ok(self.to_owned());
        }

        // Try subclasses of decimals, they will be upcast to Decimal
        if self.is_instance(decimal_type)? {
            return create_decimal(self, self);
        }

        Err(ValError::new(
            ErrorType::IsInstanceOf {
                class: decimal_type.qualname().unwrap_or_else(|_| "Decimal".to_owned()),
                context: None,
            },
            self,
        ))
    }

    fn lax_decimal(&self, py: Python<'py>) -> ValResult<Bound<'py, PyAny>> {
        let decimal_type = get_decimal_type(py);
        // Fast path for existing decimal objects
        if self.is_exact_instance(decimal_type) {
            return Ok(self.to_owned().clone());
        }

        if self.is_instance_of::<PyString>() || (self.is_instance_of::<PyInt>() && !self.is_instance_of::<PyBool>()) {
            // checking isinstance for str / int / bool is fast compared to decimal / float
            create_decimal(self, self)
        } else if self.is_instance(decimal_type)? {
            // upcast subclasses to decimal
            return create_decimal(self, self);
        } else if self.is_instance_of::<PyFloat>() {
            create_decimal(self.str()?.as_any(), self)
        } else {
            Err(ValError::new(ErrorTypeDefaults::DecimalType, self))
        }
    }

    type Dict<'a> = GenericPyMapping<'a, 'py> where Self: 'a;

    fn strict_dict<'a>(&'a self) -> ValResult<GenericPyMapping<'a, 'py>> {
        if let Ok(dict) = self.downcast::<PyDict>() {
            Ok(GenericPyMapping::Dict(dict))
        } else {
            Err(ValError::new(ErrorTypeDefaults::DictType, self))
        }
    }

    fn lax_dict<'a>(&'a self) -> ValResult<GenericPyMapping<'a, 'py>> {
        if let Ok(dict) = self.downcast::<PyDict>() {
            Ok(GenericPyMapping::Dict(dict))
        } else if let Ok(mapping) = self.downcast::<PyMapping>() {
            Ok(GenericPyMapping::Mapping(mapping))
        } else {
            Err(ValError::new(ErrorTypeDefaults::DictType, self))
        }
    }

    fn validate_model_fields<'a>(
        &'a self,
        strict: bool,
        from_attributes: bool,
    ) -> ValResult<GenericPyMapping<'a, 'py>> {
        if from_attributes {
            // if from_attributes, first try a dict, then mapping then from_attributes
            if let Ok(dict) = self.downcast::<PyDict>() {
                return Ok(GenericPyMapping::Dict(dict));
            } else if !strict {
                if let Ok(mapping) = self.downcast::<PyMapping>() {
                    return Ok(GenericPyMapping::Mapping(mapping));
                }
            }

            if from_attributes_applicable(self) {
                Ok(GenericPyMapping::GetAttr(self.to_owned(), None))
            } else if let Ok((obj, kwargs)) = self.extract() {
                if from_attributes_applicable(&obj) {
                    Ok(GenericPyMapping::GetAttr(obj, Some(kwargs)))
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

    type List<'a> = PySequenceIterable<'a, 'py> where Self: 'a;

    fn validate_list<'a>(&'a self, strict: bool) -> ValMatch<PySequenceIterable<'a, 'py>> {
        if let Ok(list) = self.downcast::<PyList>() {
            return Ok(ValidationMatch::exact(PySequenceIterable::List(list)));
        } else if !strict {
            if let Ok(other) = extract_sequence_iterable(self) {
                return Ok(ValidationMatch::lax(other));
            }
        }

        Err(ValError::new(ErrorTypeDefaults::ListType, self))
    }

    type Tuple<'a> = PySequenceIterable<'a, 'py> where Self: 'a;

    fn validate_tuple<'a>(&'a self, strict: bool) -> ValMatch<PySequenceIterable<'a, 'py>> {
        if let Ok(tup) = self.downcast::<PyTuple>() {
            return Ok(ValidationMatch::exact(PySequenceIterable::Tuple(tup)));
        } else if !strict {
            if let Ok(other) = extract_sequence_iterable(self) {
                return Ok(ValidationMatch::lax(other));
            }
        }

        Err(ValError::new(ErrorTypeDefaults::TupleType, self))
    }

    type Set<'a> = PySequenceIterable<'a, 'py> where Self: 'a;

    fn validate_set<'a>(&'a self, strict: bool) -> ValMatch<PySequenceIterable<'a, 'py>> {
        if let Ok(set) = self.downcast::<PySet>() {
            return Ok(ValidationMatch::exact(PySequenceIterable::Set(set)));
        } else if !strict {
            if let Ok(other) = extract_sequence_iterable(self) {
                return Ok(ValidationMatch::lax(other));
            }
        }

        Err(ValError::new(ErrorTypeDefaults::SetType, self))
    }

    fn validate_frozenset<'a>(&'a self, strict: bool) -> ValMatch<PySequenceIterable<'a, 'py>> {
        if let Ok(frozenset) = self.downcast::<PyFrozenSet>() {
            return Ok(ValidationMatch::exact(PySequenceIterable::FrozenSet(frozenset)));
        } else if !strict {
            if let Ok(other) = extract_sequence_iterable(self) {
                return Ok(ValidationMatch::lax(other));
            }
        }

        Err(ValError::new(ErrorTypeDefaults::FrozenSetType, self))
    }

    fn validate_iter(&self) -> ValResult<GenericIterator<'static>> {
        if self.iter().is_ok() {
            Ok(self.into())
        } else {
            Err(ValError::new(ErrorTypeDefaults::IterableType, self))
        }
    }

    fn validate_date(&self, strict: bool) -> ValResult<ValidationMatch<EitherDate<'py>>> {
        if let Ok(date) = self.downcast_exact::<PyDate>() {
            Ok(ValidationMatch::exact(date.clone().into()))
        } else if self.is_instance_of::<PyDateTime>() {
            // have to check if it's a datetime first, otherwise the line below converts to a date
            // even if we later try coercion from a datetime, we don't want to return a datetime now
            Err(ValError::new(ErrorTypeDefaults::DateType, self))
        } else if let Ok(date) = self.downcast::<PyDate>() {
            Ok(ValidationMatch::strict(date.clone().into()))
        } else if let Some(bytes) = {
            if strict {
                None
            } else if let Ok(py_str) = self.downcast::<PyString>() {
                let str = py_string_str(py_str)?;
                Some(str.as_bytes())
            } else if let Ok(py_bytes) = self.downcast::<PyBytes>() {
                Some(py_bytes.as_bytes())
            } else {
                None
            }
        } {
            bytes_as_date(self, bytes).map(ValidationMatch::lax)
        } else {
            Err(ValError::new(ErrorTypeDefaults::DateType, self))
        }
    }

    fn validate_time(
        &self,
        strict: bool,
        microseconds_overflow_behavior: MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<ValidationMatch<EitherTime<'py>>> {
        if let Ok(time) = self.downcast_exact::<PyTime>() {
            return Ok(ValidationMatch::exact(time.clone().into()));
        } else if let Ok(time) = self.downcast::<PyTime>() {
            return Ok(ValidationMatch::strict(time.clone().into()));
        }

        'lax: {
            if !strict {
                return if let Ok(py_str) = self.downcast::<PyString>() {
                    let str = py_string_str(py_str)?;
                    bytes_as_time(self, str.as_bytes(), microseconds_overflow_behavior)
                } else if let Ok(py_bytes) = self.downcast::<PyBytes>() {
                    bytes_as_time(self, py_bytes.as_bytes(), microseconds_overflow_behavior)
                } else if self.is_exact_instance_of::<PyBool>() {
                    Err(ValError::new(ErrorTypeDefaults::TimeType, self))
                } else if let Some(int) = extract_i64(self) {
                    int_as_time(self, int, 0)
                } else if let Ok(float) = self.extract::<f64>() {
                    float_as_time(self, float)
                } else {
                    break 'lax;
                }
                .map(ValidationMatch::lax);
            }
        }

        Err(ValError::new(ErrorTypeDefaults::TimeType, self))
    }

    fn validate_datetime(
        &self,
        strict: bool,
        microseconds_overflow_behavior: MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<ValidationMatch<EitherDateTime<'py>>> {
        if let Ok(dt) = self.downcast_exact::<PyDateTime>() {
            return Ok(ValidationMatch::exact(dt.clone().into()));
        } else if let Ok(dt) = self.downcast::<PyDateTime>() {
            return Ok(ValidationMatch::strict(dt.clone().into()));
        }

        'lax: {
            if !strict {
                return if let Ok(py_str) = self.downcast::<PyString>() {
                    let str = py_string_str(py_str)?;
                    bytes_as_datetime(self, str.as_bytes(), microseconds_overflow_behavior)
                } else if let Ok(py_bytes) = self.downcast::<PyBytes>() {
                    bytes_as_datetime(self, py_bytes.as_bytes(), microseconds_overflow_behavior)
                } else if self.is_exact_instance_of::<PyBool>() {
                    Err(ValError::new(ErrorTypeDefaults::DatetimeType, self))
                } else if let Some(int) = extract_i64(self) {
                    int_as_datetime(self, int, 0)
                } else if let Ok(float) = self.extract::<f64>() {
                    float_as_datetime(self, float)
                } else if let Ok(date) = self.downcast::<PyDate>() {
                    Ok(date_as_datetime(date)?)
                } else {
                    break 'lax;
                }
                .map(ValidationMatch::lax);
            }
        }

        Err(ValError::new(ErrorTypeDefaults::DatetimeType, self))
    }

    fn validate_timedelta(
        &self,
        strict: bool,
        microseconds_overflow_behavior: MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<ValidationMatch<EitherTimedelta<'py>>> {
        if let Ok(either_dt) = EitherTimedelta::try_from(self) {
            let exactness = if matches!(either_dt, EitherTimedelta::PyExact(_)) {
                Exactness::Exact
            } else {
                Exactness::Strict
            };
            return Ok(ValidationMatch::new(either_dt, exactness));
        }

        'lax: {
            if !strict {
                return if let Ok(py_str) = self.downcast::<PyString>() {
                    let str = py_string_str(py_str)?;
                    bytes_as_timedelta(self, str.as_bytes(), microseconds_overflow_behavior)
                } else if let Ok(py_bytes) = self.downcast::<PyBytes>() {
                    bytes_as_timedelta(self, py_bytes.as_bytes(), microseconds_overflow_behavior)
                } else if let Some(int) = extract_i64(self) {
                    Ok(int_as_duration(self, int)?.into())
                } else if let Ok(float) = self.extract::<f64>() {
                    Ok(float_as_duration(self, float)?.into())
                } else {
                    break 'lax;
                }
                .map(ValidationMatch::lax);
            }
        }

        Err(ValError::new(ErrorTypeDefaults::TimeDeltaType, self))
    }
}

impl<'py> BorrowInput<'py> for Bound<'py, PyAny> {
    type Input = Bound<'py, PyAny>;
    fn borrow_input(&self) -> &Self::Input {
        self
    }
}

impl<'py> BorrowInput<'py> for Borrowed<'_, 'py, PyAny> {
    type Input = Bound<'py, PyAny>;
    fn borrow_input(&self) -> &Self::Input {
        self
    }
}

/// Best effort check of whether it's likely to make sense to inspect obj for attributes and iterate over it
/// with `obj.dir()`
fn from_attributes_applicable(obj: &Bound<'_, PyAny>) -> bool {
    let Some(module_name) = obj
        .get_type()
        .getattr(intern!(obj.py(), "__module__"))
        .ok()
        .and_then(|module_name| module_name.downcast_into::<PyString>().ok())
    else {
        return false;
    };
    // I don't think it's a very good list at all! But it doesn't have to be at perfect, it just needs to avoid
    // the most egregious foot guns, it's mostly just to catch "builtins"
    // still happy to add more or do something completely different if anyone has a better idea???
    // dbg!(obj, module_name);
    !matches!(module_name.to_str(), Ok("builtins" | "datetime" | "collections"))
}

/// Utility for extracting a string from a PyAny, if possible.
fn maybe_as_string<'a>(v: &'a Bound<'_, PyAny>, unicode_error: ErrorType) -> ValResult<Option<Cow<'a, str>>> {
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

/// Utility for extracting an enum value, if possible.
fn maybe_as_enum<'py>(v: &Bound<'py, PyAny>) -> Option<Bound<'py, PyAny>> {
    let py = v.py();
    let enum_meta_object = get_enum_meta_object(py);
    let meta_type = v.get_type().get_type();
    if meta_type.is(enum_meta_object) {
        v.getattr(intern!(py, "value")).ok()
    } else {
        None
    }
}

#[cfg(PyPy)]
static DICT_KEYS_TYPE: pyo3::sync::GILOnceCell<Py<PyType>> = pyo3::sync::GILOnceCell::new();

#[cfg(PyPy)]
fn is_dict_keys_type(v: &Bound<'_, PyAny>) -> bool {
    let py = v.py();
    let keys_type = DICT_KEYS_TYPE
        .get_or_init(py, || {
            py.eval("type({}.keys())", None, None)
                .unwrap()
                .downcast::<PyType>()
                .unwrap()
                .into()
        })
        .bind(py);
    v.is_instance(keys_type).unwrap_or(false)
}

#[cfg(PyPy)]
static DICT_VALUES_TYPE: pyo3::sync::GILOnceCell<Py<PyType>> = pyo3::sync::GILOnceCell::new();

#[cfg(PyPy)]
fn is_dict_values_type(v: &Bound<'_, PyAny>) -> bool {
    let py = v.py();
    let values_type = DICT_VALUES_TYPE
        .get_or_init(py, || {
            py.eval("type({}.values())", None, None)
                .unwrap()
                .downcast::<PyType>()
                .unwrap()
                .into()
        })
        .bind(py);
    v.is_instance(values_type).unwrap_or(false)
}

#[cfg(PyPy)]
static DICT_ITEMS_TYPE: pyo3::sync::GILOnceCell<Py<PyType>> = pyo3::sync::GILOnceCell::new();

#[cfg(PyPy)]
fn is_dict_items_type(v: &Bound<'_, PyAny>) -> bool {
    let py = v.py();
    let items_type = DICT_ITEMS_TYPE
        .get_or_init(py, || {
            py.eval("type({}.items())", None, None)
                .unwrap()
                .downcast::<PyType>()
                .unwrap()
                .into()
        })
        .bind(py);
    v.is_instance(items_type).unwrap_or(false)
}

#[cfg_attr(debug_assertions, derive(Debug))]
pub struct PyArgs<'py> {
    pub args: Option<PyPosArgs<'py>>,
    pub kwargs: Option<PyKwargs<'py>>,
}

#[cfg_attr(debug_assertions, derive(Debug))]
pub struct PyPosArgs<'py>(Bound<'py, PyTuple>);
#[cfg_attr(debug_assertions, derive(Debug))]
pub struct PyKwargs<'py>(Bound<'py, PyDict>);

impl<'py> PyArgs<'py> {
    pub fn new(args: Option<Bound<'py, PyTuple>>, kwargs: Option<Bound<'py, PyDict>>) -> Self {
        Self {
            args: args.map(PyPosArgs),
            kwargs: kwargs.map(PyKwargs),
        }
    }
}

impl<'py> Arguments<'py> for PyArgs<'py> {
    type Args = PyPosArgs<'py>;
    type Kwargs = PyKwargs<'py>;

    fn args(&self) -> Option<&PyPosArgs<'py>> {
        self.args.as_ref()
    }

    fn kwargs(&self) -> Option<&PyKwargs<'py>> {
        self.kwargs.as_ref()
    }
}

impl<'py> PositionalArgs<'py> for PyPosArgs<'py> {
    type Item<'a> = Borrowed<'a, 'py, PyAny> where Self: 'a;

    fn len(&self) -> usize {
        self.0.len()
    }

    fn get_item(&self, index: usize) -> Option<Self::Item<'_>> {
        self.0.get_borrowed_item(index).ok()
    }

    fn iter(&self) -> impl Iterator<Item = Self::Item<'_>> {
        self.0.iter_borrowed()
    }
}

impl<'py> KeywordArgs<'py> for PyKwargs<'py> {
    type Key<'a> = Bound<'py, PyAny>
    where
        Self: 'a;

    type Item<'a> = Bound<'py, PyAny>
    where
        Self: 'a;

    fn len(&self) -> usize {
        self.0.len()
    }

    fn get_item<'k>(
        &self,
        key: &'k crate::lookup_key::LookupKey,
    ) -> ValResult<Option<(&'k crate::lookup_key::LookupPath, Self::Item<'_>)>> {
        key.py_get_dict_item(&self.0)
    }

    fn iter(&self) -> impl Iterator<Item = ValResult<(Self::Key<'_>, Self::Item<'_>)>> {
        self.0.iter().map(Ok)
    }
}

#[cfg_attr(debug_assertions, derive(Debug))]
pub enum GenericPyMapping<'a, 'py> {
    Dict(&'a Bound<'py, PyDict>),
    Mapping(&'a Bound<'py, PyMapping>),
    GetAttr(Bound<'py, PyAny>, Option<Bound<'py, PyDict>>),
}

impl<'py> ValidatedDict<'py> for GenericPyMapping<'_, 'py> {
    type Key<'a> = Bound<'py, PyAny>
    where
        Self: 'a;

    type Item<'a> = Bound<'py, PyAny>
    where
        Self: 'a;

    fn get_item<'k>(
        &self,
        key: &'k crate::lookup_key::LookupKey,
    ) -> ValResult<Option<(&'k crate::lookup_key::LookupPath, Self::Item<'_>)>> {
        match self {
            Self::Dict(dict) => key.py_get_dict_item(dict),
            Self::Mapping(mapping) => key.py_get_mapping_item(mapping),
            Self::GetAttr(obj, dict) => key.py_get_attr(obj, dict.as_ref()),
        }
    }

    fn as_py_dict(&self) -> Option<&Bound<'py, PyDict>> {
        match self {
            Self::Dict(dict) => Some(dict),
            _ => None,
        }
    }

    fn iterate<'a, R>(
        &'a self,
        consumer: impl ConsumeIterator<ValResult<(Self::Key<'a>, Self::Item<'a>)>, Output = R>,
    ) -> ValResult<R> {
        match self {
            Self::Dict(dict) => Ok(consumer.consume_iterator(dict.iter().map(Ok))),
            Self::Mapping(mapping) => Ok(consumer.consume_iterator(iterate_mapping_items(mapping)?)),
            Self::GetAttr(obj, _) => Ok(consumer.consume_iterator(iterate_attributes(obj))),
        }
    }
}

/// Container for all the collections (sized iterable containers) types, which
/// can mostly be converted to each other in lax mode.
/// This mostly matches python's definition of `Collection`.
pub enum PySequenceIterable<'a, 'py> {
    List(&'a Bound<'py, PyList>),
    Tuple(&'a Bound<'py, PyTuple>),
    Set(&'a Bound<'py, PySet>),
    FrozenSet(&'a Bound<'py, PyFrozenSet>),
    Iterator(Bound<'py, PyIterator>),
}

/// Extract types which can be iterated to produce a sequence-like container like a list, tuple, set
/// or frozenset
fn extract_sequence_iterable<'a, 'py>(obj: &'a Bound<'py, PyAny>) -> ValResult<PySequenceIterable<'a, 'py>> {
    // Handle concrete non-overlapping types first, then abstract types
    if let Ok(iterable) = obj.downcast::<PyList>() {
        Ok(PySequenceIterable::List(iterable))
    } else if let Ok(iterable) = obj.downcast::<PyTuple>() {
        Ok(PySequenceIterable::Tuple(iterable))
    } else if let Ok(iterable) = obj.downcast::<PySet>() {
        Ok(PySequenceIterable::Set(iterable))
    } else if let Ok(iterable) = obj.downcast::<PyFrozenSet>() {
        Ok(PySequenceIterable::FrozenSet(iterable))
    } else {
        // Try to get this as a generable iterable thing, but exclude string and mapping types
        if !(obj.is_instance_of::<PyString>()
            || obj.is_instance_of::<PyBytes>()
            || obj.is_instance_of::<PyByteArray>()
            || obj.is_instance_of::<PyDict>()
            || obj.downcast::<PyMapping>().is_ok())
        {
            if let Ok(iter) = obj.iter() {
                return Ok(PySequenceIterable::Iterator(iter));
            }
        }

        Err(ValError::new(ErrorTypeDefaults::IterableType, obj))
    }
}

impl<'py> PySequenceIterable<'_, 'py> {
    pub fn generic_len(&self) -> Option<usize> {
        match &self {
            PySequenceIterable::List(iter) => Some(iter.len()),
            PySequenceIterable::Tuple(iter) => Some(iter.len()),
            PySequenceIterable::Set(iter) => Some(iter.len()),
            PySequenceIterable::FrozenSet(iter) => Some(iter.len()),
            PySequenceIterable::Iterator(iter) => iter.len().ok(),
        }
    }

    fn generic_iterate<R>(
        self,
        consumer: impl ConsumeIterator<PyResult<Bound<'py, PyAny>>, Output = R>,
    ) -> ValResult<R> {
        match self {
            PySequenceIterable::List(iter) => Ok(consumer.consume_iterator(iter.iter().map(Ok))),
            PySequenceIterable::Tuple(iter) => Ok(consumer.consume_iterator(iter.iter().map(Ok))),
            PySequenceIterable::Set(iter) => Ok(consumer.consume_iterator(iter.iter().map(Ok))),
            PySequenceIterable::FrozenSet(iter) => Ok(consumer.consume_iterator(iter.iter().map(Ok))),
            PySequenceIterable::Iterator(iter) => Ok(consumer.consume_iterator(iter.iter()?)),
        }
    }
}

impl<'py> ValidatedList<'py> for PySequenceIterable<'_, 'py> {
    type Item = Bound<'py, PyAny>;
    fn len(&self) -> Option<usize> {
        self.generic_len()
    }
    fn iterate<R>(self, consumer: impl ConsumeIterator<PyResult<Self::Item>, Output = R>) -> ValResult<R> {
        self.generic_iterate(consumer)
    }
    fn as_py_list(&self) -> Option<&Bound<'py, PyList>> {
        match self {
            PySequenceIterable::List(iter) => Some(iter),
            _ => None,
        }
    }
}

impl<'py> ValidatedTuple<'py> for PySequenceIterable<'_, 'py> {
    type Item = Bound<'py, PyAny>;
    fn len(&self) -> Option<usize> {
        self.generic_len()
    }
    fn iterate<R>(self, consumer: impl ConsumeIterator<PyResult<Self::Item>, Output = R>) -> ValResult<R> {
        self.generic_iterate(consumer)
    }
}

impl<'py> ValidatedSet<'py> for PySequenceIterable<'_, 'py> {
    type Item = Bound<'py, PyAny>;
    fn iterate<R>(self, consumer: impl ConsumeIterator<PyResult<Self::Item>, Output = R>) -> ValResult<R> {
        self.generic_iterate(consumer)
    }
}
