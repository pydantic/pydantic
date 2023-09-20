use std::borrow::Cow;

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};
use speedate::MicrosecondsPrecisionOverflowBehavior;
use strum::EnumMessage;

use crate::errors::{ErrorType, ErrorTypeDefaults, InputValue, LocItem, ValError, ValResult};
use crate::validators::decimal::create_decimal;

use super::datetime::{
    bytes_as_date, bytes_as_datetime, bytes_as_time, bytes_as_timedelta, float_as_datetime, float_as_duration,
    float_as_time, int_as_datetime, int_as_duration, int_as_time, EitherDate, EitherDateTime, EitherTime,
};
use super::shared::{float_as_int, int_as_bool, map_json_err, str_as_bool, str_as_float, str_as_int, string_to_vec};
use super::{
    BorrowInput, EitherBytes, EitherFloat, EitherInt, EitherString, EitherTimedelta, GenericArguments, GenericIterable,
    GenericIterator, GenericMapping, Input, JsonArgs, JsonArray, JsonInput,
};

impl<'a> Input<'a> for JsonInput {
    /// This is required by since JSON object keys are always strings, I don't think it can be called
    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn as_loc_item(&self) -> LocItem {
        match self {
            JsonInput::Int(i) => (*i).into(),
            JsonInput::String(s) => s.as_str().into(),
            v => format!("{v:?}").into(),
        }
    }

    fn as_error_value(&'a self) -> InputValue<'a> {
        // cloning JsonInput is cheap due to use of Arc
        InputValue::JsonInput(self.clone())
    }

    fn is_none(&self) -> bool {
        matches!(self, JsonInput::Null)
    }

    fn as_kwargs(&'a self, py: Python<'a>) -> Option<&'a PyDict> {
        match self {
            JsonInput::Object(object) => {
                let dict = PyDict::new(py);
                for (k, v) in object.iter() {
                    dict.set_item(k, v.to_object(py)).unwrap();
                }
                Some(dict)
            }
            _ => None,
        }
    }

    fn validate_args(&'a self) -> ValResult<'a, GenericArguments<'a>> {
        match self {
            JsonInput::Object(object) => Ok(JsonArgs::new(None, Some(object)).into()),
            JsonInput::Array(array) => Ok(JsonArgs::new(Some(array), None).into()),
            _ => Err(ValError::new(ErrorTypeDefaults::ArgumentsType, self)),
        }
    }

