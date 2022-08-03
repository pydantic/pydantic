use pyo3::prelude::*;
use pyo3::types::PyDict;

use strum::{Display, EnumMessage};

use super::PydanticValueError;

/// Definite each validation error.
/// NOTE: if an error has parameters:
/// * the variables in the message need to match the enum struct
/// * you need to add an entry to the `render` enum to render the error message as a template
/// * you need to add an entry to the `py_dict` enum to generate `ctx` for error messages
#[derive(Display, EnumMessage, Clone)]
#[cfg_attr(debug_assertions, derive(Debug))]
#[strum(serialize_all = "snake_case")]
pub enum ErrorKind {
    #[strum(message = "Invalid input")]
    InvalidInput,
    #[strum(message = "Invalid JSON: {error}")]
    InvalidJson {
        error: String,
    },
    // ---------------------
    // recursion error
    #[strum(message = "Recursion error - cyclic reference detected")]
    RecursionLoop,
    // ---------------------
    // typed dict specific errors
    #[strum(message = "Input should be a valid dictionary or instance to extract fields from")]
    DictAttributesType,
    #[strum(message = "Field required")]
    Missing,
    #[strum(message = "Extra inputs are not permitted")]
    ExtraForbidden,
    #[strum(message = "Keys should be strings")]
    InvalidKey,
    #[strum(message = "Error extracting attribute: {error}")]
    GetAttributeError {
        error: String,
    },
    // ---------------------
    // model class specific errors
    #[strum(message = "Input should be an instance of {class_name}")]
    ModelClassType {
        class_name: String,
    },
    // ---------------------
    // None errors
    #[strum(message = "Input should be None/null")]
    NoneRequired,
    // boolean errors
    #[strum(message = "Input should be a valid boolean")]
    Bool,
    // ---------------------
    // generic comparison errors - used for all inequality comparisons except int and float which have their
    // own type, bounds arguments are Strings so they can be created from any type
    #[strum(message = "Input should be greater than {gt}")]
    GreaterThan {
        gt: String,
    },
    #[strum(message = "Input should be greater than or equal to {ge}")]
    GreaterThanEqual {
        ge: String,
    },
    #[strum(message = "Input should be less than {lt}")]
    LessThan {
        lt: String,
    },
    #[strum(message = "Input should be less than or equal to {le}")]
    LessThanEqual {
        le: String,
    },
    // ---------------------
    // generic length errors - used for everything with a length except strings and bytes which need custom messages
    #[strum(
        message = "Input should have at least {min_length} item{expected_plural}, got {input_length} item{input_plural}"
    )]
    TooShort {
        min_length: usize,
        input_length: usize,
    },
    #[strum(
        message = "Input should have at most {max_length} item{expected_plural}, got {input_length} item{input_plural}"
    )]
    TooLong {
        max_length: usize,
        input_length: usize,
    },
    // ---------------------
    // string errors
    #[strum(message = "Input should be a valid string")]
    StrType,
    #[strum(message = "Input should be a valid string, unable to parse raw data as a unicode string")]
    StrUnicode,
    #[strum(
        message = "String should have at least {min_length} characters",
        serialize = "too_short"
    )]
    StrTooShort {
        min_length: usize,
    },
    #[strum(
        message = "String should have at most {max_length} characters",
        serialize = "too_long"
    )]
    StrTooLong {
        max_length: usize,
    },
    #[strum(message = "String should match pattern '{pattern}'")]
    StrPatternMismatch {
        pattern: String,
    },
    // ---------------------
    // dict errors
    #[strum(message = "Input should be a valid dictionary")]
    DictType,
    #[strum(message = "Unable to convert mapping to a dictionary, error: {error}")]
    DictFromMapping {
        error: String,
    },
    // ---------------------
    // generic list-list errors
    #[strum(message = "Error iterating over object")]
    IterationError,
    // ---------------------
    // list errors
    #[strum(message = "Input should be a valid list/array")]
    ListType,
    // ---------------------
    // tuple errors
    #[strum(message = "Input should be a valid tuple")]
    TupleType,
    // ---------------------
    // set errors
    #[strum(message = "Input should be a valid set")]
    SetType,
    // ---------------------
    // bool errors
    #[strum(message = "Input should be a valid boolean")]
    BoolType,
    #[strum(message = "Input should be a valid boolean, unable to interpret input")]
    BoolParsing,
    // ---------------------
    // int errors
    #[strum(message = "Input should be a valid integer")]
    IntType,
    #[strum(message = "Input should be a valid integer, unable to parse string as an integer")]
    IntParsing,
    #[strum(message = "Input should be a valid integer, got a number with a fractional part")]
    IntFromFloat,
    #[strum(message = "Input should be a valid integer, got {nan_value}")]
    IntNan {
        nan_value: &'static str,
    },
    #[strum(serialize = "multiple_of", message = "Input should be a multiple of {multiple_of}")]
    IntMultipleOf {
        multiple_of: i64,
    },
    #[strum(serialize = "greater_than", message = "Input should be greater than {gt}")]
    IntGreaterThan {
        gt: i64,
    },
    #[strum(
        serialize = "greater_than_equal",
        message = "Input should be greater than or equal to {ge}"
    )]
    IntGreaterThanEqual {
        ge: i64,
    },
    #[strum(serialize = "less_than", message = "Input should be less than {lt}")]
    IntLessThan {
        lt: i64,
    },
    #[strum(
        serialize = "less_than_equal",
        message = "Input should be less than or equal to {le}"
    )]
    IntLessThanEqual {
        le: i64,
    },
    // ---------------------
    // float errors
    #[strum(message = "Input should be a valid number")]
    FloatType,
    #[strum(message = "Input should be a valid number, unable to parse string as an number")]
    FloatParsing,
    #[strum(serialize = "multiple_of", message = "Input should be a multiple of {multiple_of}")]
    FloatMultipleOf {
        multiple_of: f64,
    },
    #[strum(serialize = "greater_than", message = "Input should be greater than {gt}")]
    FloatGreaterThan {
        gt: f64,
    },
    #[strum(
        serialize = "greater_than_equal",
        message = "Input should be greater than or equal to {ge}"
    )]
    FloatGreaterThanEqual {
        ge: f64,
    },
    #[strum(serialize = "less_than", message = "Input should be less than {lt}")]
    FloatLessThan {
        lt: f64,
    },
    #[strum(
        serialize = "less_than_equal",
        message = "Input should be less than or equal to {le}"
    )]
    FloatLessThanEqual {
        le: f64,
    },
    // ---------------------
    // bytes errors
    #[strum(message = "Input should be a valid bytes")]
    BytesType,
    #[strum(message = "Data should have at least {min_length} bytes", serialize = "too_short")]
    BytesTooShort {
        min_length: usize,
    },
    #[strum(message = "Data should have at most {max_length} bytes", serialize = "too_long")]
    BytesTooLong {
        max_length: usize,
    },
    // ---------------------
    // python errors from functions
    #[strum(message = "Value error, {error}")]
    ValueError {
        error: String,
    },
    #[strum(message = "Assertion failed, {error}")]
    AssertionError {
        error: String,
    },
    // Note: strum message and serialize are not used here
    CustomError {
        value_error: PydanticValueError,
    },
    // ---------------------
    // literals
    #[strum(serialize = "literal_error", message = "Input should be {expected}")]
    LiteralSingleError {
        expected: String,
    },
    #[strum(serialize = "literal_error", message = "Input should be one of: {expected}")]
    LiteralMultipleError {
        expected: String,
    },
    // ---------------------
    // date errors
    #[strum(message = "Input should be a valid date")]
    DateType,
    #[strum(message = "Input should be a valid date in the format YYYY-MM-DD, {error}")]
    DateParsing {
        error: &'static str,
    },
    #[strum(message = "Input should be a valid date or datetime, {error}")]
    DateFromDatetimeParsing {
        error: String,
    },
    #[strum(message = "Datetimes provided to dates should have zero time - e.g. be exact dates")]
    DateFromDatetimeInexact,
    // ---------------------
    // date errors
    #[strum(message = "Input should be a valid time")]
    TimeType,
    #[strum(message = "Input should be in a valid time format, {error}")]
    TimeParsing {
        error: &'static str,
    },
    // ---------------------
    // datetime errors
    #[strum(serialize = "datetime_type", message = "Input should be a valid datetime")]
    DateTimeType,
    #[strum(
        serialize = "datetime_parsing",
        message = "Input should be a valid datetime, {error}"
    )]
    DateTimeParsing {
        error: &'static str,
    },
    #[strum(
        serialize = "datetime_object_invalid",
        message = "Invalid datetime object, got {error}"
    )]
    DateTimeObjectInvalid {
        error: String,
    },
    // ---------------------
    // timedelta errors
    #[strum(message = "Input should be a valid timedelta")]
    TimeDeltaType,
    #[strum(message = "Input should be a valid timedelta, {error}")]
    TimeDeltaParsing {
        error: &'static str,
    },
    // ---------------------
    // frozenset errors
    #[strum(message = "Input should be a valid frozenset")]
    FrozenSetType,
    // ---------------------
    // introspection types - e.g. isinstance, callable
    #[strum(message = "Input should be an instance of {class}")]
    IsInstanceOf {
        class: String,
    },
    #[strum(message = "Input should be callable")]
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
    UnionTagNotFound {
        discriminator: String,
    },
    // ---------------------
    // argument errors
    #[strum(message = "Arguments must be a tuple of (positional arguments, keyword arguments) or a plain dict")]
    ArgumentsType,
    #[strum(message = "Unexpected keyword argument")]
    UnexpectedKeywordArgument,
    #[strum(message = "Missing required keyword argument")]
    MissingKeywordArgument,
    #[strum(message = "Unexpected positional argument")]
    UnexpectedPositionalArgument,
    #[strum(message = "Missing required positional argument")]
    MissingPositionalArgument,
    #[strum(message = "Got multiple values for argument")]
    MultipleArgumentValues,
}

