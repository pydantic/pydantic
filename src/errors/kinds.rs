use pyo3::prelude::*;
use pyo3::types::PyDict;

use strum::{Display, EnumMessage};

/// Definite each validation error.
/// NOTE: if an error has parameters:
/// * the variables in the message need to match the enum struct
/// * you need to add an entry to the `render` enum to render the error message as a template
/// * you need to add an entry to the `py_dict` enum to generate `ctx` for error messages
#[derive(Debug, Display, EnumMessage, Clone)]
#[strum(serialize_all = "snake_case")]
pub enum ErrorKind {
    #[strum(message = "Invalid input")]
    InvalidInput,
    #[strum(message = "Invalid JSON: {error}")]
    InvalidJson { error: String },
    // ---------------------
    // recursion error
    #[strum(message = "Recursion error - cyclic reference detected")]
    RecursionLoop,
    // ---------------------
    // typed dict specific errors
    #[strum(message = "Value must be a valid dictionary or instance to extract fields from")]
    DictAttributesType,
    #[strum(message = "Field required")]
    Missing,
    #[strum(message = "Extra values are not permitted")]
    ExtraForbidden,
    #[strum(message = "Model keys must be strings")]
    InvalidKey,
    #[strum(message = "Error extracting attribute: {error}")]
    GetAttributeError { error: String },
    // ---------------------
    // model class specific errors
    #[strum(message = "Value must be an instance of {class_name}")]
    ModelClassType { class_name: String },
    // ---------------------
    // None errors
    #[strum(message = "Value must be None/null")]
    NoneRequired,
    // boolean errors
    #[strum(message = "Value must be a valid boolean")]
    Bool,
    // ---------------------
    // generic comparison errors - used for all inequality comparisons except int and float which have their
    // own type, bounds arguments are Strings so they can be created from any type
    #[strum(message = "Value must be greater than {gt}")]
    GreaterThan { gt: String },
    #[strum(message = "Value must be greater than or equal to {ge}")]
    GreaterThanEqual { ge: String },
    #[strum(message = "Value must be less than {lt}")]
    LessThan { lt: String },
    #[strum(message = "Value must be less than or equal to {le}")]
    LessThanEqual { le: String },
    // ---------------------
    // generic length errors - used for everything with a length except strings and bytes which need custom messages
    #[strum(message = "Input must have at least {min_length} items")]
    TooShort { min_length: usize },
    #[strum(message = "Input must have at most {max_length} items")]
    TooLong { max_length: usize },
    // ---------------------
    // string errors
    #[strum(message = "Value must be a valid string")]
    StrType,
    #[strum(message = "Value must be a valid string, unable to parse raw data as a unicode string")]
    StrUnicode,
    #[strum(
        message = "String must have at least {min_length} characters",
        serialize = "too_short"
    )]
    StrTooShort { min_length: usize },
    #[strum(message = "String must have at most {max_length} characters", serialize = "too_long")]
    StrTooLong { max_length: usize },
    #[strum(message = "String must match pattern '{pattern}'")]
    StrPatternMismatch { pattern: String },
    // ---------------------
    // dict errors
    #[strum(message = "Value must be a valid dictionary")]
    DictType,
    #[strum(message = "Unable to convert mapping to a dictionary, error: {error}")]
    DictFromMapping { error: String },
    // ---------------------
    // list errors
    #[strum(message = "Value must be a valid list/array")]
    ListType,
    // ---------------------
    // tuple errors
    #[strum(message = "Value must be a valid tuple")]
    TupleType,
    #[strum(message = "Tuple must have exactly {expected_length} item{plural}")]
    TupleLengthMismatch { expected_length: usize, plural: bool },
    // ---------------------
    // set errors
    #[strum(message = "Value must be a valid set")]
    SetType,
    // ---------------------
    // bool errors
    #[strum(message = "Value must be a valid boolean")]
    BoolType,
    #[strum(message = "Value must be a valid boolean, unable to interpret input")]
    BoolParsing,
    // ---------------------
    // int errors
    #[strum(message = "Value must be a valid integer")]
    IntType,
    #[strum(message = "Value must be a valid integer, unable to parse string as an integer")]
    IntParsing,
    #[strum(message = "Value must be a valid integer, got a number with a fractional part")]
    IntFromFloat,
    #[strum(message = "Value must be a valid integer, got {nan_value}")]
    IntNan { nan_value: &'static str },
    #[strum(serialize = "multiple_of", message = "Value must be a multiple of {multiple_of}")]
    IntMultipleOf { multiple_of: i64 },
    #[strum(serialize = "greater_than", message = "Value must be greater than {gt}")]
    IntGreaterThan { gt: i64 },
    #[strum(
        serialize = "greater_than_equal",
        message = "Value must be greater than or equal to {ge}"
    )]
    IntGreaterThanEqual { ge: i64 },
    #[strum(serialize = "less_than", message = "Value must be less than {lt}")]
    IntLessThan { lt: i64 },
    #[strum(serialize = "less_than_equal", message = "Value must be less than or equal to {le}")]
    IntLessThanEqual { le: i64 },
    // ---------------------
    // float errors
    #[strum(message = "Value must be a valid number")]
    FloatType,
    #[strum(message = "Value must be a valid number, unable to parse string as an number")]
    FloatParsing,
    #[strum(serialize = "multiple_of", message = "Value must be a multiple of {multiple_of}")]
    FloatMultipleOf { multiple_of: f64 },
    #[strum(serialize = "greater_than", message = "Value must be greater than {gt}")]
    FloatGreaterThan { gt: f64 },
    #[strum(
        serialize = "greater_than_equal",
        message = "Value must be greater than or equal to {ge}"
    )]
    FloatGreaterThanEqual { ge: f64 },
    #[strum(serialize = "less_than", message = "Value must be less than {lt}")]
    FloatLessThan { lt: f64 },
    #[strum(serialize = "less_than_equal", message = "Value must be less than or equal to {le}")]
    FloatLessThanEqual { le: f64 },
    // ---------------------
    // bytes errors
    #[strum(message = "Value must be a valid bytes")]
    BytesType,
    #[strum(message = "Data must have at least {min_length} bytes", serialize = "too_short")]
    BytesTooShort { min_length: usize },
    #[strum(message = "Data must have at most {max_length} bytes", serialize = "too_long")]
    BytesTooLong { max_length: usize },
    // ---------------------
    // python errors from functions (the messages here will not be used as we sett message in these cases)
    #[strum(message = "Invalid value: {error}")]
    ValueError { error: String },
    #[strum(message = "Assertion failed: {error}")]
    AssertionError { error: String },
    // ---------------------
    // literals
    #[strum(serialize = "literal_error", message = "Value must be {expected}")]
    LiteralSingleError { expected: String },
    #[strum(serialize = "literal_error", message = "Value must be one of: {expected}")]
    LiteralMultipleError { expected: String },
    // ---------------------
    // date errors
    #[strum(message = "Value must be a valid date")]
    DateType,
    #[strum(message = "Value must be a valid date in the format YYYY-MM-DD, {error}")]
    DateParsing { error: &'static str },
    #[strum(message = "Value must be a valid date or datetime, {error}")]
    DateFromDatetimeParsing { error: String },
    #[strum(message = "Datetimes provided to dates must have zero time - e.g. be exact dates")]
    DateFromDatetimeInexact,
    // ---------------------
    // date errors
    #[strum(message = "Value must be a valid time")]
    TimeType,
    #[strum(message = "Value must be in a valid time format, {error}")]
    TimeParsing { error: &'static str },
    // ---------------------
    // datetime errors
    #[strum(serialize = "datetime_type", message = "Value must be a valid datetime")]
    DateTimeType,
    #[strum(serialize = "datetime_parsing", message = "Value must be a valid datetime, {error}")]
    DateTimeParsing { error: &'static str },
    #[strum(
        serialize = "datetime_object_invalid",
        message = "Invalid datetime object, got {error}"
    )]
    DateTimeObjectInvalid { error: String },
    // ---------------------
    // timedelta errors
    #[strum(message = "Value must be a valid timedelta")]
    TimeDeltaType,
    #[strum(message = "Value must be a valid timedelta, {error}")]
    TimeDeltaParsing { error: &'static str },
    // ---------------------
    // frozenset errors
    #[strum(message = "Value must be a valid frozenset")]
    FrozenSetType,
    // ---------------------
    // introspection types - e.g. isinstance, callable
    #[strum(message = "Input must be an instance of {class}")]
    IsInstanceOf { class: String },
    #[strum(message = "Input must be callable")]
    CallableType,
    // ---------------------
    // union errors
    #[strum(
        message = "Input tag '{tag}' found using {discriminator} does not match any of the expected tags: {expected_tags}"
    )]
    UnionTagInvalid {
        discriminator: String,
        tag: String,
        expected_tags: String,
    },
    #[strum(message = "Unable to extract tag using discriminator {discriminator}")]
    UnionTagNotFound { discriminator: String },
}

