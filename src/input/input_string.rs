use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};

use jiter::JsonValue;
use speedate::MicrosecondsPrecisionOverflowBehavior;

use crate::errors::{AsLocItem, ErrorTypeDefaults, InputValue, LocItem, ValError, ValResult};
use crate::input::py_string_str;
use crate::tools::safe_repr;
use crate::validators::decimal::create_decimal;

use super::datetime::{
    bytes_as_date, bytes_as_datetime, bytes_as_time, bytes_as_timedelta, EitherDate, EitherDateTime, EitherTime,
};
use super::shared::{map_json_err, str_as_bool, str_as_float};
use super::{
    BorrowInput, EitherBytes, EitherFloat, EitherInt, EitherString, EitherTimedelta, GenericArguments, GenericIterable,
    GenericIterator, GenericMapping, Input, ValidationMatch,
};

#[derive(Debug)]
pub enum StringMapping<'py> {
    String(&'py PyString),
    Mapping(&'py PyDict),
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
    pub fn new_key(py_key: &'py PyAny) -> ValResult<'py, StringMapping> {
        if let Ok(py_str) = py_key.downcast::<PyString>() {
            Ok(Self::String(py_str))
        } else {
            Err(ValError::new(ErrorTypeDefaults::StringType, py_key))
        }
    }

    pub fn new_value(py_value: &'py PyAny) -> ValResult<'py, Self> {
        if let Ok(py_str) = py_value.downcast::<PyString>() {
            Ok(Self::String(py_str))
        } else if let Ok(value) = py_value.downcast::<PyDict>() {
            Ok(Self::Mapping(value))
        } else {
            Err(ValError::new(ErrorTypeDefaults::StringType, py_value))
        }
    }
}

impl AsLocItem for StringMapping<'_> {
    fn as_loc_item(&self) -> LocItem {
        match self {
            Self::String(s) => s.to_string_lossy().as_ref().into(),
            Self::Mapping(d) => safe_repr(d).to_string().into(),
        }
    }
}

impl<'a> Input<'a> for StringMapping<'a> {
    fn as_error_value(&'a self) -> InputValue<'a> {
        match self {
            Self::String(s) => s.as_error_value(),
            Self::Mapping(d) => InputValue::PyAny(d),
        }
    }

    fn as_kwargs(&'a self, _py: Python<'a>) -> Option<&'a PyDict> {
        None
    }

    fn validate_args(&'a self) -> ValResult<'a, GenericArguments<'a>> {
        // do we want to support this?
        Err(ValError::new(ErrorTypeDefaults::ArgumentsType, self))
    }

    fn validate_dataclass_args(&'a self, _dataclass_name: &str) -> ValResult<'a, GenericArguments<'a>> {
        match self {
            StringMapping::String(_) => Err(ValError::new(ErrorTypeDefaults::ArgumentsType, self)),
            StringMapping::Mapping(m) => Ok(GenericArguments::StringMapping(m)),
        }
    }

    fn parse_json(&'a self) -> ValResult<'a, JsonValue> {
        match self {
            Self::String(s) => {
                let str = py_string_str(s)?;
                JsonValue::parse(str.as_bytes(), true).map_err(|e| map_json_err(self, e))
            }
            Self::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::JsonType, self)),
        }
    }

    fn validate_str(
        &'a self,
        _strict: bool,
        _coerce_numbers_to_str: bool,
    ) -> ValResult<ValidationMatch<EitherString<'a>>> {
        match self {
            Self::String(s) => Ok(ValidationMatch::strict((*s).into())),
            Self::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::StringType, self)),
        }
    }

    fn validate_bytes(&'a self, _strict: bool) -> ValResult<ValidationMatch<EitherBytes<'a>>> {
        match self {
            Self::String(s) => py_string_str(s).map(|b| ValidationMatch::strict(b.as_bytes().into())),
            Self::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::BytesType, self)),
        }
    }

    fn validate_bool(&self, _strict: bool) -> ValResult<'_, ValidationMatch<bool>> {
        match self {
            Self::String(s) => str_as_bool(self, py_string_str(s)?).map(ValidationMatch::strict),
            Self::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::BoolType, self)),
        }
    }

    fn validate_int(&'a self, _strict: bool) -> ValResult<'a, ValidationMatch<EitherInt<'a>>> {
        match self {
            Self::String(s) => match py_string_str(s)?.parse() {
                Ok(i) => Ok(ValidationMatch::strict(EitherInt::I64(i))),
                Err(_) => Err(ValError::new(ErrorTypeDefaults::IntParsing, self)),
            },
            Self::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::IntType, self)),
        }
    }

    fn validate_float(&'a self, _strict: bool) -> ValResult<'a, ValidationMatch<EitherFloat<'a>>> {
        match self {
            Self::String(s) => str_as_float(self, py_string_str(s)?).map(ValidationMatch::strict),
            Self::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::FloatType, self)),
        }
    }

    fn strict_decimal(&'a self, py: Python<'a>) -> ValResult<&'a PyAny> {
        match self {
            Self::String(s) => create_decimal(s, self, py),
            Self::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::DecimalType, self)),
        }
    }

    fn strict_dict(&'a self) -> ValResult<GenericMapping<'a>> {
        match self {
            Self::String(_) => Err(ValError::new(ErrorTypeDefaults::DictType, self)),
            Self::Mapping(d) => Ok(GenericMapping::StringMapping(d)),
        }
    }

    fn strict_list(&'a self) -> ValResult<GenericIterable<'a>> {
        Err(ValError::new(ErrorTypeDefaults::ListType, self))
    }

    fn strict_tuple(&'a self) -> ValResult<GenericIterable<'a>> {
        Err(ValError::new(ErrorTypeDefaults::TupleType, self))
    }

    fn strict_set(&'a self) -> ValResult<GenericIterable<'a>> {
        Err(ValError::new(ErrorTypeDefaults::SetType, self))
    }

    fn strict_frozenset(&'a self) -> ValResult<GenericIterable<'a>> {
        Err(ValError::new(ErrorTypeDefaults::FrozenSetType, self))
    }

    fn extract_generic_iterable(&'a self) -> ValResult<GenericIterable<'a>> {
        Err(ValError::new(ErrorTypeDefaults::IterableType, self))
    }

    fn validate_iter(&self) -> ValResult<GenericIterator> {
        Err(ValError::new(ErrorTypeDefaults::IterableType, self))
    }

    fn validate_date(&self, _strict: bool) -> ValResult<ValidationMatch<EitherDate>> {
        match self {
            Self::String(s) => bytes_as_date(self, py_string_str(s)?.as_bytes()).map(ValidationMatch::strict),
            Self::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::DateType, self)),
        }
    }

    fn validate_time(
        &self,
        _strict: bool,
        microseconds_overflow_behavior: MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<ValidationMatch<EitherTime>> {
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
    ) -> ValResult<ValidationMatch<EitherDateTime>> {
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
    ) -> ValResult<ValidationMatch<EitherTimedelta>> {
        match self {
            Self::String(s) => bytes_as_timedelta(self, py_string_str(s)?.as_bytes(), microseconds_overflow_behavior)
                .map(ValidationMatch::strict),
            Self::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::TimeDeltaType, self)),
        }
    }
}

impl BorrowInput for StringMapping<'_> {
    type Input<'a> = StringMapping<'a> where Self: 'a;
    fn borrow_input(&self) -> &Self::Input<'_> {
        self
    }
}
