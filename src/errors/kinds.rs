use ahash::AHashMap;
use pyo3::once_cell::GILOnceCell;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use strum::{Display, EnumMessage, IntoEnumIterator};
use strum_macros::EnumIter;

use super::PydanticCustomError;

/// Definite each validation error.
/// NOTE: if an error has parameters:
/// * the variables in the message need to match the enum struct
/// * you need to add an entry to the `render` enum to render the error message as a template
/// * you need to add an entry to the `py_dict` enum to generate `ctx` for error messages
#[derive(Clone, Debug, Display, EnumMessage, EnumIter)]
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
    #[strum(message = "Field is frozen")]
    Frozen,
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
    // generic collection and iteration errors
    #[strum(message = "Input should be iterable")]
    IterableType,
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
        nan_value: String,
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
    #[strum(message = "Input should be a finite number")]
    FiniteNumber,
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
        value_error: PydanticCustomError,
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
        error: String,
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
        error: String,
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
        error: String,
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
        error: String,
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
            $error_kind.message_template()
            $(
                .replace(concat!("{", stringify!($value), "}"), $value)
            )*
        )
    };
}

macro_rules! to_string_render {
    ($error_kind:ident, $($value:ident),* $(,)?) => {
        Ok(
            $error_kind.message_template()
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
            dict.set_item::<&str, Py<PyAny>>(stringify!($value), $value.into_py($py))?;
        )*
        Ok(Some(dict.into_py($py)))
    }};
}

macro_rules! extract_context {
    ($kind:ident, $context:ident, $($key:ident: $type_:ty),* $(,)?) => {{
        let context = match $context {
            Some(context) => context,
            None => {
                let context_parts = [$(format!("{}: {}", stringify!($key), stringify!($type_)),)*];
                return Err(format!("{} requires context: {{{}}}", stringify!($kind), context_parts.join(", ")));
            }
        };
        Ok(Self::$kind{
            $(
                $key: context
                  .get_item(stringify!($key))
                  .ok_or(format!("{}: '{}' required in context", stringify!($kind), stringify!($key)))?
                  .extract::<$type_>()
                  .map_err(|_| format!("{}: '{}' context value must be a {}", stringify!($kind), stringify!($key), stringify!($type_)))?,
            )*
        })
    }};
}

fn plural_s(value: &usize) -> &'static str {
    if *value == 1 {
        ""
    } else {
        "s"
    }
}

static ERROR_KIND_LOOKUP: GILOnceCell<AHashMap<String, ErrorKind>> = GILOnceCell::new();

