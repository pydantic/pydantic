use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};

use speedate::MicrosecondsPrecisionOverflowBehavior;

use crate::errors::{ErrorTypeDefaults, InputValue, LocItem, ValError, ValResult};
use crate::input::py_string_str;
use crate::tools::safe_repr;
use crate::validators::decimal::create_decimal;

use super::datetime::{
    bytes_as_date, bytes_as_datetime, bytes_as_time, bytes_as_timedelta, EitherDate, EitherDateTime, EitherTime,
};
use super::shared::{str_as_bool, str_as_float, str_as_int};
use super::{
    BorrowInput, EitherBytes, EitherFloat, EitherInt, EitherString, EitherTimedelta, GenericArguments, GenericIterable,
    GenericIterator, GenericMapping, Input, ValidationMatch,
};

#[derive(Debug, Clone)]
pub enum StringMapping<'py> {
    String(Bound<'py, PyString>),
    Mapping(Bound<'py, PyDict>),
}

impl<'py> ToPyObject for StringMapping<'py> {
    fn to_object(&self, py: Python<'_>) -> PyObject {
        match self {
            Self::String(s) => s.to_object(py),
            Self::Mapping(d) => d.to_object(py),
        }
    }
}

impl<'py> StringMapping<'py> {
    pub fn new_key(py_key: &Bound<'py, PyAny>) -> ValResult<Self> {
        if let Ok(py_str) = py_key.downcast::<PyString>() {
            Ok(Self::String(py_str.clone()))
        } else {
            Err(ValError::new(ErrorTypeDefaults::StringType, py_key))
        }
    }

    pub fn new_value(py_value: &Bound<'py, PyAny>) -> ValResult<Self> {
        if let Ok(py_str) = py_value.downcast::<PyString>() {
            Ok(Self::String(py_str.clone()))
        } else if let Ok(value) = py_value.downcast::<PyDict>() {
            Ok(Self::Mapping(value.clone()))
        } else {
            Err(ValError::new(ErrorTypeDefaults::StringType, py_value))
        }
    }
}

impl From<StringMapping<'_>> for LocItem {
    fn from(string_mapping: StringMapping<'_>) -> Self {
        match string_mapping {
            StringMapping::String(s) => s.to_string_lossy().as_ref().into(),
            StringMapping::Mapping(d) => safe_repr(&d).to_string().into(),
        }
    }
}

