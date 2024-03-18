use std::borrow::Cow;

use jiter::{JsonArray, JsonValue};
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
use super::return_enums::ValidationMatch;
use super::shared::{float_as_int, int_as_bool, str_as_bool, str_as_float, str_as_int};
use super::{
    BorrowInput, EitherBytes, EitherFloat, EitherInt, EitherString, EitherTimedelta, GenericArguments, GenericIterable,
    GenericIterator, GenericMapping, Input, JsonArgs,
};

/// This is required but since JSON object keys are always strings, I don't think it can be called
impl From<&JsonValue> for LocItem {
    fn from(json_value: &JsonValue) -> Self {
        match json_value {
            JsonValue::Int(i) => (*i).into(),
            JsonValue::Str(s) => s.as_str().into(),
            v => format!("{v:?}").into(),
        }
    }
}

impl From<JsonValue> for LocItem {
    fn from(json_value: JsonValue) -> Self {
        (&json_value).into()
    }
}

impl<'py> Input<'py> for JsonValue {
    fn as_error_value(&self) -> InputValue {
        // cloning JsonValue is cheap due to use of Arc
        InputValue::Json(self.clone())
    }

    fn is_none(&self) -> bool {
        matches!(self, JsonValue::Null)
    }

    fn as_kwargs(&self, py: Python<'py>) -> Option<Bound<'py, PyDict>> {
        match self {
            JsonValue::Object(object) => {
                let dict = PyDict::new_bound(py);
                for (k, v) in object.iter() {
                    dict.set_item(k, v.to_object(py)).unwrap();
                }
                Some(dict)
            }
            _ => None,
        }
    }

    fn validate_args(&self) -> ValResult<GenericArguments<'_, 'py>> {
        match self {
            JsonValue::Object(object) => Ok(JsonArgs::new(None, Some(object)).into()),
            JsonValue::Array(array) => Ok(JsonArgs::new(Some(array), None).into()),
            _ => Err(ValError::new(ErrorTypeDefaults::ArgumentsType, self)),
        }
    }

    fn validate_dataclass_args<'a>(&'a self, class_name: &str) -> ValResult<GenericArguments<'a, 'py>> {
        match self {
            JsonValue::Object(object) => Ok(JsonArgs::new(None, Some(object)).into()),
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

    fn validate_str(&self, strict: bool, coerce_numbers_to_str: bool) -> ValResult<ValidationMatch<EitherString<'_>>> {
        // Justification for `strict` instead of `exact` is that in JSON strings can also
        // represent other datatypes such as UUID and date more exactly, so string is a
        // converting input
        // TODO: in V3 we may want to make JSON str always win if in union, for consistency,
        // see https://github.com/pydantic/pydantic-core/pull/867#discussion_r1386582501
        match self {
            JsonValue::Str(s) => Ok(ValidationMatch::strict(s.as_str().into())),
            JsonValue::Int(i) if !strict && coerce_numbers_to_str => Ok(ValidationMatch::lax(i.to_string().into())),
            JsonValue::BigInt(b) if !strict && coerce_numbers_to_str => Ok(ValidationMatch::lax(b.to_string().into())),
            JsonValue::Float(f) if !strict && coerce_numbers_to_str => Ok(ValidationMatch::lax(f.to_string().into())),
            _ => Err(ValError::new(ErrorTypeDefaults::StringType, self)),
        }
    }

    fn validate_bytes<'a>(&'a self, _strict: bool) -> ValResult<ValidationMatch<EitherBytes<'a, 'py>>> {
        match self {
            JsonValue::Str(s) => Ok(ValidationMatch::strict(s.as_bytes().into())),
            _ => Err(ValError::new(ErrorTypeDefaults::BytesType, self)),
        }
    }

    fn validate_bool(&self, strict: bool) -> ValResult<ValidationMatch<bool>> {
        match self {
            JsonValue::Bool(b) => Ok(ValidationMatch::exact(*b)),
            JsonValue::Str(s) if !strict => str_as_bool(self, s).map(ValidationMatch::lax),
            JsonValue::Int(int) if !strict => int_as_bool(self, *int).map(ValidationMatch::lax),
            JsonValue::Float(float) if !strict => match float_as_int(self, *float) {
                Ok(int) => int
                    .as_bool()
                    .ok_or_else(|| ValError::new(ErrorTypeDefaults::BoolParsing, self))
                    .map(ValidationMatch::lax),
                _ => Err(ValError::new(ErrorTypeDefaults::BoolType, self)),
            },
            _ => Err(ValError::new(ErrorTypeDefaults::BoolType, self)),
        }
    }