impl ErrorKind {
    pub fn new(py: Python, value: &str, ctx: Option<&PyDict>) -> Result<Self, String> {
        let lookup = ERROR_KIND_LOOKUP.get_or_init(py, Self::build_lookup);
        let error_kind = match lookup.get(value) {
            Some(error_kind) => error_kind.clone(),
            None => return Err(format!("Invalid error kind: '{}'", value)),
        };
        match error_kind {
            Self::InvalidJson { .. } => extract_context!(InvalidJson, ctx, error: String),
            Self::GetAttributeError { .. } => extract_context!(GetAttributeError, ctx, error: String),
            Self::ModelClassType { .. } => extract_context!(ModelClassType, ctx, class_name: String),
            Self::GreaterThan { .. } => extract_context!(GreaterThan, ctx, gt: String),
            Self::GreaterThanEqual { .. } => extract_context!(GreaterThanEqual, ctx, ge: String),
            Self::LessThan { .. } => extract_context!(LessThan, ctx, lt: String),
            Self::LessThanEqual { .. } => extract_context!(LessThanEqual, ctx, le: String),
            Self::TooShort { .. } => extract_context!(TooShort, ctx, min_length: usize, input_length: usize),
            Self::TooLong { .. } => extract_context!(TooLong, ctx, max_length: usize, input_length: usize),
            Self::StrTooShort { .. } => extract_context!(StrTooShort, ctx, min_length: usize),
            Self::StrTooLong { .. } => extract_context!(StrTooLong, ctx, max_length: usize),
            Self::StrPatternMismatch { .. } => extract_context!(StrPatternMismatch, ctx, pattern: String),
            Self::DictFromMapping { .. } => extract_context!(DictFromMapping, ctx, error: String),
            Self::IntNan { .. } => extract_context!(IntNan, ctx, nan_value: String),
            Self::IntMultipleOf { .. } => extract_context!(IntMultipleOf, ctx, multiple_of: i64),
            Self::IntGreaterThan { .. } => extract_context!(IntGreaterThan, ctx, gt: i64),
            Self::IntGreaterThanEqual { .. } => extract_context!(IntGreaterThanEqual, ctx, ge: i64),
            Self::IntLessThan { .. } => extract_context!(IntLessThan, ctx, lt: i64),
            Self::IntLessThanEqual { .. } => extract_context!(IntLessThanEqual, ctx, le: i64),
            Self::FloatMultipleOf { .. } => extract_context!(FloatMultipleOf, ctx, multiple_of: f64),
            Self::FloatGreaterThan { .. } => extract_context!(FloatGreaterThan, ctx, gt: f64),
            Self::FloatGreaterThanEqual { .. } => extract_context!(FloatGreaterThanEqual, ctx, ge: f64),
            Self::FloatLessThan { .. } => extract_context!(FloatLessThan, ctx, lt: f64),
            Self::FloatLessThanEqual { .. } => extract_context!(FloatLessThanEqual, ctx, le: f64),
            Self::BytesTooShort { .. } => extract_context!(BytesTooShort, ctx, min_length: usize),
            Self::BytesTooLong { .. } => extract_context!(BytesTooLong, ctx, max_length: usize),
            Self::ValueError { .. } => extract_context!(ValueError, ctx, error: String),
            Self::AssertionError { .. } => extract_context!(AssertionError, ctx, error: String),
            Self::LiteralSingleError { .. } => extract_context!(LiteralSingleError, ctx, expected: String),
            Self::LiteralMultipleError { .. } => extract_context!(LiteralMultipleError, ctx, expected: String),
            Self::DateParsing { .. } => extract_context!(DateParsing, ctx, error: String),
            Self::DateFromDatetimeParsing { .. } => extract_context!(DateFromDatetimeParsing, ctx, error: String),
            Self::TimeParsing { .. } => extract_context!(TimeParsing, ctx, error: String),
            Self::DateTimeParsing { .. } => extract_context!(DateTimeParsing, ctx, error: String),
            Self::DateTimeObjectInvalid { .. } => extract_context!(DateTimeObjectInvalid, ctx, error: String),
            Self::TimeDeltaParsing { .. } => extract_context!(TimeDeltaParsing, ctx, error: String),
            Self::IsInstanceOf { .. } => extract_context!(IsInstanceOf, ctx, class: String),
            Self::UnionTagInvalid { .. } => extract_context!(
                UnionTagInvalid,
                ctx,
                discriminator: String,
                tag: String,
                expected_tags: String
            ),
            Self::UnionTagNotFound { .. } => extract_context!(UnionTagNotFound, ctx, discriminator: String),
            _ => {
                if ctx.is_some() {
                    Err(format!("'{}' errors do not require context", value))
                } else {
                    Ok(error_kind)
                }
            }
        }
    }

    fn build_lookup() -> AHashMap<String, Self> {
        let mut lookup = AHashMap::new();
        for error_kind in Self::iter() {
            if !matches!(error_kind, Self::CustomError { .. }) {
                lookup.insert(error_kind.to_string(), error_kind);
            }
        }
        lookup
    }

    pub fn message_template(&self) -> &'static str {
        self.get_message().expect("ErrorKind with no strum message")
    }

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
            _ => Ok(self.message_template().to_string()),
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
