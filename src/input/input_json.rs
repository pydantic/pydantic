use pyo3::prelude::*;

use crate::errors::{ErrorType, InputValue, LocItem, ValError, ValLineError, ValResult};

use super::datetime::{
    bytes_as_date, bytes_as_datetime, bytes_as_time, bytes_as_timedelta, float_as_datetime, float_as_duration,
    float_as_time, int_as_datetime, int_as_duration, int_as_time, EitherDate, EitherDateTime, EitherTime,
};
use super::input_abstract::InputType;
use super::parse_json::JsonArray;
use super::shared::{float_as_int, int_as_bool, map_json_err, str_as_bool, str_as_int};
use super::{
    EitherBytes, EitherString, EitherTimedelta, GenericArguments, GenericCollection, GenericIterator, GenericMapping,
    Input, JsonArgs, JsonInput, JsonType,
};

impl<'a> Input<'a> for JsonInput {
    fn get_type(&self) -> &'static InputType {
        &InputType::Json
    }

    /// This is required by since JSON object keys are always strings, I don't think it can be called
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn as_loc_item(&self) -> LocItem {
        match self {
            JsonInput::Int(i) => (*i).into(),
            JsonInput::String(s) => s.as_str().into(),
            v => format!("{v:?}").into(),
        }
    }

    fn as_error_value(&'a self) -> InputValue<'a> {
        InputValue::JsonInput(self)
    }

    fn is_none(&self) -> bool {
        matches!(self, JsonInput::Null)
    }

    fn input_is_instance(&self, _class: &PyAny, json_mask: u8) -> PyResult<bool> {
        if json_mask == 0 {
            Ok(false)
        } else {
            let json_type: JsonType = match self {
                JsonInput::Null => JsonType::Null,
                JsonInput::Bool(_) => JsonType::Bool,
                JsonInput::Int(_) => JsonType::Int,
                JsonInput::Float(_) => JsonType::Float,
                JsonInput::String(_) => JsonType::String,
                JsonInput::Array(_) => JsonType::Array,
                JsonInput::Object(_) => JsonType::Object,
            };
            Ok(json_type.matches(json_mask))
        }
    }

    fn validate_args(&'a self) -> ValResult<'a, GenericArguments<'a>> {
        match self {
            JsonInput::Object(object) => {
                if let Some(args) = object.get("__args__") {
                    if let Some(kwargs) = object.get("__kwargs__") {
                        // we only try this logic if there are only these two items in the dict
                        if object.len() == 2 {
                            let args = match args {
                                JsonInput::Null => Ok(None),
                                JsonInput::Array(args) => Ok(Some(args.as_slice())),
                                _ => Err(ValLineError::new_with_loc(
                                    ErrorType::PositionalArgumentsType,
                                    args,
                                    "__args__",
                                )),
                            };
                            let kwargs = match kwargs {
                                JsonInput::Null => Ok(None),
                                JsonInput::Object(kwargs) => Ok(Some(kwargs)),
                                _ => Err(ValLineError::new_with_loc(
                                    ErrorType::KeywordArgumentsType,
                                    kwargs,
                                    "__kwargs__",
                                )),
                            };

                            return match (args, kwargs) {
                                (Ok(args), Ok(kwargs)) => Ok(JsonArgs::new(args, kwargs).into()),
                                (Err(args_error), Err(kwargs_error)) => {
                                    return Err(ValError::LineErrors(vec![args_error, kwargs_error]))
                                }
                                (Err(error), _) => Err(ValError::LineErrors(vec![error])),
                                (_, Err(error)) => Err(ValError::LineErrors(vec![error])),
                            };
                        }
                    }
                }
                Ok(JsonArgs::new(None, Some(object)).into())
            }
            JsonInput::Array(array) => Ok(JsonArgs::new(Some(array), None).into()),
            _ => Err(ValError::new(ErrorType::ArgumentsType, self)),
        }
    }

    fn parse_json(&'a self) -> ValResult<'a, JsonInput> {
        match self {
            JsonInput::String(s) => serde_json::from_str(s.as_str()).map_err(|e| map_json_err(self, e)),
            _ => Err(ValError::new(ErrorType::JsonType, self)),
        }
    }

    fn strict_str(&'a self) -> ValResult<EitherString<'a>> {
        match self {
            JsonInput::String(s) => Ok(s.as_str().into()),
            _ => Err(ValError::new(ErrorType::StringType, self)),
        }
    }
    fn lax_str(&'a self) -> ValResult<EitherString<'a>> {
        match self {
            JsonInput::String(s) => Ok(s.as_str().into()),
            _ => Err(ValError::new(ErrorType::StringType, self)),
        }
    }

    fn validate_bytes(&'a self, _strict: bool) -> ValResult<EitherBytes<'a>> {
        match self {
            JsonInput::String(s) => Ok(s.as_bytes().into()),
            _ => Err(ValError::new(ErrorType::BytesType, self)),
        }
    }
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn strict_bytes(&'a self) -> ValResult<EitherBytes<'a>> {
        self.validate_bytes(false)
    }

    fn strict_bool(&self) -> ValResult<bool> {
        match self {
            JsonInput::Bool(b) => Ok(*b),
            _ => Err(ValError::new(ErrorType::BoolType, self)),
        }
    }
    fn lax_bool(&self) -> ValResult<bool> {
        match self {
            JsonInput::Bool(b) => Ok(*b),
            JsonInput::String(s) => str_as_bool(self, s),
            JsonInput::Int(int) => int_as_bool(self, *int),
            JsonInput::Float(float) => match float_as_int(self, *float) {
                Ok(int) => int_as_bool(self, int),
                _ => Err(ValError::new(ErrorType::BoolType, self)),
            },
            _ => Err(ValError::new(ErrorType::BoolType, self)),
        }
    }

    fn strict_int(&self) -> ValResult<i64> {
        match self {
            JsonInput::Int(i) => Ok(*i),
            _ => Err(ValError::new(ErrorType::IntType, self)),
        }
    }
    fn lax_int(&self) -> ValResult<i64> {
        match self {
            JsonInput::Bool(b) => match *b {
                true => Ok(1),
                false => Ok(0),
            },
            JsonInput::Int(i) => Ok(*i),
            JsonInput::Float(f) => float_as_int(self, *f),
            JsonInput::String(str) => str_as_int(self, str),
            _ => Err(ValError::new(ErrorType::IntType, self)),
        }
    }

    fn strict_float(&self) -> ValResult<f64> {
        match self {
            JsonInput::Float(f) => Ok(*f),
            JsonInput::Int(i) => Ok(*i as f64),
            _ => Err(ValError::new(ErrorType::FloatType, self)),
        }
    }
    fn lax_float(&self) -> ValResult<f64> {
        match self {
            JsonInput::Bool(b) => match *b {
                true => Ok(1.0),
                false => Ok(0.0),
            },
            JsonInput::Float(f) => Ok(*f),
            JsonInput::Int(i) => Ok(*i as f64),
            JsonInput::String(str) => match str.parse::<f64>() {
                Ok(i) => Ok(i),
                Err(_) => Err(ValError::new(ErrorType::FloatParsing, self)),
            },
            _ => Err(ValError::new(ErrorType::FloatType, self)),
        }
    }

    fn validate_dict(&'a self, _strict: bool) -> ValResult<GenericMapping<'a>> {
        match self {
            JsonInput::Object(dict) => Ok(dict.into()),
            _ => Err(ValError::new(ErrorType::DictType, self)),
        }
    }
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn strict_dict(&'a self) -> ValResult<GenericMapping<'a>> {
        self.validate_dict(false)
    }

    fn validate_list(&'a self, _strict: bool, _allow_any_iter: bool) -> ValResult<GenericCollection<'a>> {
        match self {
            JsonInput::Array(a) => Ok(a.into()),
            _ => Err(ValError::new(ErrorType::ListType, self)),
        }
    }
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn strict_list(&'a self) -> ValResult<GenericCollection<'a>> {
        self.validate_list(false, false)
    }

    fn validate_tuple(&'a self, _strict: bool) -> ValResult<GenericCollection<'a>> {
        // just as in set's case, List has to be allowed
        match self {
            JsonInput::Array(a) => Ok(a.into()),
            _ => Err(ValError::new(ErrorType::TupleType, self)),
        }
    }
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn strict_tuple(&'a self) -> ValResult<GenericCollection<'a>> {
        self.validate_tuple(false)
    }

    fn validate_set(&'a self, _strict: bool) -> ValResult<GenericCollection<'a>> {
        // we allow a list here since otherwise it would be impossible to create a set from JSON
        match self {
            JsonInput::Array(a) => Ok(a.into()),
            _ => Err(ValError::new(ErrorType::SetType, self)),
        }
    }
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn strict_set(&'a self) -> ValResult<GenericCollection<'a>> {
        self.validate_set(false)
    }

    fn validate_frozenset(&'a self, _strict: bool) -> ValResult<GenericCollection<'a>> {
        // we allow a list here since otherwise it would be impossible to create a frozenset from JSON
        match self {
            JsonInput::Array(a) => Ok(a.into()),
            _ => Err(ValError::new(ErrorType::FrozenSetType, self)),
        }
    }
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn strict_frozenset(&'a self) -> ValResult<GenericCollection<'a>> {
        self.validate_frozenset(false)
    }

    fn validate_iter(&self) -> ValResult<GenericIterator> {
        match self {
            JsonInput::Array(a) => Ok(a.clone().into()),
            JsonInput::String(s) => Ok(string_to_vec(s).into()),
            JsonInput::Object(object) => {
                // return keys iterator to match python's behavior
                let keys: Vec<JsonInput> = object.keys().map(|k| JsonInput::String(k.clone())).collect();
                Ok(keys.into())
            }
            _ => Err(ValError::new(ErrorType::IterableType, self)),
        }
    }

    fn validate_date(&self, _strict: bool) -> ValResult<EitherDate> {
        match self {
            JsonInput::String(v) => bytes_as_date(self, v.as_bytes()),
            _ => Err(ValError::new(ErrorType::DateType, self)),
        }
    }
    // NO custom `lax_date` implementation, if strict_date fails, the validator will fallback to lax_datetime
    // then check there's no remainder
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn strict_date(&self) -> ValResult<EitherDate> {
        self.validate_date(false)
    }

    fn strict_time(&self) -> ValResult<EitherTime> {
        match self {
            JsonInput::String(v) => bytes_as_time(self, v.as_bytes()),
            _ => Err(ValError::new(ErrorType::TimeType, self)),
        }
    }
    fn lax_time(&self) -> ValResult<EitherTime> {
        match self {
            JsonInput::String(v) => bytes_as_time(self, v.as_bytes()),
            JsonInput::Int(v) => int_as_time(self, *v, 0),
            JsonInput::Float(v) => float_as_time(self, *v),
            _ => Err(ValError::new(ErrorType::TimeType, self)),
        }
    }

    fn strict_datetime(&self) -> ValResult<EitherDateTime> {
        match self {
            JsonInput::String(v) => bytes_as_datetime(self, v.as_bytes()),
            _ => Err(ValError::new(ErrorType::DatetimeType, self)),
        }
    }
    fn lax_datetime(&self) -> ValResult<EitherDateTime> {
        match self {
            JsonInput::String(v) => bytes_as_datetime(self, v.as_bytes()),
            JsonInput::Int(v) => int_as_datetime(self, *v, 0),
            JsonInput::Float(v) => float_as_datetime(self, *v),
            _ => Err(ValError::new(ErrorType::DatetimeType, self)),
        }
    }

    fn strict_timedelta(&self) -> ValResult<EitherTimedelta> {
        match self {
            JsonInput::String(v) => bytes_as_timedelta(self, v.as_bytes()),
            _ => Err(ValError::new(ErrorType::TimeDeltaType, self)),
        }
    }
    fn lax_timedelta(&self) -> ValResult<EitherTimedelta> {
        match self {
            JsonInput::String(v) => bytes_as_timedelta(self, v.as_bytes()),
            JsonInput::Int(v) => Ok(int_as_duration(self, *v)?.into()),
            JsonInput::Float(v) => Ok(float_as_duration(self, *v)?.into()),
            _ => Err(ValError::new(ErrorType::TimeDeltaType, self)),
        }
    }
}

/// Required for Dict keys so the string can behave like an Input
impl<'a> Input<'a> for String {
    fn get_type(&self) -> &'static InputType {
        &InputType::String
    }

    fn as_loc_item(&self) -> LocItem {
        self.to_string().into()
    }

    fn as_error_value(&'a self) -> InputValue<'a> {
        InputValue::String(self)
    }

    #[cfg_attr(has_no_coverage, no_coverage)]
    fn is_none(&self) -> bool {
        false
    }

    fn input_is_instance(&self, _class: &PyAny, json_mask: u8) -> PyResult<bool> {
        if json_mask == 0 {
            Ok(false)
        } else {
            Ok(JsonType::String.matches(json_mask))
        }
    }

    #[cfg_attr(has_no_coverage, no_coverage)]
    fn validate_args(&'a self) -> ValResult<'a, GenericArguments<'a>> {
        Err(ValError::new(ErrorType::ArgumentsType, self))
    }

    fn parse_json(&'a self) -> ValResult<'a, JsonInput> {
        serde_json::from_str(self.as_str()).map_err(|e| map_json_err(self, e))
    }

    fn validate_str(&'a self, _strict: bool) -> ValResult<EitherString<'a>> {
        Ok(self.as_str().into())
    }
    fn strict_str(&'a self) -> ValResult<EitherString<'a>> {
        self.validate_str(false)
    }

    fn validate_bytes(&'a self, _strict: bool) -> ValResult<EitherBytes<'a>> {
        Ok(self.as_bytes().into())
    }
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn strict_bytes(&'a self) -> ValResult<EitherBytes<'a>> {
        self.validate_bytes(false)
    }

    fn strict_bool(&self) -> ValResult<bool> {
        Err(ValError::new(ErrorType::BoolType, self))
    }
    fn lax_bool(&self) -> ValResult<bool> {
        str_as_bool(self, self)
    }

    fn strict_int(&self) -> ValResult<i64> {
        Err(ValError::new(ErrorType::IntType, self))
    }
    fn lax_int(&self) -> ValResult<i64> {
        match self.parse() {
            Ok(i) => Ok(i),
            Err(_) => Err(ValError::new(ErrorType::IntParsing, self)),
        }
    }

    #[cfg_attr(has_no_coverage, no_coverage)]
    fn strict_float(&self) -> ValResult<f64> {
        Err(ValError::new(ErrorType::FloatType, self))
    }
    fn lax_float(&self) -> ValResult<f64> {
        match self.parse() {
            Ok(i) => Ok(i),
            Err(_) => Err(ValError::new(ErrorType::FloatParsing, self)),
        }
    }

    #[cfg_attr(has_no_coverage, no_coverage)]
    fn validate_dict(&'a self, _strict: bool) -> ValResult<GenericMapping<'a>> {
        Err(ValError::new(ErrorType::DictType, self))
    }
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn strict_dict(&'a self) -> ValResult<GenericMapping<'a>> {
        self.validate_dict(false)
    }

    #[cfg_attr(has_no_coverage, no_coverage)]
    fn validate_list(&'a self, _strict: bool, _allow_any_iter: bool) -> ValResult<GenericCollection<'a>> {
        Err(ValError::new(ErrorType::ListType, self))
    }
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn strict_list(&'a self) -> ValResult<GenericCollection<'a>> {
        self.validate_list(false, false)
    }

    #[cfg_attr(has_no_coverage, no_coverage)]
    fn validate_tuple(&'a self, _strict: bool) -> ValResult<GenericCollection<'a>> {
        Err(ValError::new(ErrorType::TupleType, self))
    }
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn strict_tuple(&'a self) -> ValResult<GenericCollection<'a>> {
        self.validate_tuple(false)
    }

    #[cfg_attr(has_no_coverage, no_coverage)]
    fn validate_set(&'a self, _strict: bool) -> ValResult<GenericCollection<'a>> {
        Err(ValError::new(ErrorType::SetType, self))
    }
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn strict_set(&'a self) -> ValResult<GenericCollection<'a>> {
        self.validate_set(false)
    }

    #[cfg_attr(has_no_coverage, no_coverage)]
    fn validate_frozenset(&'a self, _strict: bool) -> ValResult<GenericCollection<'a>> {
        Err(ValError::new(ErrorType::FrozenSetType, self))
    }
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn strict_frozenset(&'a self) -> ValResult<GenericCollection<'a>> {
        self.validate_frozenset(false)
    }

    fn validate_iter(&self) -> ValResult<GenericIterator> {
        Ok(string_to_vec(self).into())
    }

    fn validate_date(&self, _strict: bool) -> ValResult<EitherDate> {
        bytes_as_date(self, self.as_bytes())
    }
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn strict_date(&self) -> ValResult<EitherDate> {
        self.validate_date(false)
    }

    fn validate_time(&self, _strict: bool) -> ValResult<EitherTime> {
        bytes_as_time(self, self.as_bytes())
    }
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn strict_time(&self) -> ValResult<EitherTime> {
        self.validate_time(false)
    }

    fn validate_datetime(&self, _strict: bool) -> ValResult<EitherDateTime> {
        bytes_as_datetime(self, self.as_bytes())
    }
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn strict_datetime(&self) -> ValResult<EitherDateTime> {
        self.validate_datetime(false)
    }

    fn validate_timedelta(&self, _strict: bool) -> ValResult<EitherTimedelta> {
        bytes_as_timedelta(self, self.as_bytes())
    }
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn strict_timedelta(&self) -> ValResult<EitherTimedelta> {
        self.validate_timedelta(false)
    }
}

fn string_to_vec(s: &str) -> JsonArray {
    s.chars().map(|c| JsonInput::String(c.to_string())).collect()
}
