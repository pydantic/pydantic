use std::borrow::Cow;
use std::fmt;

use ahash::AHashMap;
use pyo3::exceptions::{PyKeyError, PyTypeError};
use pyo3::once_cell::GILOnceCell;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use crate::build_tools::{py_err, py_error_type};
use strum::{Display, EnumMessage, IntoEnumIterator};
use strum_macros::EnumIter;

use super::PydanticCustomError;

#[pyfunction]
pub fn list_all_errors(py: Python) -> PyResult<&PyList> {
    let mut errors: Vec<&PyDict> = Vec::with_capacity(100);
    for error_type in ErrorType::iter() {
        if !matches!(error_type, ErrorType::CustomError { .. }) {
            let d = PyDict::new(py);
            d.set_item("type", error_type.to_string())?;
            d.set_item("message_template", error_type.message_template())?;
            d.set_item("example_message", error_type.render_message(py)?)?;
            d.set_item("example_context", error_type.py_dict(py)?)?;
            errors.push(d);
        }
    }
    Ok(PyList::new(py, errors))
}

/// Definite each validation error.
/// NOTE: if an error has parameters:
/// * the variables in the message need to match the enum struct
/// * you need to add an entry to the `render` enum to render the error message as a template
/// * you need to add an entry to the `py_dict` enum to generate `ctx` for error messages
#[derive(Clone, Debug, Display, EnumMessage, EnumIter)]
#[strum(serialize_all = "snake_case")]
pub enum ErrorType {
    #[strum(message = "Invalid JSON: {error}")]
    JsonInvalid {
        error: String,
    },
    #[strum(message = "JSON input should be string, bytes or bytearray")]
    JsonType,
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
        gt: Number,
    },
    #[strum(message = "Input should be greater than or equal to {ge}")]
    GreaterThanEqual {
        ge: Number,
    },
    #[strum(message = "Input should be less than {lt}")]
    LessThan {
        lt: Number,
    },
    #[strum(message = "Input should be less than or equal to {le}")]
    LessThanEqual {
        le: Number,
    },
    #[strum(message = "Input should be a multiple of {multiple_of}")]
    MultipleOf {
        multiple_of: Number,
    },
    #[strum(message = "Input should be a finite number")]
    FiniteNumber,
    // ---------------------
    // generic length errors - used for everything with a length except strings and bytes which need custom messages
    #[strum(
        message = "{field_type} should have at least {min_length} item{expected_plural} after validation, not {actual_length}"
    )]
    TooShort {
        field_type: String,
        min_length: usize,
        actual_length: usize,
    },
    #[strum(
        message = "{field_type} should have at most {max_length} item{expected_plural} after validation, not {actual_length}"
    )]
    TooLong {
        field_type: String,
        max_length: usize,
        actual_length: usize,
    },
    // ---------------------
    // generic collection and iteration errors
    #[strum(message = "Input should be iterable")]
    IterableType,
    #[strum(message = "Error iterating over object, error: {error}")]
    IterationError {
        error: String,
    },
    // ---------------------
    // string errors
    #[strum(message = "Input should be a valid string")]
    StringType,
    #[strum(message = "Input should be a string, not an instance of a subclass of str")]
    StringSubType,
    #[strum(message = "Input should be a valid string, unable to parse raw data as a unicode string")]
    StringUnicode,
    #[strum(message = "String should have at least {min_length} characters")]
    StringTooShort {
        min_length: usize,
    },
    #[strum(message = "String should have at most {max_length} characters")]
    StringTooLong {
        max_length: usize,
    },
    #[strum(message = "String should match pattern '{pattern}'")]
    StringPatternMismatch {
        pattern: String,
    },
    // ---------------------
    // dict errors
    #[strum(message = "Input should be a valid dictionary")]
    DictType,
    #[strum(message = "Input should be a valid mapping, error: {error}")]
    MappingType {
        error: Cow<'static, str>,
    },
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
    // ---------------------
    // float errors
    #[strum(message = "Input should be a valid number")]
    FloatType,
    #[strum(message = "Input should be a valid number, unable to parse string as an number")]
    FloatParsing,
    // ---------------------
    // bytes errors
    #[strum(message = "Input should be a valid bytes")]
    BytesType,
    #[strum(message = "Data should have at least {min_length} bytes")]
    BytesTooShort {
        min_length: usize,
    },
    #[strum(message = "Data should have at most {max_length} bytes")]
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
    #[strum(message = "Input should be {expected}")]
    LiteralError {
        expected: String,
    },
    // ---------------------
    // date errors
    #[strum(message = "Input should be a valid date")]
    DateType,
    #[strum(message = "Input should be a valid date in the format YYYY-MM-DD, {error}")]
    DateParsing {
        error: Cow<'static, str>,
    },
    #[strum(message = "Input should be a valid date or datetime, {error}")]
    DateFromDatetimeParsing {
        error: String,
    },
    #[strum(message = "Datetimes provided to dates should have zero time - e.g. be exact dates")]
    DateFromDatetimeInexact,
    #[strum(message = "Date should be in the past")]
    DatePast,
    #[strum(message = "Date should be in the future")]
    DateFuture,
    // ---------------------
    // date errors
    #[strum(message = "Input should be a valid time")]
    TimeType,
    #[strum(message = "Input should be in a valid time format, {error}")]
    TimeParsing {
        error: Cow<'static, str>,
    },
    // ---------------------
    // datetime errors
    #[strum(message = "Input should be a valid datetime")]
    DatetimeType,
    #[strum(message = "Input should be a valid datetime, {error}")]
    DatetimeParsing {
        error: Cow<'static, str>,
    },
    #[strum(message = "Invalid datetime object, got {error}")]
    DatetimeObjectInvalid {
        error: String,
    },
    #[strum(message = "Datetime should be in the past")]
    DatetimePast,
    #[strum(message = "Datetime should be in the future")]
    DatetimeFuture,
    #[strum(message = "Datetime should have timezone info")]
    DatetimeAware,
    #[strum(message = "Datetime should not have timezone info")]
    DatetimeNaive,
    // ---------------------
    // timedelta errors
    #[strum(message = "Input should be a valid timedelta")]
    TimeDeltaType,
    #[strum(message = "Input should be a valid timedelta, {error}")]
    TimeDeltaParsing {
        error: Cow<'static, str>,
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
    #[strum(message = "Input should be a subclass of {class}")]
    IsSubclassOf {
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
    #[strum(message = "Arguments must be a tuple, list or a dictionary")]
    ArgumentsType,
    #[strum(message = "Positional arguments must be a list or tuple")]
    PositionalArgumentsType,
    #[strum(message = "Keyword arguments must be a dictionary")]
    KeywordArgumentsType,
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
    // ---------------------
    // URL errors
    #[strum(message = "URL input should be a string or URL")]
    UrlType,
    #[strum(message = "Input should be a valid URL, {error}")]
    UrlParsing {
        // would be great if this could be a static cow, waiting for https://github.com/servo/rust-url/issues/801
        error: String,
    },
    #[strum(message = "Input violated strict URL syntax rules, {error}")]
    UrlSyntaxViolation {
        error: Cow<'static, str>,
    },
    #[strum(message = "URL should have at most {max_length} characters")]
    UrlTooLong {
        max_length: usize,
    },
    #[strum(message = "URL scheme should be {expected_schemes}")]
    UrlScheme {
        expected_schemes: String,
    },
}

macro_rules! render {
    ($error_type:ident, $($value:ident),* $(,)?) => {
        Ok(
            $error_type.message_template()
            $(
                .replace(concat!("{", stringify!($value), "}"), $value)
            )*
        )
    };
}

macro_rules! to_string_render {
    ($error_type:ident, $($value:ident),* $(,)?) => {
        Ok(
            $error_type.message_template()
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
            dict.set_item::<&str, Py<PyAny>>(stringify!($value), $value.to_object($py))?;
        )*
        Ok(Some(dict.into_py($py)))
    }};
}