    fn validate_dataclass_args(&'a self, class_name: &str) -> ValResult<'a, GenericArguments<'a>> {
        match self {
            JsonInput::Object(object) => Ok(JsonArgs::new(None, Some(object)).into()),
            _ => {
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
    }

    fn parse_json(&'a self) -> ValResult<'a, JsonInput> {
        match self {
            JsonInput::String(s) => serde_json::from_str(s.as_str()).map_err(|e| map_json_err(self, e)),
            _ => Err(ValError::new(ErrorTypeDefaults::JsonType, self)),
        }
    }

    fn strict_str(&'a self) -> ValResult<EitherString<'a>> {
        match self {
            JsonInput::String(s) => Ok(s.as_str().into()),
            _ => Err(ValError::new(ErrorTypeDefaults::StringType, self)),
        }
    }
    fn lax_str(&'a self, coerce_numbers_to_str: bool) -> ValResult<EitherString<'a>> {
        match self {
            JsonInput::String(s) => Ok(s.as_str().into()),
            JsonInput::BigInt(v) if coerce_numbers_to_str => Ok(v.to_string().into()),
            JsonInput::Float(v) if coerce_numbers_to_str => Ok(v.to_string().into()),
            JsonInput::Int(v) if coerce_numbers_to_str => Ok(v.to_string().into()),
            JsonInput::Uint(v) if coerce_numbers_to_str => Ok(v.to_string().into()),
            _ => Err(ValError::new(ErrorTypeDefaults::StringType, self)),
        }
    }

    fn validate_bytes(&'a self, _strict: bool) -> ValResult<EitherBytes<'a>> {
        match self {
            JsonInput::String(s) => Ok(s.as_bytes().into()),
            _ => Err(ValError::new(ErrorTypeDefaults::BytesType, self)),
        }
    }
    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn strict_bytes(&'a self) -> ValResult<EitherBytes<'a>> {
        self.validate_bytes(false)
    }

    fn strict_bool(&self) -> ValResult<bool> {
        match self {
            JsonInput::Bool(b) => Ok(*b),
            _ => Err(ValError::new(ErrorTypeDefaults::BoolType, self)),
        }
    }
    fn lax_bool(&self) -> ValResult<bool> {
        match self {
            JsonInput::Bool(b) => Ok(*b),
            JsonInput::String(s) => str_as_bool(self, s),
            JsonInput::Int(int) => int_as_bool(self, *int),
            JsonInput::Float(float) => match float_as_int(self, *float) {
                Ok(int) => int
                    .as_bool()
                    .ok_or_else(|| ValError::new(ErrorTypeDefaults::BoolParsing, self)),
                _ => Err(ValError::new(ErrorTypeDefaults::BoolType, self)),
            },
            _ => Err(ValError::new(ErrorTypeDefaults::BoolType, self)),
        }
    }

    fn strict_int(&'a self) -> ValResult<EitherInt<'a>> {
        match self {
            JsonInput::Int(i) => Ok(EitherInt::I64(*i)),
            JsonInput::Uint(u) => Ok(EitherInt::U64(*u)),
            JsonInput::BigInt(b) => Ok(EitherInt::BigInt(b.clone())),
            _ => Err(ValError::new(ErrorTypeDefaults::IntType, self)),
        }
    }
    fn lax_int(&'a self) -> ValResult<EitherInt<'a>> {
        match self {
            JsonInput::Bool(b) => match *b {
                true => Ok(EitherInt::I64(1)),
                false => Ok(EitherInt::I64(0)),
            },
            JsonInput::Int(i) => Ok(EitherInt::I64(*i)),
            JsonInput::Uint(u) => Ok(EitherInt::U64(*u)),
            JsonInput::BigInt(b) => Ok(EitherInt::BigInt(b.clone())),
            JsonInput::Float(f) => float_as_int(self, *f),
            JsonInput::String(str) => str_as_int(self, str),
            _ => Err(ValError::new(ErrorTypeDefaults::IntType, self)),
        }
    }

    fn ultra_strict_float(&'a self) -> ValResult<EitherFloat<'a>> {
        match self {
            JsonInput::Float(f) => Ok(EitherFloat::F64(*f)),
            _ => Err(ValError::new(ErrorTypeDefaults::FloatType, self)),
        }
    }
    fn strict_float(&'a self) -> ValResult<EitherFloat<'a>> {
        match self {
            JsonInput::Float(f) => Ok(EitherFloat::F64(*f)),
            JsonInput::Int(i) => Ok(EitherFloat::F64(*i as f64)),
            JsonInput::Uint(u) => Ok(EitherFloat::F64(*u as f64)),
            _ => Err(ValError::new(ErrorTypeDefaults::FloatType, self)),
        }
    }
    fn lax_float(&'a self) -> ValResult<EitherFloat<'a>> {
        match self {
            JsonInput::Bool(b) => match *b {
                true => Ok(EitherFloat::F64(1.0)),
                false => Ok(EitherFloat::F64(0.0)),
            },
            JsonInput::Float(f) => Ok(EitherFloat::F64(*f)),
            JsonInput::Int(i) => Ok(EitherFloat::F64(*i as f64)),
            JsonInput::Uint(u) => Ok(EitherFloat::F64(*u as f64)),
            JsonInput::String(str) => str_as_float(self, str),
            _ => Err(ValError::new(ErrorTypeDefaults::FloatType, self)),
        }
    }

    fn strict_decimal(&'a self, py: Python<'a>) -> ValResult<&'a PyAny> {
        match self {
            JsonInput::Float(f) => create_decimal(PyString::new(py, &f.to_string()), self, py),

            JsonInput::String(..) | JsonInput::Int(..) | JsonInput::Uint(..) | JsonInput::BigInt(..) => {
                create_decimal(self.to_object(py).into_ref(py), self, py)
            }
            _ => Err(ValError::new(ErrorTypeDefaults::DecimalType, self)),
        }
    }

    fn validate_dict(&'a self, _strict: bool) -> ValResult<GenericMapping<'a>> {
        match self {
            JsonInput::Object(dict) => Ok(dict.into()),
            _ => Err(ValError::new(ErrorTypeDefaults::DictType, self)),
        }
    }
    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn strict_dict(&'a self) -> ValResult<GenericMapping<'a>> {
        self.validate_dict(false)
    }

    fn validate_list(&'a self, _strict: bool) -> ValResult<GenericIterable<'a>> {
        match self {
            JsonInput::Array(a) => Ok(GenericIterable::JsonArray(a)),
            _ => Err(ValError::new(ErrorTypeDefaults::ListType, self)),
        }
    }
    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn strict_list(&'a self) -> ValResult<GenericIterable<'a>> {
        self.validate_list(false)
    }

    fn validate_tuple(&'a self, _strict: bool) -> ValResult<GenericIterable<'a>> {
        // just as in set's case, List has to be allowed
        match self {
            JsonInput::Array(a) => Ok(GenericIterable::JsonArray(a)),
            _ => Err(ValError::new(ErrorTypeDefaults::TupleType, self)),
        }
    }
    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn strict_tuple(&'a self) -> ValResult<GenericIterable<'a>> {
        self.validate_tuple(false)
    }

    fn validate_set(&'a self, _strict: bool) -> ValResult<GenericIterable<'a>> {
        // we allow a list here since otherwise it would be impossible to create a set from JSON
        match self {
            JsonInput::Array(a) => Ok(GenericIterable::JsonArray(a)),
            _ => Err(ValError::new(ErrorTypeDefaults::SetType, self)),
        }
    }
    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn strict_set(&'a self) -> ValResult<GenericIterable<'a>> {
        self.validate_set(false)
    }

    fn validate_frozenset(&'a self, _strict: bool) -> ValResult<GenericIterable<'a>> {
        // we allow a list here since otherwise it would be impossible to create a frozenset from JSON
        match self {
            JsonInput::Array(a) => Ok(GenericIterable::JsonArray(a)),
            _ => Err(ValError::new(ErrorTypeDefaults::FrozenSetType, self)),
        }
    }
    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn strict_frozenset(&'a self) -> ValResult<GenericIterable<'a>> {
        self.validate_frozenset(false)
    }

    fn extract_generic_iterable(&self) -> ValResult<GenericIterable> {
        match self {
            JsonInput::Array(a) => Ok(GenericIterable::JsonArray(a)),
            JsonInput::String(s) => Ok(GenericIterable::JsonString(s)),
            JsonInput::Object(object) => Ok(GenericIterable::JsonObject(object)),
            _ => Err(ValError::new(ErrorTypeDefaults::IterableType, self)),
        }
    }

    fn validate_iter(&self) -> ValResult<GenericIterator> {
        match self {
            JsonInput::Array(a) => Ok(a.clone().into()),
            JsonInput::String(s) => Ok(string_to_vec(s).into()),
            JsonInput::Object(object) => {
                // return keys iterator to match python's behavior
                let keys: JsonArray = JsonArray::new(object.keys().map(|k| JsonInput::String(k.clone())).collect());
                Ok(keys.into())
            }
            _ => Err(ValError::new(ErrorTypeDefaults::IterableType, self)),
        }
    }

    fn validate_date(&self, _strict: bool) -> ValResult<EitherDate> {
        match self {
            JsonInput::String(v) => bytes_as_date(self, v.as_bytes()),
            _ => Err(ValError::new(ErrorTypeDefaults::DateType, self)),
        }
    }
    // NO custom `lax_date` implementation, if strict_date fails, the validator will fallback to lax_datetime
    // then check there's no remainder
    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn strict_date(&self) -> ValResult<EitherDate> {
        self.validate_date(false)
    }

    fn strict_time(
        &self,
        microseconds_overflow_behavior: MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<EitherTime> {
        match self {
            JsonInput::String(v) => bytes_as_time(self, v.as_bytes(), microseconds_overflow_behavior),
            _ => Err(ValError::new(ErrorTypeDefaults::TimeType, self)),
        }
    }
    fn lax_time(&self, microseconds_overflow_behavior: MicrosecondsPrecisionOverflowBehavior) -> ValResult<EitherTime> {
        match self {
            JsonInput::String(v) => bytes_as_time(self, v.as_bytes(), microseconds_overflow_behavior),
            JsonInput::Int(v) => int_as_time(self, *v, 0),
            JsonInput::Float(v) => float_as_time(self, *v),
            JsonInput::BigInt(_) => Err(ValError::new(
                ErrorType::TimeParsing {
                    error: Cow::Borrowed(
                        speedate::ParseError::TimeTooLarge
                            .get_documentation()
                            .unwrap_or_default(),
                    ),
                    context: None,
                },
                self,
            )),
            _ => Err(ValError::new(ErrorTypeDefaults::TimeType, self)),
        }
    }

    fn strict_datetime(
        &self,
        microseconds_overflow_behavior: MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<EitherDateTime> {
        match self {
            JsonInput::String(v) => bytes_as_datetime(self, v.as_bytes(), microseconds_overflow_behavior),
            _ => Err(ValError::new(ErrorTypeDefaults::DatetimeType, self)),
        }
    }
    fn lax_datetime(
        &self,
        microseconds_overflow_behavior: MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<EitherDateTime> {
        match self {
            JsonInput::String(v) => bytes_as_datetime(self, v.as_bytes(), microseconds_overflow_behavior),
            JsonInput::Int(v) => int_as_datetime(self, *v, 0),
            JsonInput::Float(v) => float_as_datetime(self, *v),
            _ => Err(ValError::new(ErrorTypeDefaults::DatetimeType, self)),
        }
    }

    fn strict_timedelta(
        &self,
        microseconds_overflow_behavior: MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<EitherTimedelta> {
        match self {
            JsonInput::String(v) => bytes_as_timedelta(self, v.as_bytes(), microseconds_overflow_behavior),
            _ => Err(ValError::new(ErrorTypeDefaults::TimeDeltaType, self)),
        }
    }
    fn lax_timedelta(
        &self,
        microseconds_overflow_behavior: MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<EitherTimedelta> {
        match self {
            JsonInput::String(v) => bytes_as_timedelta(self, v.as_bytes(), microseconds_overflow_behavior),
            JsonInput::Int(v) => Ok(int_as_duration(self, *v)?.into()),
            JsonInput::Float(v) => Ok(float_as_duration(self, *v)?.into()),
            _ => Err(ValError::new(ErrorTypeDefaults::TimeDeltaType, self)),
        }
    }
}

impl BorrowInput for &'_ JsonInput {
    type Input<'a> = JsonInput where Self: 'a;
    fn borrow_input(&self) -> &Self::Input<'_> {
        self
    }
}

/// TODO: it would be good to get JsonInput and StringMapping string variants to go through this
/// implementation
/// Required for Dict keys so the string can behave like an Input
impl<'a> Input<'a> for String {
    fn as_loc_item(&self) -> LocItem {
        self.to_string().into()
    }

    fn as_error_value(&'a self) -> InputValue<'a> {
        InputValue::String(self)
    }

    fn as_kwargs(&'a self, _py: Python<'a>) -> Option<&'a PyDict> {
        None
    }

    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn validate_args(&'a self) -> ValResult<'a, GenericArguments<'a>> {
        Err(ValError::new(ErrorTypeDefaults::ArgumentsType, self))
    }

    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn validate_dataclass_args(&'a self, class_name: &str) -> ValResult<'a, GenericArguments<'a>> {
        let class_name = class_name.to_string();
        Err(ValError::new(
            ErrorType::DataclassType {
                class_name,
                context: None,
            },
            self,
        ))
    }

    fn parse_json(&'a self) -> ValResult<'a, JsonInput> {
        serde_json::from_str(self.as_str()).map_err(|e| map_json_err(self, e))
    }

    fn strict_str(&'a self) -> ValResult<EitherString<'a>> {
        Ok(self.as_str().into())
    }

    fn strict_bytes(&'a self) -> ValResult<EitherBytes<'a>> {
        Ok(self.as_bytes().into())
    }

    fn strict_bool(&self) -> ValResult<bool> {
        str_as_bool(self, self)
    }

    fn strict_int(&'a self) -> ValResult<EitherInt<'a>> {
        match self.parse() {
            Ok(i) => Ok(EitherInt::I64(i)),
            Err(_) => Err(ValError::new(ErrorTypeDefaults::IntParsing, self)),
        }
    }

    fn ultra_strict_float(&'a self) -> ValResult<EitherFloat<'a>> {
        self.strict_float()
    }
    fn strict_float(&'a self) -> ValResult<EitherFloat<'a>> {
        str_as_float(self, self)
    }

    fn strict_decimal(&'a self, py: Python<'a>) -> ValResult<&'a PyAny> {
        create_decimal(self.to_object(py).into_ref(py), self, py)
    }

    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn strict_dict(&'a self) -> ValResult<GenericMapping<'a>> {
        Err(ValError::new(ErrorTypeDefaults::DictType, self))
    }

    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn strict_list(&'a self) -> ValResult<GenericIterable<'a>> {
        Err(ValError::new(ErrorTypeDefaults::ListType, self))
    }

    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn strict_tuple(&'a self) -> ValResult<GenericIterable<'a>> {
        Err(ValError::new(ErrorTypeDefaults::TupleType, self))
    }

    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn strict_set(&'a self) -> ValResult<GenericIterable<'a>> {
        Err(ValError::new(ErrorTypeDefaults::SetType, self))
    }

    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn strict_frozenset(&'a self) -> ValResult<GenericIterable<'a>> {
        Err(ValError::new(ErrorTypeDefaults::FrozenSetType, self))
    }

    fn extract_generic_iterable(&'a self) -> ValResult<GenericIterable<'a>> {
        Ok(GenericIterable::JsonString(self))
    }

    fn validate_iter(&self) -> ValResult<GenericIterator> {
        Ok(string_to_vec(self).into())
    }

    fn strict_date(&self) -> ValResult<EitherDate> {
        bytes_as_date(self, self.as_bytes())
    }

    fn strict_time(
        &self,
        microseconds_overflow_behavior: MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<EitherTime> {
        bytes_as_time(self, self.as_bytes(), microseconds_overflow_behavior)
    }

    fn strict_datetime(
        &self,
        microseconds_overflow_behavior: MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<EitherDateTime> {
        bytes_as_datetime(self, self.as_bytes(), microseconds_overflow_behavior)
    }

    fn strict_timedelta(
        &self,
        microseconds_overflow_behavior: MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<EitherTimedelta> {
        bytes_as_timedelta(self, self.as_bytes(), microseconds_overflow_behavior)
    }
}

impl BorrowInput for &'_ String {
    type Input<'a> = String where Self: 'a;
    fn borrow_input(&self) -> &Self::Input<'_> {
        self
    }
}

impl BorrowInput for String {
    type Input<'a> = String where Self: 'a;
    fn borrow_input(&self) -> &Self::Input<'_> {
        self
    }
}
