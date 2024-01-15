use std::any::type_name;
use std::borrow::Cow;
use std::fmt;

use pyo3::exceptions::{PyKeyError, PyTypeError};
use pyo3::once_cell::GILOnceCell;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use ahash::AHashMap;
use num_bigint::BigInt;
use strum::{Display, EnumMessage, IntoEnumIterator};
use strum_macros::EnumIter;

use crate::input::{InputType, Int};
use crate::tools::{extract_i64, py_err, py_error_type};

use super::PydanticCustomError;

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
                error_type.render_message(py, InputType::Python)?,
            )?;
            let message_template_json = error_type.message_template_json();
            if message_template_python != message_template_json {
                d.set_item("message_template_json", message_template_json)?;
                d.set_item("example_message_json", error_type.render_message(py, InputType::Json)?)?;
            }
            d.set_item("example_context", error_type.py_dict(py)?)?;
            errors.push(d);
        }
    }
    Ok(PyList::new(py, errors))
}

fn field_from_context<'py, T: FromPyObject<'py>>(
    context: Option<&'py PyDict>,
    field_name: &str,
    enum_name: &str,
    type_name_fn: fn() -> &'static str,
) -> PyResult<T> {
    context
        .ok_or_else(|| py_error_type!(PyTypeError; "{}: '{}' required in context", enum_name, field_name))?
        .get_item(field_name)?
        .ok_or_else(|| py_error_type!(PyTypeError; "{}: '{}' required in context", enum_name, field_name))?
        .extract::<T>()
        .map_err(|_| py_error_type!(PyTypeError; "{}: '{}' context value must be a {}", enum_name, field_name, type_name_fn()))
}

fn cow_field_from_context<'py, T: FromPyObject<'py>, B: ?Sized + 'static>(
    context: Option<&'py PyDict>,
    field_name: &str,
    enum_name: &str,
    _type_name_fn: fn() -> &'static str,
) -> PyResult<Cow<'static, B>>
where
    B: ToOwned<Owned = T>,
{
    let res: T = field_from_context(context, field_name, enum_name, || {
        type_name::<T>().split("::").last().unwrap()
    })?;
    Ok(Cow::Owned(res))
}

macro_rules! basic_error_default {
    (
        $item:ident $(,)?
    ) => {
        pub const $item: ErrorType = ErrorType::$item { context: None };
    };
    (
        $item:ident, $($key:ident),* $(,)?
    ) => {}; // With more parameters enum item must be explicitly created
}

macro_rules! error_types {
    (
        $(
            $item:ident {
                $($key:ident: {ctx_type: $ctx_type:ty, ctx_fn: $ctx_fn:path}),* $(,)?
            },
        )+
    ) => {
        #[derive(Clone, Debug, Display, EnumMessage, EnumIter)]
        #[strum(serialize_all = "snake_case")]
        pub enum ErrorType {
            $(
                $item {
                    context: Option<Py<PyDict>>,
                    $($key: $ctx_type,)*
                }
            ),+,
        }
        impl ErrorType {
            pub fn new(py: Python, value: &str, context: Option<&PyDict>) -> PyResult<Self> {
                let lookup = ERROR_TYPE_LOOKUP.get_or_init(py, Self::build_lookup);
                let error_type = match lookup.get(value) {
                    Some(error_type) => error_type.clone(),
                    None => return py_err!(PyKeyError; "Invalid error type: '{}'", value),
                };
                match error_type {
                    $(
                        Self::$item { .. } => {
                            Ok(Self::$item {
                                context: context.map(|c| c.into_py(py)),
                                $(
                                    $key: $ctx_fn(context, stringify!($key), stringify!($item), || stringify!($ctx_type))?,
                                )*
                            })
                        },
                    )+
                }
            }

            fn py_dict_update_ctx(&self, py: Python, dict: &PyDict) -> PyResult<bool> {
                match self {
                    $(
                        Self::$item { context, $($key,)* } => {
                            $(
                                dict.set_item::<&str, Py<PyAny>>(stringify!($key), $key.to_object(py))?;
                            )*
                            if let Some(ctx) = context {
                                dict.update(ctx.as_ref(py).downcast()?)?;
                                Ok(true)
                            } else {
                                Ok(false)
                            }
                        },
                    )+
                }
            }
        }

        pub struct ErrorTypeDefaults {}
        // Allow unused default constants as they are generated by macro.
        // Also allow camel case as constants so we dont need to do case conversion of macro
        // generated names. Enums are also then easier to find when searching.
        #[allow(dead_code, non_upper_case_globals)]
        impl ErrorTypeDefaults {
            $(
                basic_error_default!($item, $($key),*);
            )+
        }
    };
}

