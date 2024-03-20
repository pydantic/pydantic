use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};

use speedate::MicrosecondsPrecisionOverflowBehavior;

use crate::errors::{ErrorTypeDefaults, InputValue, LocItem, ValError, ValResult};
use crate::input::py_string_str;
use crate::lookup_key::{LookupKey, LookupPath};
use crate::tools::safe_repr;
use crate::validators::decimal::create_decimal;

use super::datetime::{
    bytes_as_date, bytes_as_datetime, bytes_as_time, bytes_as_timedelta, EitherDate, EitherDateTime, EitherTime,
};
use super::input_abstract::{Never, ValMatch};
use super::shared::{str_as_bool, str_as_float, str_as_int};
use super::{
    Arguments, BorrowInput, EitherBytes, EitherFloat, EitherInt, EitherString, EitherTimedelta, GenericIterable,
    GenericIterator, Input, KeywordArgs, ValidatedDict, ValidationMatch,
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
    pub fn new_key(py_key: Bound<'py, PyAny>) -> ValResult<Self> {
        match py_key.downcast_into::<PyString>() {
            Ok(value) => Ok(Self::String(value)),
            Err(downcast_error) => Err(ValError::new(
                ErrorTypeDefaults::StringType,
                downcast_error.into_inner(),
            )),
        }
    }

    pub fn new_value(py_value: Bound<'py, PyAny>) -> ValResult<Self> {
        match py_value.downcast_into::<PyString>() {
            Ok(py_str) => Ok(Self::String(py_str)),
            Err(downcast_error) => match downcast_error.into_inner().downcast_into::<PyDict>() {
                Ok(value) => Ok(Self::Mapping(value)),
                Err(downcast_error) => Err(ValError::new(
                    ErrorTypeDefaults::StringType,
                    downcast_error.into_inner(),
                )),
            },
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

    type Arguments<'a> = StringMappingDict<'py> where Self: 'a;

    fn validate_args(&self) -> ValResult<StringMappingDict<'py>> {
        // do we want to support this?
        Err(ValError::new(ErrorTypeDefaults::ArgumentsType, self))
    }

    fn validate_dataclass_args<'a>(&'a self, _dataclass_name: &str) -> ValResult<StringMappingDict<'py>> {
        match self {
            StringMapping::String(_) => Err(ValError::new(ErrorTypeDefaults::ArgumentsType, self)),
            StringMapping::Mapping(m) => Ok(StringMappingDict(m.clone())),
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

    type Dict<'a> = StringMappingDict<'py> where Self: 'a;

    fn strict_dict(&self) -> ValResult<StringMappingDict<'py>> {
        match self {
            Self::String(_) => Err(ValError::new(ErrorTypeDefaults::DictType, self)),
            Self::Mapping(d) => Ok(StringMappingDict(d.clone())),
        }
    }

    type List<'a> = Never where Self: 'a;

    fn validate_list(&self, _strict: bool) -> ValMatch<Never> {
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

pub struct StringMappingDict<'py>(Bound<'py, PyDict>);

impl<'py> Arguments<'py> for StringMappingDict<'py> {
    type Args = Never;
    type Kwargs = Self;

    fn args(&self) -> Option<&Self::Args> {
        None
    }

    fn kwargs(&self) -> Option<&Self::Kwargs> {
        Some(self)
    }
}

impl<'py> KeywordArgs<'py> for StringMappingDict<'py> {
    type Key<'a> = StringMapping<'py>
    where
        Self: 'a;

    type Item<'a> = StringMapping<'py>
    where
        Self: 'a;

    fn len(&self) -> usize {
        self.0.len()
    }

    fn get_item<'k>(&self, key: &'k LookupKey) -> ValResult<Option<(&'k LookupPath, Self::Item<'_>)>> {
        key.py_get_string_mapping_item(&self.0)
    }

    fn iter(&self) -> impl Iterator<Item = ValResult<(Self::Key<'_>, Self::Item<'_>)>> {
        self.0
            .iter()
            .map(|(key, val)| Ok((StringMapping::new_key(key)?, StringMapping::new_value(val)?)))
    }
}

impl<'py> ValidatedDict<'py> for StringMappingDict<'py> {
    type Key<'a> = StringMapping<'py>
    where
        Self: 'a;

    type Item<'a> = StringMapping<'py>
    where
        Self: 'a;
    fn get_item<'k>(&self, key: &'k LookupKey) -> ValResult<Option<(&'k LookupPath, Self::Item<'_>)>> {
        key.py_get_string_mapping_item(&self.0)
    }
    fn as_py_dict(&self) -> Option<&Bound<'py, PyDict>> {
        None
    }
    fn iterate<'a, R>(
        &'a self,
        consumer: impl super::ConsumeIterator<ValResult<(Self::Key<'a>, Self::Item<'a>)>, Output = R>,
    ) -> ValResult<R> {
        Ok(consumer.consume_iterator(
            self.0
                .iter()
                .map(|(key, val)| Ok((StringMapping::new_key(key)?, StringMapping::new_value(val)?))),
        ))
    }
}
