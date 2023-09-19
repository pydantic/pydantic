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
use super::shared::{map_json_err, str_as_bool, str_as_float};
use super::{
    BorrowInput, EitherBytes, EitherFloat, EitherInt, EitherString, EitherTimedelta, GenericArguments, GenericIterable,
    GenericIterator, GenericMapping, Input, JsonInput,
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

impl<'a> Input<'a> for StringMapping<'a> {
    fn as_loc_item(&self) -> LocItem {
        match self {
            Self::String(s) => s.to_string_lossy().as_ref().into(),
            Self::Mapping(d) => safe_repr(d).to_string().into(),
        }
    }

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

    fn parse_json(&'a self) -> ValResult<'a, JsonInput> {
        match self {
            Self::String(s) => {
                let str = py_string_str(s)?;
                serde_json::from_str(str).map_err(|e| map_json_err(self, e))
            }
            Self::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::JsonType, self)),
        }
    }

    fn strict_str(&'a self) -> ValResult<EitherString<'a>> {
        match self {
            Self::String(s) => Ok((*s).into()),
            Self::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::StringType, self)),
        }
    }

    fn strict_bytes(&'a self) -> ValResult<EitherBytes<'a>> {
        match self {
            Self::String(s) => py_string_str(s).map(|b| b.as_bytes().into()),
            Self::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::BytesType, self)),
        }
    }

    fn lax_bytes(&'a self) -> ValResult<EitherBytes<'a>> {
        match self {
            Self::String(s) => {
                let str = py_string_str(s)?;
                Ok(str.as_bytes().into())
            }
            Self::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::BytesType, self)),
        }
    }

    fn strict_bool(&self) -> ValResult<bool> {
        match self {
            Self::String(s) => str_as_bool(self, py_string_str(s)?),
            Self::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::BoolType, self)),
        }
    }

    fn strict_int(&'a self) -> ValResult<EitherInt<'a>> {
        match self {
            Self::String(s) => match py_string_str(s)?.parse() {
                Ok(i) => Ok(EitherInt::I64(i)),
                Err(_) => Err(ValError::new(ErrorTypeDefaults::IntParsing, self)),
            },
            Self::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::IntType, self)),
        }
    }

    fn ultra_strict_float(&'a self) -> ValResult<EitherFloat<'a>> {
        self.strict_float()
    }

    fn strict_float(&'a self) -> ValResult<EitherFloat<'a>> {
        match self {
            Self::String(s) => str_as_float(self, py_string_str(s)?),
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

    fn strict_date(&self) -> ValResult<EitherDate> {
        match self {
            Self::String(s) => bytes_as_date(self, py_string_str(s)?.as_bytes()),
            Self::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::DateType, self)),
        }
    }

    fn strict_time(
        &self,
        microseconds_overflow_behavior: MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<EitherTime> {
        match self {
            Self::String(s) => bytes_as_time(self, py_string_str(s)?.as_bytes(), microseconds_overflow_behavior),
            Self::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::TimeType, self)),
        }
    }

    fn strict_datetime(
        &self,
        microseconds_overflow_behavior: MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<EitherDateTime> {
        match self {
            Self::String(s) => bytes_as_datetime(self, py_string_str(s)?.as_bytes(), microseconds_overflow_behavior),
            Self::Mapping(_) => Err(ValError::new(ErrorTypeDefaults::DatetimeType, self)),
        }
    }

    fn strict_timedelta(
        &self,
        microseconds_overflow_behavior: MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<EitherTimedelta> {
        match self {
            Self::String(s) => bytes_as_timedelta(self, py_string_str(s)?.as_bytes(), microseconds_overflow_behavior),
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