// Definite each validation error.
// NOTE: if an error has parameters:
// * the variables in the message need to match the enum struct
// * you need to add an entry to the `render` enum to render the error message as a template
error_types! {
    // ---------------------
    // Assignment errors
    NoSuchAttribute {
        attribute: {ctx_type: String, ctx_fn: field_from_context},
    },
    // ---------------------
    // JSON errors
    JsonInvalid {
        error: {ctx_type: String, ctx_fn: field_from_context},
    },
    JsonType {},
    // ---------------------
    // recursion error
    RecursionLoop {},
    // ---------------------
    // typed dict specific errors
    Missing {},
    FrozenField {},
    FrozenInstance {},
    ExtraForbidden {},
    InvalidKey {},
    GetAttributeError {
        error: {ctx_type: String, ctx_fn: field_from_context},
    },
    // ---------------------
    // model class specific errors
    ModelType {
        class_name: {ctx_type: String, ctx_fn: field_from_context},
    },
    ModelAttributesType {},
    // ---------------------
    // dataclass errors (we don't talk about ArgsKwargs here for simplicity)
    DataclassType {
        class_name: {ctx_type: String, ctx_fn: field_from_context},
    },
    DataclassExactType {
        class_name: {ctx_type: String, ctx_fn: field_from_context},
    },
    // ---------------------
    // None errors
    NoneRequired {},
    // ---------------------
    // generic comparison errors
    GreaterThan {
        gt: {ctx_type: Number, ctx_fn: field_from_context},
    },
    GreaterThanEqual {
        ge: {ctx_type: Number, ctx_fn: field_from_context},
    },
    LessThan {
        lt: {ctx_type: Number, ctx_fn: field_from_context},
    },
    LessThanEqual {
        le: {ctx_type: Number, ctx_fn: field_from_context},
    },
    MultipleOf {
        multiple_of: {ctx_type: Number, ctx_fn: field_from_context},
    },
    FiniteNumber {},
    // ---------------------
    // generic length errors - used for everything with a length except strings and bytes which need custom messages
    TooShort {
        field_type: {ctx_type: String, ctx_fn: field_from_context},
        min_length: {ctx_type: usize, ctx_fn: field_from_context},
        actual_length: {ctx_type: usize, ctx_fn: field_from_context},
    },
    TooLong {
        field_type: {ctx_type: String, ctx_fn: field_from_context},
        max_length: {ctx_type: usize, ctx_fn: field_from_context},
        actual_length: {ctx_type: Option<usize>, ctx_fn: field_from_context},
    },
    // ---------------------
    // generic collection and iteration errors
    IterableType {},
    IterationError {
        error: {ctx_type: String, ctx_fn: field_from_context},
    },
    // ---------------------
    // string errors
    StringType {},
    StringSubType {},
    StringUnicode {},
    StringTooShort {
        min_length: {ctx_type: usize, ctx_fn: field_from_context},
    },
    StringTooLong {
        max_length: {ctx_type: usize, ctx_fn: field_from_context},
    },
    StringPatternMismatch {
        pattern: {ctx_type: String, ctx_fn: field_from_context},
    },
    // ---------------------
    // enum errors
    Enum {
        expected: {ctx_type: String, ctx_fn: field_from_context},
    },
    // ---------------------
    // dict errors
    DictType {},
    MappingType {
        error: {ctx_type: Cow<'static, str>, ctx_fn: cow_field_from_context<String, _>},
    },
    // ---------------------
    // list errors
    ListType {},
    // ---------------------
    // tuple errors
    TupleType {},
    // ---------------------
    // set errors
    SetType {},
    // ---------------------
    // bool errors
    BoolType {},
    BoolParsing {},
    // ---------------------
    // int errors
    IntType {},
    IntParsing {},
    IntParsingSize {},
    IntFromFloat {},
    // ---------------------
    // float errors
    FloatType {},
    FloatParsing {},
    // ---------------------
    // bytes errors
    BytesType {},
    BytesTooShort {
        min_length: {ctx_type: usize, ctx_fn: field_from_context},
    },
    BytesTooLong {
        max_length: {ctx_type: usize, ctx_fn: field_from_context},
    },
    // ---------------------
    // python errors from functions
    ValueError {
        error: {ctx_type: Option<PyObject>, ctx_fn: field_from_context}, // Use Option because EnumIter requires Default to be implemented
    },
    AssertionError {
        error: {ctx_type: Option<PyObject>, ctx_fn: field_from_context}, // Use Option because EnumIter requires Default to be implemented
    },
    // Note: strum message and serialize are not used here
    CustomError {
        // context is a common field in all enums
        error_type: {ctx_type: String, ctx_fn: field_from_context},
        message_template: {ctx_type: String, ctx_fn: field_from_context},
    },
    // ---------------------
    // literals
    LiteralError {
        expected: {ctx_type: String, ctx_fn: field_from_context},
    },
    // ---------------------
    // date errors
    DateType {},
    DateParsing {
        error: {ctx_type: Cow<'static, str>, ctx_fn: cow_field_from_context<String, _>},
    },
    DateFromDatetimeParsing {
        error: {ctx_type: Cow<'static, str>, ctx_fn: cow_field_from_context<String, _>},
    },
    DateFromDatetimeInexact {},
    DatePast {},
    DateFuture {},
    // ---------------------
    // date errors
    TimeType {},
    TimeParsing {
        error: {ctx_type: Cow<'static, str>, ctx_fn: cow_field_from_context<String, _>},
    },
    // ---------------------
    // datetime errors
    DatetimeType {},
    DatetimeParsing {
        error: {ctx_type: Cow<'static, str>, ctx_fn: cow_field_from_context<String, _>},
    },
    DatetimeObjectInvalid {
        error: {ctx_type: String, ctx_fn: field_from_context},
    },
    DatetimeFromDateParsing {
        error: {ctx_type: Cow<'static, str>, ctx_fn: cow_field_from_context<String, _>},
    },
    DatetimePast {},
    DatetimeFuture {},
    // ---------------------
    // timezone errors
    TimezoneNaive {},
    TimezoneAware {},
    TimezoneOffset {
        tz_expected: {ctx_type: i32, ctx_fn: field_from_context},
        tz_actual: {ctx_type: i32, ctx_fn: field_from_context},
    },
    // ---------------------
    // timedelta errors
    TimeDeltaType {},
    TimeDeltaParsing {
        error: {ctx_type: Cow<'static, str>, ctx_fn: cow_field_from_context<String, _>},
    },
    // ---------------------
    // frozenset errors
    FrozenSetType {},
    // ---------------------
    // introspection types - e.g. isinstance, callable
    IsInstanceOf {
        class: {ctx_type: String, ctx_fn: field_from_context},
    },
    IsSubclassOf {
        class: {ctx_type: String, ctx_fn: field_from_context},
    },
    CallableType {},
    // ---------------------
    // union errors
    UnionTagInvalid {
        discriminator: {ctx_type: String, ctx_fn: field_from_context},
        tag: {ctx_type: String, ctx_fn: field_from_context},
        expected_tags: {ctx_type: String, ctx_fn: field_from_context},
    },
    UnionTagNotFound {
        discriminator: {ctx_type: String, ctx_fn: field_from_context},
    },
    // ---------------------
    // argument errors
    ArgumentsType {},
    MissingArgument {},
    UnexpectedKeywordArgument {},
    MissingKeywordOnlyArgument {},
    UnexpectedPositionalArgument {},
    MissingPositionalOnlyArgument {},
    MultipleArgumentValues {},
    // ---------------------
    // URL errors
    UrlType {},
    UrlParsing {
        // would be great if this could be a static cow, waiting for https://github.com/servo/rust-url/issues/801
        error: {ctx_type: String, ctx_fn: field_from_context},
    },
    UrlSyntaxViolation {
        error: {ctx_type: Cow<'static, str>, ctx_fn: cow_field_from_context<String, _>},
    },
    UrlTooLong {
        max_length: {ctx_type: usize, ctx_fn: field_from_context},
    },
    UrlScheme {
        expected_schemes: {ctx_type: String, ctx_fn: field_from_context},
    },
    // UUID errors,
    UuidType {},
    UuidParsing {
        error: {ctx_type: String, ctx_fn: field_from_context},
    },
    UuidVersion {
        expected_version: {ctx_type: usize, ctx_fn: field_from_context},
    },
    // Decimal errors
    DecimalType {},
    DecimalParsing {},
    DecimalMaxDigits {
        max_digits: {ctx_type: u64, ctx_fn: field_from_context},
    },
    DecimalMaxPlaces {
        decimal_places: {ctx_type: u64, ctx_fn: field_from_context},
    },
    DecimalWholeDigits {
        whole_digits: {ctx_type: u64, ctx_fn: field_from_context},
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

fn plural_s<T: From<u8> + PartialEq>(value: T) -> &'static str {
    if value == 1.into() {
        ""
    } else {
        "s"
    }
}

static ERROR_TYPE_LOOKUP: GILOnceCell<AHashMap<String, ErrorType>> = GILOnceCell::new();

impl ErrorType {
    pub fn new_custom_error(py: Python, custom_error: PydanticCustomError) -> Self {
        Self::CustomError {
            error_type: custom_error.error_type(),
            message_template: custom_error.message_template(),
            context: custom_error.context(py),
        }
    }

    pub fn message_template_python(&self) -> &'static str {
        match self {
            Self::NoSuchAttribute {..} => "Object has no attribute '{attribute}'",
            Self::JsonInvalid {..} => "Invalid JSON: {error}",
            Self::JsonType {..} => "JSON input should be string, bytes or bytearray",
            Self::RecursionLoop {..} => "Recursion error - cyclic reference detected",
            Self::Missing {..} => "Field required",
            Self::FrozenField {..} => "Field is frozen",
            Self::FrozenInstance {..} => "Instance is frozen",
            Self::ExtraForbidden {..} => "Extra inputs are not permitted",
            Self::InvalidKey {..} => "Keys should be strings",
            Self::GetAttributeError {..} => "Error extracting attribute: {error}",
            Self::ModelType {..} => "Input should be a valid dictionary or instance of {class_name}",
            Self::ModelAttributesType {..} => "Input should be a valid dictionary or object to extract fields from",
            Self::DataclassType {..} => "Input should be a dictionary or an instance of {class_name}",
            Self::DataclassExactType {..} => "Input should be an instance of {class_name}",
            Self::NoneRequired {..} => "Input should be None",
            Self::GreaterThan {..} => "Input should be greater than {gt}",
            Self::GreaterThanEqual {..} => "Input should be greater than or equal to {ge}",
            Self::LessThan {..} => "Input should be less than {lt}",
            Self::LessThanEqual {..} => "Input should be less than or equal to {le}",
            Self::MultipleOf {..} => "Input should be a multiple of {multiple_of}",
            Self::FiniteNumber {..} => "Input should be a finite number",
            Self::TooShort {..} => "{field_type} should have at least {min_length} item{expected_plural} after validation, not {actual_length}",
            Self::TooLong {..} => "{field_type} should have at most {max_length} item{expected_plural} after validation, not {actual_length}",
            Self::IterableType {..} => "Input should be iterable",
            Self::IterationError {..} => "Error iterating over object, error: {error}",
            Self::StringType {..} => "Input should be a valid string",
            Self::StringSubType {..} => "Input should be a string, not an instance of a subclass of str",
            Self::StringUnicode {..} => "Input should be a valid string, unable to parse raw data as a unicode string",
            Self::StringTooShort {..} => "String should have at least {min_length} character{expected_plural}",
            Self::StringTooLong {..} => "String should have at most {max_length} character{expected_plural}",
            Self::StringPatternMismatch {..} => "String should match pattern '{pattern}'",
            Self::Enum {..} => "Input should be {expected}",
            Self::DictType {..} => "Input should be a valid dictionary",
            Self::MappingType {..} => "Input should be a valid mapping, error: {error}",
            Self::ListType {..} => "Input should be a valid list",
            Self::TupleType {..} => "Input should be a valid tuple",
            Self::SetType {..} => "Input should be a valid set",
            Self::BoolType {..} => "Input should be a valid boolean",
            Self::BoolParsing {..} => "Input should be a valid boolean, unable to interpret input",
            Self::IntType {..} => "Input should be a valid integer",
            Self::IntParsing {..} => "Input should be a valid integer, unable to parse string as an integer",
            Self::IntFromFloat {..} => "Input should be a valid integer, got a number with a fractional part",
            Self::IntParsingSize {..} => "Unable to parse input string as an integer, exceeded maximum size",
            Self::FloatType {..} => "Input should be a valid number",
            Self::FloatParsing {..} => "Input should be a valid number, unable to parse string as a number",
            Self::BytesType {..} => "Input should be a valid bytes",
            Self::BytesTooShort {..} => "Data should have at least {min_length} byte{expected_plural}",
            Self::BytesTooLong {..} => "Data should have at most {max_length} byte{expected_plural}",
            Self::ValueError {..} => "Value error, {error}",
            Self::AssertionError {..} => "Assertion failed, {error}",
            Self::CustomError {..} => "",  // custom errors are handled separately
            Self::LiteralError {..} => "Input should be {expected}",
            Self::DateType {..} => "Input should be a valid date",
            Self::DateParsing {..} => "Input should be a valid date in the format YYYY-MM-DD, {error}",
            Self::DateFromDatetimeParsing {..} => "Input should be a valid date or datetime, {error}",
            Self::DateFromDatetimeInexact {..} => "Datetimes provided to dates should have zero time - e.g. be exact dates",
            Self::DatePast {..} => "Date should be in the past",
            Self::DateFuture {..} => "Date should be in the future",
            Self::TimeType {..} => "Input should be a valid time",
            Self::TimeParsing {..} => "Input should be in a valid time format, {error}",
            Self::DatetimeType {..} => "Input should be a valid datetime",
            Self::DatetimeParsing {..} => "Input should be a valid datetime, {error}",
            Self::DatetimeObjectInvalid {..} => "Invalid datetime object, got {error}",
            Self::DatetimeFromDateParsing {..} => "Input should be a valid datetime or date, {error}",
            Self::DatetimePast {..} => "Input should be in the past",
            Self::DatetimeFuture {..} => "Input should be in the future",
            Self::TimezoneNaive {..} => "Input should not have timezone info",
            Self::TimezoneAware {..} => "Input should have timezone info",
            Self::TimezoneOffset {..} => "Timezone offset of {tz_expected} required, got {tz_actual}",
            Self::TimeDeltaType {..} => "Input should be a valid timedelta",
            Self::TimeDeltaParsing {..} => "Input should be a valid timedelta, {error}",
            Self::FrozenSetType {..} => "Input should be a valid frozenset",
            Self::IsInstanceOf {..} => "Input should be an instance of {class}",
            Self::IsSubclassOf {..} => "Input should be a subclass of {class}",
            Self::CallableType {..} => "Input should be callable",
            Self::UnionTagInvalid {..} => "Input tag '{tag}' found using {discriminator} does not match any of the expected tags: {expected_tags}",
            Self::UnionTagNotFound {..} => "Unable to extract tag using discriminator {discriminator}",
            Self::ArgumentsType {..} => "Arguments must be a tuple, list or a dictionary",
            Self::MissingArgument {..} => "Missing required argument",
            Self::UnexpectedKeywordArgument {..} => "Unexpected keyword argument",
            Self::MissingKeywordOnlyArgument {..} => "Missing required keyword only argument",
            Self::UnexpectedPositionalArgument {..} => "Unexpected positional argument",
            Self::MissingPositionalOnlyArgument {..} => "Missing required positional only argument",
            Self::MultipleArgumentValues {..} => "Got multiple values for argument",
            Self::UrlType {..} => "URL input should be a string or URL",
            Self::UrlParsing {..} => "Input should be a valid URL, {error}",
            Self::UrlSyntaxViolation {..} => "Input violated strict URL syntax rules, {error}",
            Self::UrlTooLong {..} => "URL should have at most {max_length} character{expected_plural}",
            Self::UrlScheme {..} => "URL scheme should be {expected_schemes}",
            Self::UuidType {..} => "UUID input should be a string, bytes or UUID object",
            Self::UuidParsing {..} => "Input should be a valid UUID, {error}",
            Self::UuidVersion {..} => "UUID version {expected_version} expected",
            Self::DecimalType {..} => "Decimal input should be an integer, float, string or Decimal object",
            Self::DecimalParsing {..} => "Input should be a valid decimal",
            Self::DecimalMaxDigits {..} => "Decimal input should have no more than {max_digits} digit{expected_plural} in total",
            Self::DecimalMaxPlaces {..} => "Decimal input should have no more than {decimal_places} decimal place{expected_plural}",
            Self::DecimalWholeDigits {..} => "Decimal input should have no more than {whole_digits} digit{expected_plural} before the decimal point",
        }
    }

    pub fn message_template_json(&self) -> &'static str {
        match self {
            Self::NoneRequired { .. } => "Input should be null",
            Self::ListType { .. }
            | Self::TupleType { .. }
            | Self::IterableType { .. }
            | Self::SetType { .. }
            | Self::FrozenSetType { .. } => "Input should be a valid array",
            Self::ModelType { .. }
            | Self::ModelAttributesType { .. }
            | Self::DictType { .. }
            | Self::DataclassType { .. } => "Input should be an object",
            Self::TimeDeltaType { .. } => "Input should be a valid duration",
            Self::TimeDeltaParsing { .. } => "Input should be a valid duration, {error}",
            Self::ArgumentsType { .. } => "Arguments must be an array or an object",
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
            Self::CustomError { error_type, .. } => error_type.clone(),
            _ => self.to_string(),
        }
    }

    pub fn render_message(&self, py: Python, input_type: InputType) -> PyResult<String> {
        let tmpl = match input_type {
            InputType::Python => self.message_template_python(),
            _ => self.message_template_json(),
        };
        match self {
            Self::NoSuchAttribute { attribute, .. } => render!(tmpl, attribute),
            Self::JsonInvalid { error, .. } => render!(tmpl, error),
            Self::GetAttributeError { error, .. } => render!(tmpl, error),
            Self::ModelType { class_name, .. } => render!(tmpl, class_name),
            Self::DataclassType { class_name, .. } => render!(tmpl, class_name),
            Self::DataclassExactType { class_name, .. } => render!(tmpl, class_name),
            Self::GreaterThan { gt, .. } => to_string_render!(tmpl, gt),
            Self::GreaterThanEqual { ge, .. } => to_string_render!(tmpl, ge),
            Self::LessThan { lt, .. } => to_string_render!(tmpl, lt),
            Self::LessThanEqual { le, .. } => to_string_render!(tmpl, le),
            Self::MultipleOf { multiple_of, .. } => to_string_render!(tmpl, multiple_of),
            Self::TooShort {
                field_type,
                min_length,
                actual_length,
                ..
            } => {
                let expected_plural = plural_s(*min_length);
                to_string_render!(tmpl, field_type, min_length, actual_length, expected_plural,)
            }
            Self::TooLong {
                field_type,
                max_length,
                actual_length,
                ..
            } => {
                let expected_plural = plural_s(*max_length);
                let actual_length = actual_length.map_or(Cow::Borrowed("more"), |v| Cow::Owned(v.to_string()));
                to_string_render!(tmpl, field_type, max_length, actual_length, expected_plural,)
            }
            Self::IterationError { error, .. } => render!(tmpl, error),
            Self::StringTooShort { min_length, .. } => {
                let expected_plural = plural_s(*min_length);
                to_string_render!(tmpl, min_length, expected_plural)
            }
            Self::StringTooLong { max_length, .. } => {
                let expected_plural = plural_s(*max_length);
                to_string_render!(tmpl, max_length, expected_plural)
            }
            Self::StringPatternMismatch { pattern, .. } => render!(tmpl, pattern),
            Self::Enum { expected, .. } => to_string_render!(tmpl, expected),
            Self::MappingType { error, .. } => render!(tmpl, error),
            Self::BytesTooShort { min_length, .. } => {
                let expected_plural = plural_s(*min_length);
                to_string_render!(tmpl, min_length, expected_plural)
            }
            Self::BytesTooLong { max_length, .. } => {
                let expected_plural = plural_s(*max_length);
                to_string_render!(tmpl, max_length, expected_plural)
            }
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
                message_template,
                context,
                ..
            } => PydanticCustomError::format_message(message_template, context.as_ref().map(|c| c.as_ref(py))),
            Self::LiteralError { expected, .. } => render!(tmpl, expected),
            Self::DateParsing { error, .. } => render!(tmpl, error),
            Self::DateFromDatetimeParsing { error, .. } => render!(tmpl, error),
            Self::TimeParsing { error, .. } => render!(tmpl, error),
            Self::DatetimeParsing { error, .. } => render!(tmpl, error),
            Self::DatetimeFromDateParsing { error, .. } => render!(tmpl, error),
            Self::DatetimeObjectInvalid { error, .. } => render!(tmpl, error),
            Self::TimezoneOffset {
                tz_expected, tz_actual, ..
            } => to_string_render!(tmpl, tz_expected, tz_actual),
            Self::TimeDeltaParsing { error, .. } => render!(tmpl, error),
            Self::IsInstanceOf { class, .. } => render!(tmpl, class),
            Self::IsSubclassOf { class, .. } => render!(tmpl, class),
            Self::UnionTagInvalid {
                discriminator,
                tag,
                expected_tags,
                ..
            } => render!(tmpl, discriminator, tag, expected_tags),
            Self::UnionTagNotFound { discriminator, .. } => render!(tmpl, discriminator),
            Self::UrlParsing { error, .. } => render!(tmpl, error),
            Self::UrlSyntaxViolation { error, .. } => render!(tmpl, error),
            Self::UrlTooLong { max_length, .. } => {
                let expected_plural = plural_s(*max_length);
                to_string_render!(tmpl, max_length, expected_plural)
            }
            Self::UrlScheme { expected_schemes, .. } => render!(tmpl, expected_schemes),
            Self::UuidParsing { error, .. } => render!(tmpl, error),
            Self::UuidVersion { expected_version, .. } => to_string_render!(tmpl, expected_version),
            Self::DecimalMaxDigits { max_digits, .. } => {
                let expected_plural = plural_s(*max_digits);
                to_string_render!(tmpl, max_digits, expected_plural)
            }
            Self::DecimalMaxPlaces { decimal_places, .. } => {
                let expected_plural = plural_s(*decimal_places);
                to_string_render!(tmpl, decimal_places, expected_plural)
            }
            Self::DecimalWholeDigits { whole_digits, .. } => {
                let expected_plural = plural_s(*whole_digits);
                to_string_render!(tmpl, whole_digits, expected_plural)
            }
            _ => Ok(tmpl.to_string()),
        }
    }

    pub fn py_dict(&self, py: Python) -> PyResult<Option<Py<PyDict>>> {
        let dict = PyDict::new(py);
        let custom_ctx_used = self.py_dict_update_ctx(py, dict)?;

        if let Self::CustomError { .. } = self {
            if custom_ctx_used {
                // Custom error type and message are handled separately by the caller.
                // They are added to the root of the ErrorDetails.
                dict.del_item("error_type")?;
                dict.del_item("message_template")?;
                Ok(Some(dict.into()))
            } else {
                Ok(None)
            }
        } else if custom_ctx_used || !dict.is_empty() {
            Ok(Some(dict.into()))
        } else {
            Ok(None)
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
        if let Some(int) = extract_i64(obj) {
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
