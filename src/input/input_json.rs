use pyo3::types::PyType;

use crate::errors::{err_val_error, ErrorKind, InputValue, ValResult};

use super::datetime::{
    bytes_as_date, bytes_as_datetime, bytes_as_time, float_as_datetime, float_as_time, int_as_datetime, int_as_time,
    EitherDate, EitherDateTime, EitherTime,
};
use super::generics::{GenericMapping, GenericSequence};
use super::input_abstract::Input;
use super::parse_json::JsonInput;
use super::return_enums::EitherBytes;
use super::shared::{float_as_int, int_as_bool, str_as_bool, str_as_int};

impl<'a> Input<'a> for JsonInput {
    fn as_error_value(&'a self) -> InputValue<'a> {
        InputValue::JsonInput(self)
    }

    fn is_none(&self) -> bool {
        matches!(self, JsonInput::Null)
    }

    fn strict_str(&self) -> ValResult<String> {
        match self {
            JsonInput::String(s) => Ok(s.to_string()),
            _ => err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::StrType),
        }
    }

    fn lax_str(&self) -> ValResult<String> {
        match self {
            JsonInput::String(s) => Ok(s.to_string()),
            JsonInput::Int(int) => Ok(int.to_string()),
            JsonInput::Float(float) => Ok(float.to_string()),
            _ => err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::StrType),
        }
    }

    fn strict_bool(&self) -> ValResult<bool> {
        match self {
            JsonInput::Bool(b) => Ok(*b),
            _ => err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::BoolType),
        }
    }

    fn lax_bool(&self) -> ValResult<bool> {
        match self {
            JsonInput::Bool(b) => Ok(*b),
            JsonInput::String(s) => str_as_bool(self, s),
            JsonInput::Int(int) => int_as_bool(self, *int),
            // TODO float??
            _ => err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::BoolType),
        }
    }

    fn strict_int(&self) -> ValResult<i64> {
        match self {
            JsonInput::Int(i) => Ok(*i),
            _ => err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::IntType),
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
            _ => err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::IntType),
        }
    }

    fn strict_float(&self) -> ValResult<f64> {
        match self {
            JsonInput::Float(f) => Ok(*f),
            JsonInput::Int(i) => Ok(*i as f64),
            _ => err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::FloatType),
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
            JsonInput::String(str) => match str.parse() {
                Ok(i) => Ok(i),
                Err(_) => err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::FloatParsing),
            },
            _ => err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::FloatType),
        }
    }

    fn strict_model_check(&self, _class: &PyType) -> ValResult<bool> {
        Ok(false)
    }

    fn strict_dict<'data>(&'data self) -> ValResult<GenericMapping<'data>> {
        match self {
            JsonInput::Object(dict) => Ok(dict.into()),
            _ => err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::DictType),
        }
    }

    fn strict_list<'data>(&'data self) -> ValResult<GenericSequence<'data>> {
        match self {
            JsonInput::Array(a) => Ok(a.into()),
            _ => err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::ListType),
        }
    }

    fn strict_set<'data>(&'data self) -> ValResult<GenericSequence<'data>> {
        // we allow a list here since otherwise it would be impossible to create a set from JSON
        match self {
            JsonInput::Array(a) => Ok(a.into()),
            _ => err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::SetType),
        }
    }

    fn strict_bytes<'data>(&'data self) -> ValResult<EitherBytes<'data>> {
        match self {
            JsonInput::String(s) => Ok(EitherBytes::Rust(s.clone().into_bytes())),
            _ => err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::BytesType),
        }
    }

    fn strict_date(&self) -> ValResult<EitherDate> {
        match self {
            JsonInput::String(v) => bytes_as_date(self, v.as_bytes()),
            _ => err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::DateType),
        }
    }

    fn strict_time(&self) -> ValResult<EitherTime> {
        match self {
            JsonInput::String(v) => bytes_as_time(self, v.as_bytes()),
            _ => err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::TimeType),
        }
    }

    // NO custom `lax_date` implementation, if strict_date fails, the validator will fallback to lax_datetime
    // then check there's no remainder

    fn lax_time(&self) -> ValResult<EitherTime> {
        match self {
            JsonInput::String(v) => bytes_as_time(self, v.as_bytes()),
            JsonInput::Int(v) => int_as_time(self, *v, 0),
            JsonInput::Float(v) => float_as_time(self, *v),
            _ => err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::TimeType),
        }
    }

    fn strict_datetime(&self) -> ValResult<EitherDateTime> {
        match self {
            JsonInput::String(v) => bytes_as_datetime(self, v.as_bytes()),
            _ => err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::DateTimeType),
        }
    }

    fn lax_datetime(&self) -> ValResult<EitherDateTime> {
        match self {
            JsonInput::String(v) => bytes_as_datetime(self, v.as_bytes()),
            JsonInput::Int(v) => int_as_datetime(self, *v, 0),
            JsonInput::Float(v) => float_as_datetime(self, *v),
            _ => err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::DateTimeType),
        }
    }

    fn strict_tuple<'data>(&'data self) -> ValResult<GenericSequence<'data>> {
        // just as in set's case, List has to be allowed
        match self {
            JsonInput::Array(a) => Ok(a.into()),
            _ => err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::TupleType),
        }
    }
}