impl<'py> Input<'py> for StringMapping<'py> {
    fn as_error_value(&self) -> InputValue {
        match self {
            Self::String(s) => s.as_error_value(),
            Self::Mapping(d) => d.as_error_value(),
        }
    }

    fn as_kwargs(&self, _py: Python<'py>) -> Option<Bound<'py, PyDict>> {
        None
    }

    fn validate_args(&self) -> ValResult<GenericArguments<'_, 'py>> {
        // do we want to support this?
        Err(ValError::new(ErrorTypeDefaults::ArgumentsType, self))
    }

    fn validate_dataclass_args<'a>(&'a self, _dataclass_name: &str) -> ValResult<GenericArguments<'a, 'py>> {
        match self {
            StringMapping::String(_) => Err(ValError::new(ErrorTypeDefaults::ArgumentsType, self)),
            StringMapping::Mapping(m) => Ok(GenericArguments::StringMapping(m.clone())),
        }
    }

    fn validate_str(
        &self,
        _strict: bool,
        _coerce_numbers_to_str: bool,
    ) -> ValResult<ValidationMatch<EitherString<'_>>> {
        match self {
            Self::String(s) => Ok(ValidationMatch::strict(s.clone().into())),
            Self::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::StringType, self)),
        }
    }

    fn validate_bytes<'a>(&'a self, _strict: bool) -> ValResult<ValidationMatch<EitherBytes<'a, 'py>>> {
        match self {
            Self::String(s) => py_string_str(s).map(|b| ValidationMatch::strict(b.as_bytes().into())),
            Self::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::BytesType, self)),
        }
    }

    fn validate_bool(&self, _strict: bool) -> ValResult<ValidationMatch<bool>> {
        match self {
            Self::String(s) => str_as_bool(self, py_string_str(s)?).map(ValidationMatch::strict),
            Self::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::BoolType, self)),
        }
    }

    fn validate_int(&self, _strict: bool) -> ValResult<ValidationMatch<EitherInt<'_>>> {
        match self {
            Self::String(s) => str_as_int(self, py_string_str(s)?).map(ValidationMatch::strict),
            Self::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::IntType, self)),
        }
    }

    fn validate_float(&self, _strict: bool) -> ValResult<ValidationMatch<EitherFloat<'_>>> {
        match self {
            Self::String(s) => str_as_float(self, py_string_str(s)?).map(ValidationMatch::strict),
            Self::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::FloatType, self)),
        }
    }

    fn strict_decimal(&self, _py: Python<'py>) -> ValResult<Bound<'py, PyAny>> {
        match self {
            Self::String(s) => create_decimal(s, self),
            Self::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::DecimalType, self)),
        }
    }

    fn strict_dict<'a>(&'a self) -> ValResult<GenericMapping<'a, 'py>> {
        match self {
            Self::String(_) => Err(ValError::new(ErrorTypeDefaults::DictType, self)),
            Self::Mapping(d) => Ok(GenericMapping::StringMapping(d)),
        }
    }

    fn strict_list<'a>(&'a self) -> ValResult<GenericIterable<'a, 'py>> {
        Err(ValError::new(ErrorTypeDefaults::ListType, self))
    }

    fn strict_tuple<'a>(&'a self) -> ValResult<GenericIterable<'a, 'py>> {
        Err(ValError::new(ErrorTypeDefaults::TupleType, self))
    }

    fn strict_set<'a>(&'a self) -> ValResult<GenericIterable<'a, 'py>> {
        Err(ValError::new(ErrorTypeDefaults::SetType, self))
    }

    fn strict_frozenset<'a>(&'a self) -> ValResult<GenericIterable<'a, 'py>> {
        Err(ValError::new(ErrorTypeDefaults::FrozenSetType, self))
    }

    fn extract_generic_iterable<'a>(&'a self) -> ValResult<GenericIterable<'a, 'py>> {
        Err(ValError::new(ErrorTypeDefaults::IterableType, self))
    }

    fn validate_iter(&self) -> ValResult<GenericIterator> {
        Err(ValError::new(ErrorTypeDefaults::IterableType, self))
    }

    fn validate_date(&self, _strict: bool) -> ValResult<ValidationMatch<EitherDate<'py>>> {
        match self {
            Self::String(s) => bytes_as_date(self, py_string_str(s)?.as_bytes()).map(ValidationMatch::strict),
            Self::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::DateType, self)),
        }
    }

    fn validate_time(
        &self,
        _strict: bool,
        microseconds_overflow_behavior: MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<ValidationMatch<EitherTime<'py>>> {
        match self {
            Self::String(s) => bytes_as_time(self, py_string_str(s)?.as_bytes(), microseconds_overflow_behavior)
                .map(ValidationMatch::strict),
            Self::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::TimeType, self)),
        }
    }

    fn validate_datetime(
        &self,
        _strict: bool,
        microseconds_overflow_behavior: MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<ValidationMatch<EitherDateTime<'py>>> {
        match self {
            Self::String(s) => bytes_as_datetime(self, py_string_str(s)?.as_bytes(), microseconds_overflow_behavior)
                .map(ValidationMatch::strict),
            Self::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::DatetimeType, self)),
        }
    }

    fn validate_timedelta(
        &self,
        _strict: bool,
        microseconds_overflow_behavior: MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<ValidationMatch<EitherTimedelta<'py>>> {
        match self {
            Self::String(s) => bytes_as_timedelta(self, py_string_str(s)?.as_bytes(), microseconds_overflow_behavior)
                .map(ValidationMatch::strict),
            Self::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::TimeDeltaType, self)),
        }
    }
}

impl<'py> BorrowInput<'py> for StringMapping<'py> {
    type Input = Self;
    fn borrow_input(&self) -> &Self::Input {
        self
    }
}