    fn validate_int(&self, strict: bool) -> ValResult<ValidationMatch<EitherInt<'_>>> {
        match self {
            JsonValue::Int(i) => Ok(ValidationMatch::exact(EitherInt::I64(*i))),
            JsonValue::BigInt(b) => Ok(ValidationMatch::exact(EitherInt::BigInt(b.clone()))),
            JsonValue::Bool(b) if !strict => Ok(ValidationMatch::lax(EitherInt::I64((*b).into()))),
            JsonValue::Float(f) if !strict => float_as_int(self, *f).map(ValidationMatch::lax),
            JsonValue::Str(str) if !strict => str_as_int(self, str).map(ValidationMatch::lax),
            _ => Err(ValError::new(ErrorTypeDefaults::IntType, self)),
        }
    }

    fn exact_str(&self) -> ValResult<EitherString<'_>> {
        match self {
            JsonValue::Str(s) => Ok(s.as_str().into()),
            _ => Err(ValError::new(ErrorTypeDefaults::StringType, self)),
        }
    }

    fn validate_float(&self, strict: bool) -> ValResult<ValidationMatch<EitherFloat<'_>>> {
        match self {
            JsonValue::Float(f) => Ok(ValidationMatch::exact(EitherFloat::F64(*f))),
            JsonValue::Int(i) => Ok(ValidationMatch::strict(EitherFloat::F64(*i as f64))),
            JsonValue::Bool(b) if !strict => Ok(ValidationMatch::lax(EitherFloat::F64(if *b { 1.0 } else { 0.0 }))),
            JsonValue::Str(str) if !strict => str_as_float(self, str).map(ValidationMatch::lax),
            _ => Err(ValError::new(ErrorTypeDefaults::FloatType, self)),
        }
    }

    fn strict_decimal(&self, py: Python<'py>) -> ValResult<Bound<'py, PyAny>> {
        match self {
            JsonValue::Float(f) => create_decimal(&PyString::new_bound(py, &f.to_string()), self),

            JsonValue::Str(..) | JsonValue::Int(..) | JsonValue::BigInt(..) => {
                create_decimal(self.to_object(py).bind(py), self)
            }
            _ => Err(ValError::new(ErrorTypeDefaults::DecimalType, self)),
        }
    }

    fn validate_dict<'a>(&'a self, _strict: bool) -> ValResult<GenericMapping<'a, 'py>> {
        match self {
            JsonValue::Object(dict) => Ok(dict.into()),
            _ => Err(ValError::new(ErrorTypeDefaults::DictType, self)),
        }
    }
    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn strict_dict<'a>(&'a self) -> ValResult<GenericMapping<'a, 'py>> {
        self.validate_dict(false)
    }

    fn validate_list<'a>(&'a self, _strict: bool) -> ValResult<GenericIterable<'a, 'py>> {
        match self {
            JsonValue::Array(a) => Ok(GenericIterable::JsonArray(a)),
            _ => Err(ValError::new(ErrorTypeDefaults::ListType, self)),
        }
    }
    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn strict_list<'a>(&'a self) -> ValResult<GenericIterable<'a, 'py>> {
        self.validate_list(false)
    }

    fn validate_tuple<'a>(&'a self, _strict: bool) -> ValResult<GenericIterable<'a, 'py>> {
        // just as in set's case, List has to be allowed
        match self {
            JsonValue::Array(a) => Ok(GenericIterable::JsonArray(a)),
            _ => Err(ValError::new(ErrorTypeDefaults::TupleType, self)),
        }
    }
    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn strict_tuple<'a>(&'a self) -> ValResult<GenericIterable<'a, 'py>> {
        self.validate_tuple(false)
    }

    fn validate_set<'a>(&'a self, _strict: bool) -> ValResult<GenericIterable<'a, 'py>> {
        // we allow a list here since otherwise it would be impossible to create a set from JSON
        match self {
            JsonValue::Array(a) => Ok(GenericIterable::JsonArray(a)),
            _ => Err(ValError::new(ErrorTypeDefaults::SetType, self)),
        }
    }
    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn strict_set<'a>(&'a self) -> ValResult<GenericIterable<'a, 'py>> {
        self.validate_set(false)
    }

    fn validate_frozenset<'a>(&'a self, _strict: bool) -> ValResult<GenericIterable<'a, 'py>> {
        // we allow a list here since otherwise it would be impossible to create a frozenset from JSON
        match self {
            JsonValue::Array(a) => Ok(GenericIterable::JsonArray(a)),
            _ => Err(ValError::new(ErrorTypeDefaults::FrozenSetType, self)),
        }
    }
    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn strict_frozenset<'a>(&'a self) -> ValResult<GenericIterable<'a, 'py>> {
        self.validate_frozenset(false)
    }

    fn extract_generic_iterable(&self) -> ValResult<GenericIterable<'_, 'py>> {
        match self {
            JsonValue::Array(a) => Ok(GenericIterable::JsonArray(a)),
            JsonValue::Str(s) => Ok(GenericIterable::JsonString(s)),
            JsonValue::Object(object) => Ok(GenericIterable::JsonObject(object)),
            _ => Err(ValError::new(ErrorTypeDefaults::IterableType, self)),
        }
    }

    fn validate_iter(&self) -> ValResult<GenericIterator> {
        match self {
            JsonValue::Array(a) => Ok(a.clone().into()),
            JsonValue::Str(s) => Ok(string_to_vec(s).into()),
            JsonValue::Object(object) => {
                // return keys iterator to match python's behavior
                let keys: JsonArray = JsonArray::new(object.keys().map(|k| JsonValue::Str(k.clone())).collect());
                Ok(keys.into())
            }
            _ => Err(ValError::new(ErrorTypeDefaults::IterableType, self)),
        }
    }

    fn validate_date(&self, _strict: bool) -> ValResult<ValidationMatch<EitherDate<'py>>> {
        match self {
            JsonValue::Str(v) => bytes_as_date(self, v.as_bytes()).map(ValidationMatch::strict),
            _ => Err(ValError::new(ErrorTypeDefaults::DateType, self)),
        }
    }
    fn validate_time(
        &self,
        strict: bool,
        microseconds_overflow_behavior: MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<ValidationMatch<EitherTime<'py>>> {
        match self {
            JsonValue::Str(v) => {
                bytes_as_time(self, v.as_bytes(), microseconds_overflow_behavior).map(ValidationMatch::strict)
            }
            JsonValue::Int(v) if !strict => int_as_time(self, *v, 0).map(ValidationMatch::lax),
            JsonValue::Float(v) if !strict => float_as_time(self, *v).map(ValidationMatch::lax),
            JsonValue::BigInt(_) if !strict => Err(ValError::new(
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

    fn validate_datetime(
        &self,
        strict: bool,
        microseconds_overflow_behavior: speedate::MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<ValidationMatch<EitherDateTime<'py>>> {
        match self {
            JsonValue::Str(v) => {
                bytes_as_datetime(self, v.as_bytes(), microseconds_overflow_behavior).map(ValidationMatch::strict)
            }
            JsonValue::Int(v) if !strict => int_as_datetime(self, *v, 0).map(ValidationMatch::lax),
            JsonValue::Float(v) if !strict => float_as_datetime(self, *v).map(ValidationMatch::lax),
            _ => Err(ValError::new(ErrorTypeDefaults::DatetimeType, self)),
        }
    }

    fn validate_timedelta(
        &self,
        strict: bool,
        microseconds_overflow_behavior: speedate::MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<ValidationMatch<EitherTimedelta<'py>>> {
        match self {
            JsonValue::Str(v) => {
                bytes_as_timedelta(self, v.as_bytes(), microseconds_overflow_behavior).map(ValidationMatch::strict)
            }
            JsonValue::Int(v) if !strict => {
                int_as_duration(self, *v).map(|duration| ValidationMatch::lax(duration.into()))
            }
            JsonValue::Float(v) if !strict => {
                float_as_duration(self, *v).map(|duration| ValidationMatch::lax(duration.into()))
            }
            _ => Err(ValError::new(ErrorTypeDefaults::TimeDeltaType, self)),
        }
    }
}

/// Required for JSON Object keys so the string can behave like an Input
impl<'py> Input<'py> for str {
    fn as_error_value(&self) -> InputValue {
        // Justification for the clone: this is on the error pathway and we are generally ok
        // with errors having a performance penalty
        InputValue::Json(JsonValue::Str(self.to_owned()))
    }

    fn as_kwargs(&self, _py: Python<'py>) -> Option<Bound<'py, PyDict>> {
        None
    }

    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn validate_args(&self) -> ValResult<GenericArguments<'_, 'py>> {
        Err(ValError::new(ErrorTypeDefaults::ArgumentsType, self))
    }

    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn validate_dataclass_args<'a>(&'a self, class_name: &str) -> ValResult<GenericArguments<'a, 'py>> {
        let class_name = class_name.to_string();
        Err(ValError::new(
            ErrorType::DataclassType {
                class_name,
                context: None,
            },
            self,
        ))
    }

    fn validate_str(
        &self,
        _strict: bool,
        _coerce_numbers_to_str: bool,
    ) -> ValResult<ValidationMatch<EitherString<'_>>> {
        // Justification for `strict` instead of `exact` is that in JSON strings can also
        // represent other datatypes such as UUID and date more exactly, so string is a
        // converting input
        // TODO: in V3 we may want to make JSON str always win if in union, for consistency,
        // see https://github.com/pydantic/pydantic-core/pull/867#discussion_r1386582501
        Ok(ValidationMatch::strict(self.into()))
    }

    fn validate_bytes<'a>(&'a self, _strict: bool) -> ValResult<ValidationMatch<EitherBytes<'a, 'py>>> {
        Ok(ValidationMatch::strict(self.as_bytes().into()))
    }

    fn validate_bool(&self, _strict: bool) -> ValResult<ValidationMatch<bool>> {
        str_as_bool(self, self).map(ValidationMatch::lax)
    }

    fn validate_int(&self, _strict: bool) -> ValResult<ValidationMatch<EitherInt<'_>>> {
        str_as_int(self, self).map(ValidationMatch::lax)
    }

    fn validate_float(&self, _strict: bool) -> ValResult<ValidationMatch<EitherFloat<'_>>> {
        str_as_float(self, self).map(ValidationMatch::lax)
    }

    fn strict_decimal(&self, py: Python<'py>) -> ValResult<Bound<'py, PyAny>> {
        create_decimal(self.to_object(py).bind(py), self)
    }

    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn strict_dict<'a>(&'a self) -> ValResult<GenericMapping<'a, 'py>> {
        Err(ValError::new(ErrorTypeDefaults::DictType, self))
    }

    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn strict_list<'a>(&'a self) -> ValResult<GenericIterable<'a, 'py>> {
        Err(ValError::new(ErrorTypeDefaults::ListType, self))
    }

    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn strict_tuple<'a>(&'a self) -> ValResult<GenericIterable<'a, 'py>> {
        Err(ValError::new(ErrorTypeDefaults::TupleType, self))
    }

    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn strict_set<'a>(&'a self) -> ValResult<GenericIterable<'a, 'py>> {
        Err(ValError::new(ErrorTypeDefaults::SetType, self))
    }

    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn strict_frozenset<'a>(&'a self) -> ValResult<GenericIterable<'a, 'py>> {
        Err(ValError::new(ErrorTypeDefaults::FrozenSetType, self))
    }

    fn extract_generic_iterable<'a>(&'a self) -> ValResult<GenericIterable<'a, 'py>> {
        Ok(GenericIterable::JsonString(self))
    }

    fn validate_iter(&self) -> ValResult<GenericIterator> {
        Ok(string_to_vec(self).into())
    }

    fn validate_date(&self, _strict: bool) -> ValResult<ValidationMatch<EitherDate<'py>>> {
        bytes_as_date(self, self.as_bytes()).map(ValidationMatch::lax)
    }

    fn validate_time(
        &self,
        _strict: bool,
        microseconds_overflow_behavior: MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<ValidationMatch<EitherTime<'py>>> {
        bytes_as_time(self, self.as_bytes(), microseconds_overflow_behavior).map(ValidationMatch::lax)
    }

    fn validate_datetime(
        &self,
        _strict: bool,
        microseconds_overflow_behavior: MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<ValidationMatch<EitherDateTime<'py>>> {
        bytes_as_datetime(self, self.as_bytes(), microseconds_overflow_behavior).map(ValidationMatch::lax)
    }

    fn validate_timedelta(
        &self,
        _strict: bool,
        microseconds_overflow_behavior: MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<ValidationMatch<EitherTimedelta<'py>>> {
        bytes_as_timedelta(self, self.as_bytes(), microseconds_overflow_behavior).map(ValidationMatch::lax)
    }
}

impl BorrowInput<'_> for &'_ String {
    type Input = str;
    fn borrow_input(&self) -> &Self::Input {
        self
    }
}

impl BorrowInput<'_> for String {
    type Input = str;
    fn borrow_input(&self) -> &Self::Input {
        self
    }
}

fn string_to_vec(s: &str) -> JsonArray {
    JsonArray::new(s.chars().map(|c| JsonValue::Str(c.to_string())).collect())
}
