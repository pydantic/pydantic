use std::borrow::Cow;
use std::fmt;

use ahash::AHashMap;
use num_bigint::BigInt;
use pyo3::exceptions::{PyKeyError, PyTypeError, PyValueError};
use pyo3::once_cell::GILOnceCell;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use crate::input::Int;
use crate::tools::{extract_i64, py_err, py_error_type};
use strum::{Display, EnumMessage, IntoEnumIterator};
use strum_macros::EnumIter;

use super::PydanticCustomError;

#[derive(Clone, Debug)]
pub enum ErrorMode {
    Python,
    Json,
}

impl TryFrom<&str> for ErrorMode {
    type Error = PyErr;

    fn try_from(error_mode: &str) -> PyResult<Self> {
        match error_mode {
            "python" => Ok(Self::Python),
            "json" => Ok(Self::Json),
            s => py_err!(PyValueError; "Invalid error mode: {}", s),
        }
    }
}

#[pyfunction]
pub fn list_all_errors(py: Python) -> PyResult<&PyList> {
    let mut errors: Vec<&PyDict> = Vec::with_capacity(100);
    for error_type in ErrorType::iter() {
        if !matches!(error_type, ErrorType::CustomError { .. }) {
            let d = PyDict::new(py);
            d.set_item("type", error_type.to_string())?;
            let message_template_python = error_type.message_template_python();
            d.set_item("message_template_python", message_template_python)?;
            d.set_item(
                "example_message_python",
                error_type.render_message(py, &ErrorMode::Python)?,
            )?;
            let message_template_json = error_type.message_template_json();
            if message_template_python != message_template_json {
                d.set_item("message_template_json", message_template_json)?;
                d.set_item("example_message_json", error_type.render_message(py, &ErrorMode::Json)?)?;
            }
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
    // ---------------------
    // Assignment errors
    NoSuchAttribute {
        attribute: String,
    },
    // ---------------------
    // JSON errors
    JsonInvalid {
        error: String,
    },
    JsonType,
    // ---------------------
    // recursion error
    RecursionLoop,
    // ---------------------
    // typed dict specific errors
    Missing,
    FrozenField,
    FrozenInstance,
    ExtraForbidden,
    InvalidKey,
    GetAttributeError {
        error: String,
    },
    // ---------------------
    // model class specific errors
    ModelType {
        class_name: String,
    },
    ModelAttributesType,
    // ---------------------
    // dataclass errors (we don't talk about ArgsKwargs here for simplicity)
    DataclassType {
        class_name: String,
    },
    DataclassExactType {
        class_name: String,
    },
    // ---------------------
    // None errors
    NoneRequired,
    // ---------------------
    // generic comparison errors - used for all inequality comparisons except int and float which have their
    // own type, bounds arguments are Strings so they can be created from any type
    GreaterThan {
        gt: Number,
    },
    GreaterThanEqual {
        ge: Number,
    },
    LessThan {
        lt: Number,
    },
    LessThanEqual {
        le: Number,
    },
    MultipleOf {
        multiple_of: Number,
    },
    FiniteNumber,
    // ---------------------
    // generic length errors - used for everything with a length except strings and bytes which need custom messages
    TooShort {
        field_type: String,
        min_length: usize,
        actual_length: usize,
    },
    TooLong {
        field_type: String,
        max_length: usize,
        actual_length: usize,
    },
    // ---------------------
    // generic collection and iteration errors
    IterableType,
    IterationError {
        error: String,
    },
    // ---------------------
    // string errors
    StringType,
    StringSubType,
    StringUnicode,
    StringTooShort {
        min_length: usize,
    },
    StringTooLong {
        max_length: usize,
    },
    StringPatternMismatch {
        pattern: String,
    },
    // ---------------------
    // enum errors
    Enum {
        expected: String,
    },
    // ---------------------
    // dict errors
    DictType,
    MappingType {
        error: Cow<'static, str>,
    },
    // ---------------------
    // list errors
    ListType,
    // ---------------------
    // tuple errors
    TupleType,
    // ---------------------
    // set errors
    SetType,
    // ---------------------
    // bool errors
    BoolType,
    BoolParsing,
    // ---------------------
    // int errors
    IntType,
    IntParsing,
    IntParsingSize,
    IntFromFloat,
    // ---------------------
    // float errors
    FloatType,
    FloatParsing,
    // ---------------------
    // bytes errors
    BytesType,
    BytesTooShort {
        min_length: usize,
    },
    BytesTooLong {
        max_length: usize,
    },
    // ---------------------
    // python errors from functions
    ValueError {
        error: Option<PyObject>, // Use Option because EnumIter requires Default to be implemented
    },
    AssertionError {
        error: Option<PyObject>, // Use Option because EnumIter requires Default to be implemented
    },
    // Note: strum message and serialize are not used here
    CustomError {
        custom_error: PydanticCustomError,
    },
    // ---------------------
    // literals
    LiteralError {
        expected: String,
    },
    // ---------------------
    // date errors
    DateType,
    DateParsing {
        error: Cow<'static, str>,
    },
    DateFromDatetimeParsing {
        error: String,
    },
    DateFromDatetimeInexact,
    DatePast,
    DateFuture,
    // ---------------------
    // date errors
    TimeType,
    TimeParsing {
        error: Cow<'static, str>,
    },
    // ---------------------
    // datetime errors
    DatetimeType,
    DatetimeParsing {
        error: Cow<'static, str>,
    },
    DatetimeObjectInvalid {
        error: String,
    },
    DatetimePast,
    DatetimeFuture,
    // ---------------------
    // timezone errors
    TimezoneNaive,
    TimezoneAware,
    TimezoneOffset {
        tz_expected: i32,
        tz_actual: i32,
    },
    // ---------------------
    // timedelta errors
    TimeDeltaType,
    TimeDeltaParsing {
        error: Cow<'static, str>,
    },
    // ---------------------
    // frozenset errors
    FrozenSetType,
    // ---------------------
    // introspection types - e.g. isinstance, callable
    IsInstanceOf {
        class: String,
    },
    IsSubclassOf {
        class: String,
    },
    CallableType,
    // ---------------------
    // union errors
    UnionTagInvalid {
        discriminator: String,
        tag: String,
        expected_tags: String,
    },
    UnionTagNotFound {
        discriminator: String,
    },
    // ---------------------
    // argument errors
    ArgumentsType,
    MissingArgument,
    UnexpectedKeywordArgument,
    MissingKeywordOnlyArgument,
    UnexpectedPositionalArgument,
    MissingPositionalOnlyArgument,
    MultipleArgumentValues,
    // ---------------------
    // URL errors
    UrlType,
    UrlParsing {
        // would be great if this could be a static cow, waiting for https://github.com/servo/rust-url/issues/801
        error: String,
    },
    UrlSyntaxViolation {
        error: Cow<'static, str>,
    },
    UrlTooLong {
        max_length: usize,
    },
    UrlScheme {
        expected_schemes: String,
    },
}

macro_rules! render {
    ($template:ident, $($value:ident),* $(,)?) => {
        Ok(
            $template
            $(
                .replace(concat!("{", stringify!($value), "}"), $value)
            )*
        )
    };
}

macro_rules! to_string_render {
    ($template:ident, $($value:ident),* $(,)?) => {
        Ok(
            $template
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

fn plural_s(value: usize) -> &'static str {
    if value == 1 {
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
            Self::NoSuchAttribute { .. } => extract_context!(NoSuchAttribute, ctx, attribute: String),
            Self::JsonInvalid { .. } => extract_context!(JsonInvalid, ctx, error: String),
            Self::GetAttributeError { .. } => extract_context!(GetAttributeError, ctx, error: String),
            Self::ModelType { .. } => extract_context!(ModelType, ctx, class_name: String),
            Self::DataclassType { .. } => extract_context!(DataclassType, ctx, class_name: String),
            Self::DataclassExactType { .. } => extract_context!(DataclassExactType, ctx, class_name: String),
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
            Self::Enum { .. } => extract_context!(Enum, ctx, expected: String),
            Self::StringPatternMismatch { .. } => extract_context!(StringPatternMismatch, ctx, pattern: String),
            Self::MappingType { .. } => extract_context!(Cow::Owned, MappingType, ctx, error: String),
            Self::BytesTooShort { .. } => extract_context!(BytesTooShort, ctx, min_length: usize),
            Self::BytesTooLong { .. } => extract_context!(BytesTooLong, ctx, max_length: usize),
            Self::ValueError { .. } => extract_context!(ValueError, ctx, error: Option<PyObject>),
            Self::AssertionError { .. } => extract_context!(AssertionError, ctx, error: Option<PyObject>),
            Self::LiteralError { .. } => extract_context!(LiteralError, ctx, expected: String),
            Self::DateParsing { .. } => extract_context!(Cow::Owned, DateParsing, ctx, error: String),
            Self::DateFromDatetimeParsing { .. } => extract_context!(DateFromDatetimeParsing, ctx, error: String),
            Self::TimeParsing { .. } => extract_context!(Cow::Owned, TimeParsing, ctx, error: String),
            Self::DatetimeParsing { .. } => extract_context!(Cow::Owned, DatetimeParsing, ctx, error: String),
            Self::DatetimeObjectInvalid { .. } => extract_context!(DatetimeObjectInvalid, ctx, error: String),
            Self::TimezoneOffset { .. } => {
                extract_context!(TimezoneOffset, ctx, tz_expected: i32, tz_actual: i32)
            }
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

    pub fn new_custom_error(custom_error: PydanticCustomError) -> Self {
        Self::CustomError { custom_error }
    }

    pub fn message_template_python(&self) -> &'static str {
        match self {
            Self::NoSuchAttribute {..} => "Object has no attribute '{attribute}'",
            Self::JsonInvalid {..} => "Invalid JSON: {error}",
            Self::JsonType => "JSON input should be string, bytes or bytearray",
            Self::RecursionLoop => "Recursion error - cyclic reference detected",
            Self::Missing => "Field required",
            Self::FrozenField => "Field is frozen",
            Self::FrozenInstance => "Instance is frozen",
            Self::ExtraForbidden => "Extra inputs are not permitted",
            Self::InvalidKey => "Keys should be strings",
            Self::GetAttributeError {..} => "Error extracting attribute: {error}",
            Self::ModelType {..} => "Input should be a valid dictionary or instance of {class_name}",
            Self::ModelAttributesType => "Input should be a valid dictionary or object to extract fields from",
            Self::DataclassType {..} => "Input should be a dictionary or an instance of {class_name}",
            Self::DataclassExactType {..} => "Input should be an instance of {class_name}",
            Self::NoneRequired => "Input should be None",
            Self::GreaterThan {..} => "Input should be greater than {gt}",
            Self::GreaterThanEqual {..} => "Input should be greater than or equal to {ge}",
            Self::LessThan {..} => "Input should be less than {lt}",
            Self::LessThanEqual {..} => "Input should be less than or equal to {le}",
            Self::MultipleOf {..} => "Input should be a multiple of {multiple_of}",
            Self::FiniteNumber => "Input should be a finite number",
            Self::TooShort {..} => "{field_type} should have at least {min_length} item{expected_plural} after validation, not {actual_length}",
            Self::TooLong {..} => "{field_type} should have at most {max_length} item{expected_plural} after validation, not {actual_length}",
            Self::IterableType => "Input should be iterable",
            Self::IterationError {..} => "Error iterating over object, error: {error}",
            Self::StringType => "Input should be a valid string",
            Self::StringSubType => "Input should be a string, not an instance of a subclass of str",
            Self::StringUnicode => "Input should be a valid string, unable to parse raw data as a unicode string",
            Self::StringTooShort {..} => "String should have at least {min_length} characters",
            Self::StringTooLong {..} => "String should have at most {max_length} characters",
            Self::StringPatternMismatch {..} => "String should match pattern '{pattern}'",
            Self::Enum {..} => "Input should be {expected}",
            Self::DictType => "Input should be a valid dictionary",
            Self::MappingType {..} => "Input should be a valid mapping, error: {error}",
            Self::ListType => "Input should be a valid list",
            Self::TupleType => "Input should be a valid tuple",
            Self::SetType => "Input should be a valid set",
            Self::BoolType => "Input should be a valid boolean",
            Self::BoolParsing => "Input should be a valid boolean, unable to interpret input",
            Self::IntType => "Input should be a valid integer",
            Self::IntParsing => "Input should be a valid integer, unable to parse string as an integer",
            Self::IntFromFloat => "Input should be a valid integer, got a number with a fractional part",
            Self::IntParsingSize => "Unable to parse input string as an integer, exceeded maximum size",
            Self::FloatType => "Input should be a valid number",
            Self::FloatParsing => "Input should be a valid number, unable to parse string as a number",
            Self::BytesType => "Input should be a valid bytes",
            Self::BytesTooShort {..} => "Data should have at least {min_length} bytes",
            Self::BytesTooLong {..} => "Data should have at most {max_length} bytes",
            Self::ValueError {..} => "Value error, {error}",
            Self::AssertionError {..} => "Assertion failed, {error}",
            Self::CustomError {..} => "",  // custom errors are handled separately
            Self::LiteralError {..} => "Input should be {expected}",
            Self::DateType => "Input should be a valid date",
            Self::DateParsing {..} => "Input should be a valid date in the format YYYY-MM-DD, {error}",
            Self::DateFromDatetimeParsing {..} => "Input should be a valid date or datetime, {error}",
            Self::DateFromDatetimeInexact => "Datetimes provided to dates should have zero time - e.g. be exact dates",
            Self::DatePast => "Date should be in the past",
            Self::DateFuture => "Date should be in the future",
            Self::TimeType => "Input should be a valid time",
            Self::TimeParsing {..} => "Input should be in a valid time format, {error}",
            Self::DatetimeType => "Input should be a valid datetime",
            Self::DatetimeParsing {..} => "Input should be a valid datetime, {error}",
            Self::DatetimeObjectInvalid {..} => "Invalid datetime object, got {error}",
            Self::DatetimePast => "Input should be in the past",
            Self::DatetimeFuture => "Input should be in the future",
            Self::TimezoneNaive => "Input should not have timezone info",
            Self::TimezoneAware => "Input should have timezone info",
            Self::TimezoneOffset {..} => "Timezone offset of {tz_expected} required, got {tz_actual}",
            Self::TimeDeltaType => "Input should be a valid timedelta",
            Self::TimeDeltaParsing {..} => "Input should be a valid timedelta, {error}",
            Self::FrozenSetType => "Input should be a valid frozenset",
            Self::IsInstanceOf {..} => "Input should be an instance of {class}",
            Self::IsSubclassOf {..} => "Input should be a subclass of {class}",
            Self::CallableType => "Input should be callable",
            Self::UnionTagInvalid {..} => "Input tag '{tag}' found using {discriminator} does not match any of the expected tags: {expected_tags}",
            Self::UnionTagNotFound {..} => "Unable to extract tag using discriminator {discriminator}",
            Self::ArgumentsType => "Arguments must be a tuple, list or a dictionary",
            Self::MissingArgument => "Missing required argument",
            Self::UnexpectedKeywordArgument => "Unexpected keyword argument",
            Self::MissingKeywordOnlyArgument => "Missing required keyword only argument",
            Self::UnexpectedPositionalArgument => "Unexpected positional argument",
            Self::MissingPositionalOnlyArgument => "Missing required positional only argument",
            Self::MultipleArgumentValues => "Got multiple values for argument",
            Self::UrlType => "URL input should be a string or URL",
            Self::UrlParsing {..} => "Input should be a valid URL, {error}",
            Self::UrlSyntaxViolation {..} => "Input violated strict URL syntax rules, {error}",
            Self::UrlTooLong {..} => "URL should have at most {max_length} characters",
            Self::UrlScheme {..} => "URL scheme should be {expected_schemes}",
        }
    }

    pub fn message_template_json(&self) -> &'static str {
        match self {
            Self::NoneRequired => "Input should be null",
            Self::ListType | Self::TupleType | Self::IterableType | Self::SetType | Self::FrozenSetType => {
                "Input should be a valid array"
            }
            Self::ModelType { .. } | Self::ModelAttributesType | Self::DictType | Self::DataclassType { .. } => {
                "Input should be an object"
            }
            Self::TimeDeltaType => "Input should be a valid duration",
            Self::TimeDeltaParsing { .. } => "Input should be a valid duration, {error}",
            Self::ArgumentsType => "Arguments must be an array or an object",
            _ => self.message_template_python(),
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

    pub fn type_string(&self) -> String {
        match self {
            Self::CustomError {
                custom_error: value_error,
            } => value_error.error_type(),
            _ => self.to_string(),
        }
    }

    pub fn render_message(&self, py: Python, error_mode: &ErrorMode) -> PyResult<String> {
        let tmpl = match error_mode {
            ErrorMode::Python => self.message_template_python(),
            ErrorMode::Json => self.message_template_json(),
        };
        match self {
            Self::NoSuchAttribute { attribute } => render!(tmpl, attribute),
            Self::JsonInvalid { error } => render!(tmpl, error),
            Self::GetAttributeError { error } => render!(tmpl, error),
            Self::ModelType { class_name } => render!(tmpl, class_name),
            Self::DataclassType { class_name } => render!(tmpl, class_name),
            Self::DataclassExactType { class_name } => render!(tmpl, class_name),
            Self::GreaterThan { gt } => to_string_render!(tmpl, gt),
            Self::GreaterThanEqual { ge } => to_string_render!(tmpl, ge),
            Self::LessThan { lt } => to_string_render!(tmpl, lt),
            Self::LessThanEqual { le } => to_string_render!(tmpl, le),
            Self::MultipleOf { multiple_of } => to_string_render!(tmpl, multiple_of),
            Self::TooShort {
                field_type,
                min_length,
                actual_length,
            } => {
                let expected_plural = plural_s(*min_length);
                to_string_render!(tmpl, field_type, min_length, actual_length, expected_plural)
            }
            Self::TooLong {
                field_type,
                max_length,
                actual_length,
            } => {
                let expected_plural = plural_s(*max_length);
                to_string_render!(tmpl, field_type, max_length, actual_length, expected_plural)
            }
            Self::IterationError { error } => render!(tmpl, error),
            Self::StringTooShort { min_length } => to_string_render!(tmpl, min_length),
            Self::StringTooLong { max_length } => to_string_render!(tmpl, max_length),
            Self::StringPatternMismatch { pattern } => render!(tmpl, pattern),
            Self::Enum { expected } => to_string_render!(tmpl, expected),
            Self::MappingType { error } => render!(tmpl, error),
            Self::BytesTooShort { min_length } => to_string_render!(tmpl, min_length),
            Self::BytesTooLong { max_length } => to_string_render!(tmpl, max_length),
            Self::ValueError { error, .. } => {
                let error = &error
                    .as_ref()
                    .map_or(Cow::Borrowed("None"), |v| Cow::Owned(v.as_ref(py).to_string()));
                render!(tmpl, error)
            }
            Self::AssertionError { error, .. } => {
                let error = &error
                    .as_ref()
                    .map_or(Cow::Borrowed("None"), |v| Cow::Owned(v.as_ref(py).to_string()));
                render!(tmpl, error)
            }
            Self::CustomError {
                custom_error: value_error,
            } => value_error.message(py),
            Self::LiteralError { expected } => render!(tmpl, expected),
            Self::DateParsing { error } => render!(tmpl, error),
            Self::DateFromDatetimeParsing { error } => render!(tmpl, error),
            Self::TimeParsing { error } => render!(tmpl, error),
            Self::DatetimeParsing { error } => render!(tmpl, error),
            Self::DatetimeObjectInvalid { error } => render!(tmpl, error),
            Self::TimezoneOffset { tz_expected, tz_actual } => to_string_render!(tmpl, tz_expected, tz_actual),
            Self::TimeDeltaParsing { error } => render!(tmpl, error),
            Self::IsInstanceOf { class } => render!(tmpl, class),
            Self::IsSubclassOf { class } => render!(tmpl, class),
            Self::UnionTagInvalid {
                discriminator,
                tag,
                expected_tags,
            } => render!(tmpl, discriminator, tag, expected_tags),
            Self::UnionTagNotFound { discriminator } => render!(tmpl, discriminator),
            Self::UrlParsing { error } => render!(tmpl, error),
            Self::UrlSyntaxViolation { error } => render!(tmpl, error),
            Self::UrlTooLong { max_length } => to_string_render!(tmpl, max_length),
            Self::UrlScheme { expected_schemes } => render!(tmpl, expected_schemes),
            _ => Ok(tmpl.to_string()),
        }
    }

    pub fn py_dict(&self, py: Python) -> PyResult<Option<Py<PyDict>>> {
        match self {
            Self::NoSuchAttribute { attribute } => py_dict!(py, attribute),
            Self::JsonInvalid { error } => py_dict!(py, error),
            Self::GetAttributeError { error } => py_dict!(py, error),
            Self::ModelType { class_name } => py_dict!(py, class_name),
            Self::DataclassType { class_name } => py_dict!(py, class_name),
            Self::DataclassExactType { class_name } => py_dict!(py, class_name),
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
            Self::Enum { expected } => py_dict!(py, expected),
            Self::MappingType { error } => py_dict!(py, error),
            Self::BytesTooShort { min_length } => py_dict!(py, min_length),
            Self::BytesTooLong { max_length } => py_dict!(py, max_length),
            Self::ValueError { error } => py_dict!(py, error),
            Self::AssertionError { error } => py_dict!(py, error),
            Self::CustomError {
                custom_error: value_error,
            } => Ok(value_error.context(py)),
            Self::LiteralError { expected } => py_dict!(py, expected),
            Self::DateParsing { error } => py_dict!(py, error),
            Self::DateFromDatetimeParsing { error } => py_dict!(py, error),
            Self::TimeParsing { error } => py_dict!(py, error),
            Self::DatetimeParsing { error } => py_dict!(py, error),
            Self::DatetimeObjectInvalid { error } => py_dict!(py, error),
            Self::TimezoneOffset { tz_expected, tz_actual } => py_dict!(py, tz_expected, tz_actual),
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
    BigInt(BigInt),
    Float(f64),
    String(String),
}

impl Default for Number {
    fn default() -> Self {
        Self::Int(0)
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
impl From<Int> for Number {
    fn from(i: Int) -> Self {
        match i {
            Int::I64(i) => Number::Int(i),
            Int::Big(b) => Number::BigInt(b),
        }
    }
}

impl FromPyObject<'_> for Number {
    fn extract(obj: &PyAny) -> PyResult<Self> {
        if let Ok(int) = extract_i64(obj) {
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
            Self::BigInt(i) => write!(f, "{i}"),
            Self::String(s) => write!(f, "{s}"),
        }
    }
}
impl ToPyObject for Number {
    fn to_object(&self, py: Python<'_>) -> PyObject {
        match self {
            Self::Int(i) => i.into_py(py),
            Self::BigInt(i) => i.clone().into_py(py),
            Self::Float(f) => f.into_py(py),
            Self::String(s) => s.into_py(py),
        }
    }
}