macro_rules! render {
    ($template:ident, $($value:ident),* $(,)?) => {
        $template
        $(
            .replace(concat!("{", stringify!($value), "}"), $value)
        )*
    };
}

macro_rules! to_string_render {
    ($template:ident, $($value:ident),* $(,)?) => {
        $template
        $(
            .replace(concat!("{", stringify!($value), "}"), $value.to_string().as_str())
        )*
    };
}

macro_rules! py_dict {
    ($py:ident, $($value:expr),* $(,)?) => {{
        let dict = PyDict::new($py);
        $(
        dict.set_item(stringify!($value), $value.into_py($py))?;
        )*
        Ok(Some(dict.into_py($py)))
    }};
}

impl ErrorKind {
    pub fn render(&self) -> String {
        let template: &'static str = self.get_message().expect("ErrorKind with no strum message");
        match self {
            Self::InvalidJson { error } => render!(template, error),
            Self::GetAttributeError { error } => render!(template, error),
            Self::ModelClassType { class_name } => render!(template, class_name),
            Self::GreaterThan { gt } => render!(template, gt),
            Self::GreaterThanEqual { ge } => render!(template, ge),
            Self::LessThan { lt } => render!(template, lt),
            Self::LessThanEqual { le } => render!(template, le),
            Self::TooShort { min_length } => to_string_render!(template, min_length),
            Self::TooLong { max_length } => to_string_render!(template, max_length),
            Self::StrTooShort { min_length } => to_string_render!(template, min_length),
            Self::StrTooLong { max_length } => to_string_render!(template, max_length),
            Self::StrPatternMismatch { pattern } => render!(template, pattern),
            Self::DictFromMapping { error } => render!(template, error),
            Self::TupleLengthMismatch {
                expected_length,
                plural,
            } => {
                let plural = if *plural { "s" } else { "" };
                to_string_render!(template, expected_length, plural)
            }
            Self::IntNan { nan_value } => render!(template, nan_value),
            Self::IntMultipleOf { multiple_of } => to_string_render!(template, multiple_of),
            Self::IntGreaterThan { gt } => to_string_render!(template, gt),
            Self::IntGreaterThanEqual { ge } => to_string_render!(template, ge),
            Self::IntLessThan { lt } => to_string_render!(template, lt),
            Self::IntLessThanEqual { le } => to_string_render!(template, le),
            Self::FloatMultipleOf { multiple_of } => to_string_render!(template, multiple_of),
            Self::FloatGreaterThan { gt } => to_string_render!(template, gt),
            Self::FloatGreaterThanEqual { ge } => to_string_render!(template, ge),
            Self::FloatLessThan { lt } => to_string_render!(template, lt),
            Self::FloatLessThanEqual { le } => to_string_render!(template, le),
            Self::BytesTooShort { min_length } => to_string_render!(template, min_length),
            Self::BytesTooLong { max_length } => to_string_render!(template, max_length),
            Self::ValueError { error } => render!(template, error),
            Self::AssertionError { error } => render!(template, error),
            Self::LiteralSingleError { expected } => render!(template, expected),
            Self::LiteralMultipleError { expected } => render!(template, expected),
            Self::DateParsing { error } => render!(template, error),
            Self::DateFromDatetimeParsing { error } => render!(template, error),
            Self::TimeParsing { error } => render!(template, error),
            Self::DateTimeParsing { error } => render!(template, error),
            Self::DateTimeObjectInvalid { error } => render!(template, error),
            Self::TimeDeltaParsing { error } => render!(template, error),
            Self::IsInstanceOf { class } => render!(template, class),
            Self::UnionTagInvalid {
                discriminator,
                tag,
                expected_tags,
            } => render!(template, discriminator, tag, expected_tags),
            Self::UnionTagNotFound { discriminator } => render!(template, discriminator),
            _ => template.to_string(),
        }
    }