macro_rules! render {
    ($error_kind:ident, $($value:ident),* $(,)?) => {
        Ok(
            $error_kind.get_message().expect("ErrorKind with no strum message")
            $(
                .replace(concat!("{", stringify!($value), "}"), $value)
            )*
        )
    };
}

macro_rules! to_string_render {
    ($error_kind:ident, $($value:ident),* $(,)?) => {
        Ok(
            $error_kind.get_message().expect("ErrorKind with no strum message")
            $(
                .replace(concat!("{", stringify!($value), "}"), &$value.to_string())
            )*
        )
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

fn plural_s(value: &usize) -> &'static str {
    if *value == 1 {
        ""
    } else {
        "s"
    }
}

impl ErrorKind {
    pub fn kind(&self) -> String {
        match self {
            Self::CustomError { value_error } => value_error.kind(),
            _ => self.to_string(),
        }
    }

    pub fn render_message(&self, py: Python) -> PyResult<String> {
        match self {
            Self::InvalidJson { error } => render!(self, error),
            Self::GetAttributeError { error } => render!(self, error),
            Self::ModelClassType { class_name } => render!(self, class_name),
            Self::GreaterThan { gt } => render!(self, gt),
            Self::GreaterThanEqual { ge } => render!(self, ge),
            Self::LessThan { lt } => render!(self, lt),
            Self::LessThanEqual { le } => render!(self, le),
            Self::TooShort {
                min_length,
                input_length,
            } => {
                let expected_plural = plural_s(min_length);
                let input_plural = plural_s(input_length);
                to_string_render!(self, min_length, input_length, expected_plural, input_plural)
            }
            Self::TooLong {
                max_length,
                input_length,
            } => {
                let expected_plural = plural_s(max_length);
                let input_plural = plural_s(input_length);
                to_string_render!(self, max_length, input_length, expected_plural, input_plural)
            }
            Self::StrTooShort { min_length } => to_string_render!(self, min_length),
            Self::StrTooLong { max_length } => to_string_render!(self, max_length),
            Self::StrPatternMismatch { pattern } => render!(self, pattern),
            Self::DictFromMapping { error } => render!(self, error),
            Self::IntNan { nan_value } => render!(self, nan_value),
            Self::IntMultipleOf { multiple_of } => to_string_render!(self, multiple_of),
            Self::IntGreaterThan { gt } => to_string_render!(self, gt),
            Self::IntGreaterThanEqual { ge } => to_string_render!(self, ge),
            Self::IntLessThan { lt } => to_string_render!(self, lt),
            Self::IntLessThanEqual { le } => to_string_render!(self, le),
            Self::FloatMultipleOf { multiple_of } => to_string_render!(self, multiple_of),
            Self::FloatGreaterThan { gt } => to_string_render!(self, gt),
            Self::FloatGreaterThanEqual { ge } => to_string_render!(self, ge),
            Self::FloatLessThan { lt } => to_string_render!(self, lt),
            Self::FloatLessThanEqual { le } => to_string_render!(self, le),
            Self::BytesTooShort { min_length } => to_string_render!(self, min_length),
            Self::BytesTooLong { max_length } => to_string_render!(self, max_length),
            Self::ValueError { error } => render!(self, error),
            Self::AssertionError { error } => render!(self, error),
            Self::CustomError { value_error } => value_error.message(py),
            Self::LiteralSingleError { expected } => render!(self, expected),
            Self::LiteralMultipleError { expected } => render!(self, expected),
            Self::DateParsing { error } => render!(self, error),
            Self::DateFromDatetimeParsing { error } => render!(self, error),
            Self::TimeParsing { error } => render!(self, error),
            Self::DateTimeParsing { error } => render!(self, error),
            Self::DateTimeObjectInvalid { error } => render!(self, error),
            Self::TimeDeltaParsing { error } => render!(self, error),
            Self::IsInstanceOf { class } => render!(self, class),
            Self::UnionTagInvalid {
                discriminator,
                tag,
                expected_tags,
            } => render!(self, discriminator, tag, expected_tags),
            Self::UnionTagNotFound { discriminator } => render!(self, discriminator),
            _ => Ok(self.get_message().expect("ErrorKind with no strum message").to_string()),
        }
    }

    pub fn py_dict(&self, py: Python) -> PyResult<Option<Py<PyDict>>> {
        match self {
            Self::InvalidJson { error } => py_dict!(py, error),
            Self::GetAttributeError { error } => py_dict!(py, error),
            Self::ModelClassType { class_name } => py_dict!(py, class_name),
            Self::GreaterThan { gt } => py_dict!(py, gt),
            Self::GreaterThanEqual { ge } => py_dict!(py, ge),
            Self::LessThan { lt } => py_dict!(py, lt),
            Self::LessThanEqual { le } => py_dict!(py, le),
            Self::TooShort {
                min_length,
                input_length,
            } => py_dict!(py, min_length, input_length),
            Self::TooLong {
                max_length,
                input_length,
            } => py_dict!(py, max_length, input_length),
            Self::StrTooShort { min_length } => py_dict!(py, min_length),
            Self::StrTooLong { max_length } => py_dict!(py, max_length),
            Self::StrPatternMismatch { pattern } => py_dict!(py, pattern),
            Self::DictFromMapping { error } => py_dict!(py, error),
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
            Self::CustomError { value_error } => Ok(value_error.context(py)),
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