/// Required for Dict keys so the string can behave like an Input
impl<'a> Input<'a> for String {
    fn as_error_value(&'a self) -> InputValue<'a> {
        InputValue::String(self)
    }

    #[no_coverage]
    fn is_none(&self) -> bool {
        false
    }

    #[no_coverage]
    fn strict_str(&self) -> ValResult<String> {
        Ok(self.clone())
    }

    #[no_coverage]
    fn lax_str(&self) -> ValResult<String> {
        Ok(self.clone())
    }

    #[no_coverage]
    fn strict_bool(&self) -> ValResult<bool> {
        err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::BoolType)
    }

    #[no_coverage]
    fn lax_bool(&self) -> ValResult<bool> {
        str_as_bool(self, self)
    }

    #[no_coverage]
    fn strict_int(&self) -> ValResult<i64> {
        err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::IntType)
    }

    #[no_coverage]
    fn lax_int(&self) -> ValResult<i64> {
        match self.parse() {
            Ok(i) => Ok(i),
            Err(_) => err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::IntParsing),
        }
    }

    #[no_coverage]
    fn strict_float(&self) -> ValResult<f64> {
        err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::FloatType)
    }

    #[no_coverage]
    fn lax_float(&self) -> ValResult<f64> {
        match self.parse() {
            Ok(i) => Ok(i),
            Err(_) => err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::FloatParsing),
        }
    }

    #[no_coverage]
    fn strict_model_check(&self, _class: &PyType) -> ValResult<bool> {
        Ok(false)
    }

    #[no_coverage]
    fn strict_dict<'data>(&'data self) -> ValResult<GenericMapping<'data>> {
        err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::DictType)
    }

    #[no_coverage]
    fn strict_list<'data>(&'data self) -> ValResult<GenericSequence<'data>> {
        err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::ListType)
    }

    #[no_coverage]
    fn strict_set<'data>(&'data self) -> ValResult<GenericSequence<'data>> {
        err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::SetType)
    }

    fn strict_bytes<'data>(&'data self) -> ValResult<EitherBytes<'data>> {
        Ok(EitherBytes::Rust(self.clone().into_bytes()))
    }

    fn strict_date(&self) -> ValResult<EitherDate> {
        bytes_as_date(self, self.as_bytes())
    }

    fn strict_time(&self) -> ValResult<EitherTime> {
        bytes_as_time(self, self.as_bytes())
    }

    fn strict_datetime(&self) -> ValResult<EitherDateTime> {
        bytes_as_datetime(self, self.as_bytes())
    }

    #[no_coverage]
    fn strict_tuple<'data>(&'data self) -> ValResult<GenericSequence<'data>> {
        err_val_error!(input_value = self.as_error_value(), kind = ErrorKind::TupleType)
    }
}