    pub fn py_dict(&self, py: Python) -> PyResult<Option<PyObject>> {
        match self {
            Self::InvalidJson { error } => py_dict!(py, error),
            Self::GetAttributeError { error } => py_dict!(py, error),
            Self::ModelClassType { class_name } => py_dict!(py, class_name),
            Self::GreaterThan { gt } => py_dict!(py, gt),
            Self::GreaterThanEqual { ge } => py_dict!(py, ge),
            Self::LessThan { lt } => py_dict!(py, lt),
            Self::LessThanEqual { le } => py_dict!(py, le),
            Self::TooShort { min_length } => py_dict!(py, min_length),
            Self::TooLong { max_length } => py_dict!(py, max_length),
            Self::StrTooShort { min_length } => py_dict!(py, min_length),
            Self::StrTooLong { max_length } => py_dict!(py, max_length),
            Self::StrPatternMismatch { pattern } => py_dict!(py, pattern),
            Self::DictFromMapping { error } => py_dict!(py, error),
            Self::TupleLengthMismatch {
                expected_length,
                plural,
            } => py_dict!(py, expected_length, plural),
            Self::IntNan { nan_value } => py_dict!(py, nan_value),
            Self::IntMultipleOf { multiple_of } => py_dict!(py, multiple_of),
            Self::IntGreaterThan { gt } => py_dict!(py, gt),
            Self::IntGreaterThanEqual { ge } => py_dict!(py, ge),
            Self::IntLessThan { lt } => py_dict!(py, lt),
            Self::IntLessThanEqual { le } => py_dict!(py, le),
            Self::FloatMultipleOf { multiple_of } => py_dict!(py, multiple_of),
            Self::FloatGreaterThan { gt } => py_dict!(py, gt),
            Self::FloatGreaterThanEqual { ge } => py_dict!(py, ge),
            Self::FloatLessThan { lt } => py_dict!(py, lt),
            Self::FloatLessThanEqual { le } => py_dict!(py, le),
            Self::BytesTooShort { min_length } => py_dict!(py, min_length),
            Self::BytesTooLong { max_length } => py_dict!(py, max_length),
            Self::ValueError { error } => py_dict!(py, error),
            Self::AssertionError { error } => py_dict!(py, error),
            Self::LiteralSingleError { expected } => py_dict!(py, expected),
            Self::LiteralMultipleError { expected } => py_dict!(py, expected),
            Self::DateParsing { error } => py_dict!(py, error),
            Self::DateFromDatetimeParsing { error } => py_dict!(py, error),
            Self::TimeParsing { error } => py_dict!(py, error),
            Self::DateTimeParsing { error } => py_dict!(py, error),
            Self::DateTimeObjectInvalid { error } => py_dict!(py, error),
            Self::TimeDeltaParsing { error } => py_dict!(py, error),
            Self::IsInstanceOf { class } => py_dict!(py, class),
            Self::UnionTagInvalid {
                discriminator,
                tag,
                expected_tags,
            } => py_dict!(py, discriminator, tag, expected_tags),
            Self::UnionTagNotFound { discriminator } => py_dict!(py, discriminator),
            _ => Ok(None),
        }
    }
}