fn do_nothing<T>(v: T) -> T {
    v
}

macro_rules! extract_context {
    ($type:ident, $context:ident, $($key:ident: $type_:ty),* $(,)?) => {
        extract_context!(do_nothing, $type, $context, $($key: $type_,)*)
    };
    ($function:path, $type:ident, $context:ident, $($key:ident: $type_:ty),* $(,)?) => {{
        let context = match $context {
            Some(context) => context,
            None => {
                let context_parts = [$(format!("{}: {}", stringify!($key), stringify!($type_)),)*];
                return py_err!(PyTypeError; "{} requires context: {{{}}}", stringify!($type), context_parts.join(", "));
            }
        };
        Ok(Self::$type{
            $(
                $key: $function(
                    context
                    .get_item(stringify!($key))
                    .ok_or(py_error_type!(PyTypeError; "{}: '{}' required in context", stringify!($type), stringify!($key)))?
                    .extract::<$type_>()
                    .map_err(|_| py_error_type!(PyTypeError; "{}: '{}' context value must be a {}", stringify!($type), stringify!($key), stringify!($type_)))?
                ),
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

static ERROR_TYPE_LOOKUP: GILOnceCell<AHashMap<String, ErrorType>> = GILOnceCell::new();

impl ErrorType {
    /// create an new ErrorType from python, no_coverage since coverage doesn't work properly here due to the macro
    #[cfg_attr(has_no_coverage, no_coverage)]
    pub fn new(py: Python, value: &str, ctx: Option<&PyDict>) -> PyResult<Self> {
        let lookup = ERROR_TYPE_LOOKUP.get_or_init(py, Self::build_lookup);
        let error_type = match lookup.get(value) {
            Some(error_type) => error_type.clone(),
            None => return py_err!(PyKeyError; "Invalid error type: '{}'", value),
        };
        match error_type {
            Self::JsonInvalid { .. } => extract_context!(JsonInvalid, ctx, error: String),
            Self::GetAttributeError { .. } => extract_context!(GetAttributeError, ctx, error: String),
            Self::ModelClassType { .. } => extract_context!(ModelClassType, ctx, class_name: String),
            Self::GreaterThan { .. } => extract_context!(GreaterThan, ctx, gt: Number),
            Self::GreaterThanEqual { .. } => extract_context!(GreaterThanEqual, ctx, ge: Number),
            Self::LessThan { .. } => extract_context!(LessThan, ctx, lt: Number),
            Self::LessThanEqual { .. } => extract_context!(LessThanEqual, ctx, le: Number),
            Self::MultipleOf { .. } => extract_context!(MultipleOf, ctx, multiple_of: Number),
            Self::TooShort { .. } => extract_context!(
                TooShort,
                ctx,
                field_type: String,
                min_length: usize,
                actual_length: usize
            ),
            Self::TooLong { .. } => extract_context!(
                TooLong,
                ctx,
                field_type: String,
                max_length: usize,
                actual_length: usize
            ),
            Self::IterationError { .. } => extract_context!(IterationError, ctx, error: String),
            Self::StringTooShort { .. } => extract_context!(StringTooShort, ctx, min_length: usize),
            Self::StringTooLong { .. } => extract_context!(StringTooLong, ctx, max_length: usize),
            Self::StringPatternMismatch { .. } => extract_context!(StringPatternMismatch, ctx, pattern: String),
            Self::MappingType { .. } => extract_context!(Cow::Owned, MappingType, ctx, error: String),
            Self::BytesTooShort { .. } => extract_context!(BytesTooShort, ctx, min_length: usize),
            Self::BytesTooLong { .. } => extract_context!(BytesTooLong, ctx, max_length: usize),
            Self::ValueError { .. } => extract_context!(ValueError, ctx, error: String),
            Self::AssertionError { .. } => extract_context!(AssertionError, ctx, error: String),
            Self::LiteralError { .. } => extract_context!(LiteralError, ctx, expected: String),
            Self::DateParsing { .. } => extract_context!(Cow::Owned, DateParsing, ctx, error: String),
            Self::DateFromDatetimeParsing { .. } => extract_context!(DateFromDatetimeParsing, ctx, error: String),
            Self::TimeParsing { .. } => extract_context!(Cow::Owned, TimeParsing, ctx, error: String),
            Self::DatetimeParsing { .. } => extract_context!(Cow::Owned, DatetimeParsing, ctx, error: String),
            Self::DatetimeObjectInvalid { .. } => extract_context!(DatetimeObjectInvalid, ctx, error: String),
            Self::TimeDeltaParsing { .. } => extract_context!(Cow::Owned, TimeDeltaParsing, ctx, error: String),
            Self::IsInstanceOf { .. } => extract_context!(IsInstanceOf, ctx, class: String),
            Self::IsSubclassOf { .. } => extract_context!(IsSubclassOf, ctx, class: String),
            Self::UnionTagInvalid { .. } => extract_context!(
                UnionTagInvalid,
                ctx,
                discriminator: String,
                tag: String,
                expected_tags: String
            ),
            Self::UnionTagNotFound { .. } => extract_context!(UnionTagNotFound, ctx, discriminator: String),
            Self::UrlParsing { .. } => extract_context!(UrlParsing, ctx, error: String),
            Self::UrlSyntaxViolation { .. } => extract_context!(Cow::Owned, UrlSyntaxViolation, ctx, error: String),
            Self::UrlTooLong { .. } => extract_context!(UrlTooLong, ctx, max_length: usize),
            Self::UrlScheme { .. } => extract_context!(UrlScheme, ctx, expected_schemes: String),
            _ => {
                if ctx.is_some() {
                    py_err!(PyTypeError; "'{}' errors do not require context", value)
                } else {
                    Ok(error_type)
                }
            }
        }
    }

    pub fn valid_type(py: Python, error_type: &str) -> bool {
        let lookup = ERROR_TYPE_LOOKUP.get_or_init(py, Self::build_lookup);
        lookup.contains_key(error_type)
    }

    fn build_lookup() -> AHashMap<String, Self> {
        let mut lookup = AHashMap::new();
        for error_type in Self::iter() {
            if !matches!(error_type, Self::CustomError { .. }) {
                lookup.insert(error_type.to_string(), error_type);
            }
        }
        lookup
    }

    pub fn message_template(&self) -> &'static str {
        self.get_message().expect("ErrorType with no strum message")
    }

    pub fn type_string(&self) -> String {
        match self {
            Self::CustomError { value_error } => value_error.error_type(),
            _ => self.to_string(),
        }
    }

    pub fn render_message(&self, py: Python) -> PyResult<String> {
        match self {
            Self::JsonInvalid { error } => render!(self, error),
            Self::GetAttributeError { error } => render!(self, error),
            Self::ModelClassType { class_name } => render!(self, class_name),
            Self::GreaterThan { gt } => to_string_render!(self, gt),
            Self::GreaterThanEqual { ge } => to_string_render!(self, ge),
            Self::LessThan { lt } => to_string_render!(self, lt),
            Self::LessThanEqual { le } => to_string_render!(self, le),
            Self::MultipleOf { multiple_of } => to_string_render!(self, multiple_of),
            Self::TooShort {
                field_type,
                min_length,
                actual_length,
            } => {
                let expected_plural = plural_s(min_length);
                to_string_render!(self, field_type, min_length, actual_length, expected_plural)
            }
            Self::TooLong {
                field_type,
                max_length,
                actual_length,
            } => {
                let expected_plural = plural_s(max_length);
                to_string_render!(self, field_type, max_length, actual_length, expected_plural)
            }
            Self::IterationError { error } => render!(self, error),
            Self::StringTooShort { min_length } => to_string_render!(self, min_length),
            Self::StringTooLong { max_length } => to_string_render!(self, max_length),
            Self::StringPatternMismatch { pattern } => render!(self, pattern),
            Self::MappingType { error } => render!(self, error),
            Self::BytesTooShort { min_length } => to_string_render!(self, min_length),
            Self::BytesTooLong { max_length } => to_string_render!(self, max_length),
            Self::ValueError { error } => render!(self, error),
            Self::AssertionError { error } => render!(self, error),
            Self::CustomError { value_error } => value_error.message(py),
            Self::LiteralError { expected } => render!(self, expected),
            Self::DateParsing { error } => render!(self, error),
            Self::DateFromDatetimeParsing { error } => render!(self, error),
            Self::TimeParsing { error } => render!(self, error),
            Self::DatetimeParsing { error } => render!(self, error),
            Self::DatetimeObjectInvalid { error } => render!(self, error),
            Self::TimeDeltaParsing { error } => render!(self, error),
            Self::IsInstanceOf { class } => render!(self, class),
            Self::IsSubclassOf { class } => render!(self, class),
            Self::UnionTagInvalid {
                discriminator,
                tag,
                expected_tags,
            } => render!(self, discriminator, tag, expected_tags),
            Self::UnionTagNotFound { discriminator } => render!(self, discriminator),
            Self::UrlParsing { error } => render!(self, error),
            Self::UrlSyntaxViolation { error } => render!(self, error),
            Self::UrlTooLong { max_length } => to_string_render!(self, max_length),
            Self::UrlScheme { expected_schemes } => render!(self, expected_schemes),
            _ => Ok(self.message_template().to_string()),
        }
    }

    pub fn py_dict(&self, py: Python) -> PyResult<Option<Py<PyDict>>> {
        match self {
            Self::JsonInvalid { error } => py_dict!(py, error),
            Self::GetAttributeError { error } => py_dict!(py, error),
            Self::ModelClassType { class_name } => py_dict!(py, class_name),
            Self::GreaterThan { gt } => py_dict!(py, gt),
            Self::GreaterThanEqual { ge } => py_dict!(py, ge),
            Self::LessThan { lt } => py_dict!(py, lt),
            Self::LessThanEqual { le } => py_dict!(py, le),
            Self::MultipleOf { multiple_of } => py_dict!(py, multiple_of),
            Self::TooShort {
                field_type,
                min_length,
                actual_length,
            } => py_dict!(py, field_type, min_length, actual_length),
            Self::TooLong {
                field_type,
                max_length,
                actual_length,
            } => py_dict!(py, field_type, max_length, actual_length),
            Self::IterationError { error } => py_dict!(py, error),
            Self::StringTooShort { min_length } => py_dict!(py, min_length),
            Self::StringTooLong { max_length } => py_dict!(py, max_length),
            Self::StringPatternMismatch { pattern } => py_dict!(py, pattern),
            Self::MappingType { error } => py_dict!(py, error),
            Self::BytesTooShort { min_length } => py_dict!(py, min_length),
            Self::BytesTooLong { max_length } => py_dict!(py, max_length),
            Self::ValueError { error } => py_dict!(py, error),
            Self::AssertionError { error } => py_dict!(py, error),
            Self::CustomError { value_error } => Ok(value_error.context(py)),
            Self::LiteralError { expected } => py_dict!(py, expected),
            Self::DateParsing { error } => py_dict!(py, error),
            Self::DateFromDatetimeParsing { error } => py_dict!(py, error),
            Self::TimeParsing { error } => py_dict!(py, error),
            Self::DatetimeParsing { error } => py_dict!(py, error),
            Self::DatetimeObjectInvalid { error } => py_dict!(py, error),
            Self::TimeDeltaParsing { error } => py_dict!(py, error),
            Self::IsInstanceOf { class } => py_dict!(py, class),
            Self::IsSubclassOf { class } => py_dict!(py, class),
            Self::UnionTagInvalid {
                discriminator,
                tag,
                expected_tags,
            } => py_dict!(py, discriminator, tag, expected_tags),
            Self::UnionTagNotFound { discriminator } => py_dict!(py, discriminator),
            Self::UrlParsing { error } => py_dict!(py, error),
            Self::UrlSyntaxViolation { error } => py_dict!(py, error),
            Self::UrlTooLong { max_length } => py_dict!(py, max_length),
            Self::UrlScheme { expected_schemes } => py_dict!(py, expected_schemes),
            _ => Ok(None),
        }
    }
}

#[derive(Clone, Debug)]
pub enum Number {
    Int(i64),
    Float(f64),
    String(String),
}

impl Default for Number {
    fn default() -> Self {
        Self::Int(0)
    }
}

impl From<i64> for Number {
    fn from(i: i64) -> Self {
        Self::Int(i)
    }
}

impl From<f64> for Number {
    fn from(f: f64) -> Self {
        Self::Float(f)
    }
}

impl From<String> for Number {
    fn from(s: String) -> Self {
        Self::String(s)
    }
}

impl FromPyObject<'_> for Number {
    fn extract(obj: &PyAny) -> PyResult<Self> {
        if let Ok(int) = obj.extract::<i64>() {
            Ok(Number::Int(int))
        } else if let Ok(float) = obj.extract::<f64>() {
            Ok(Number::Float(float))
        } else if let Ok(string) = obj.extract::<String>() {
            Ok(Number::String(string))
        } else {
            py_err!(PyTypeError; "Expected int or float or String, got {}", obj.get_type())
        }
    }
}

impl fmt::Display for Number {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Float(s) => write!(f, "{s}"),
            Self::Int(i) => write!(f, "{i}"),
            Self::String(s) => write!(f, "{s}"),
        }
    }
}
impl ToPyObject for Number {
    fn to_object(&self, py: Python<'_>) -> PyObject {
        match self {
            Self::Int(i) => i.into_py(py),
            Self::Float(f) => f.into_py(py),
            Self::String(s) => s.into_py(py),
        }
    }
}
