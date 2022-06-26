use strum::{Display, EnumMessage};

#[derive(Debug, Display, EnumMessage, Clone)]
#[strum(serialize_all = "snake_case")]
pub enum ErrorKind {
    #[strum(message = "Invalid input")]
    InvalidInput,
    #[strum(message = "Invalid JSON: {parser_error}")]
    InvalidJson,
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
    GetAttributeError,
    // ---------------------
    // model class specific errors
    #[strum(message = "Value must be an instance of {class_name}")]
    ModelClassType,
    // ---------------------
    // None errors
    #[strum(message = "Value must be None/null")]
    NoneRequired,
    // boolean errors
    #[strum(message = "Value must be a valid boolean")]
    Bool,
    // ---------------------
    // generic comparison errors - used for all inequality comparisons
    #[strum(message = "Value must be a multiple of {multiple_of}")]
    IntMultipleOf,
    #[strum(message = "Value must be greater than {gt}")]
    GreaterThan,
    #[strum(message = "Value must be greater than or equal to {ge}")]
    GreaterThanEqual,
    #[strum(message = "Value must be less than {lt}")]
    LessThan,
    #[strum(message = "Value must be less than or equal to {le}")]
    LessThanEqual,
    // ---------------------
    // generic length errors - used for everything with a length except strings and bytes which need custom messages
    #[strum(message = "{type} must have at least {min_length} items")]
    TooShort,
    #[strum(message = "{type} must have at most {max_length} items")]
    TooLong,
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
    StrTooShort,
    #[strum(message = "String must have at most {max_length} characters", serialize = "too_long")]
    StrTooLong,
    #[strum(message = "String must match pattern '{pattern}'")]
    StrPatternMismatch,
    // ---------------------
    // dict errors
    #[strum(message = "Value must be a valid dictionary")]
    DictType,
    #[strum(message = "Unable to convert mapping to a dictionary, error: {error}")]
    DictFromMapping,
    // ---------------------
    // list errors
    #[strum(message = "Value must be a valid list/array")]
    ListType,
    // ---------------------
    // tuple errors
    #[strum(message = "Value must be a valid tuple")]
    TupleType,
    #[strum(message = "Tuple must have exactly {expected_length} item{plural}")]
    TupleLengthMismatch,
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
    IntNan,
    #[strum(message = "Value must be a multiple of {multiple_of}")]
    IntMultiple,
    // ---------------------
    // float errors
    #[strum(message = "Value must be a valid number")]
    FloatType,
    #[strum(message = "Value must be a valid number, unable to parse string as an number")]
    FloatParsing,
    #[strum(message = "Value must be a multiple of {multiple_of}")]
    FloatMultiple,
    // ---------------------
    // bytes errors
    #[strum(message = "Value must be a valid bytes")]
    BytesType,
    #[strum(message = "Data must have at least {min_length} bytes", serialize = "too_short")]
    BytesTooShort,
    #[strum(message = "Data must have at most {max_length} bytes", serialize = "too_long")]
    BytesTooLong,
    // ---------------------
    // python errors from functions (the messages here will not be used as we sett message in these cases)
    #[strum(message = "Invalid value: {error}")]
    ValueError,
    #[strum(message = "Assertion failed: {error}")]
    AssertionError,
    // ---------------------
    // literals
    #[strum(serialize = "literal_error", message = "Value must be {expected}")]
    LiteralSingleError,
    #[strum(serialize = "literal_error", message = "Value must be one of: {expected}")]
    LiteralMultipleError,
    // ---------------------
    // date errors
    #[strum(message = "Value must be a valid date")]
    DateType,
    #[strum(message = "Value must be a valid date in the format YYYY-MM-DD, {parsing_error}")]
    DateParsing,
    #[strum(message = "Value must be a valid date or datetime, {parsing_error}")]
    DateFromDatetimeParsing,
    #[strum(message = "Datetimes provided to dates must have zero time - e.g. be exact dates")]
    DateFromDatetimeInexact,
    // ---------------------
    // date errors
    #[strum(message = "Value must be a valid time")]
    TimeType,
    #[strum(message = "Value must be in a valid time format, {parsing_error}")]
    TimeParsing,
    // ---------------------
    // datetime errors
    #[strum(serialize = "datetime_type", message = "Value must be a valid datetime")]
    DateTimeType,
    // TODO #[strum(message = "Value must be in a valid datetime format, {parsing_error}")]
    #[strum(
        serialize = "datetime_parsing",
        message = "Value must be a valid datetime, {parsing_error}"
    )]
    DateTimeParsing,
    #[strum(
        serialize = "datetime_object_invalid",
        message = "Invalid datetime object, got {processing_error}"
    )]
    DateTimeObjectInvalid,
    // ---------------------
    // frozenset errors
    #[strum(message = "Value must be a valid frozenset")]
    FrozenSetType,
    #[strum(message = "FrozenSet must have at least {min_length} items")]
    FrozenSetTooShort,
    #[strum(message = "FrozenSet must have at most {max_length} items")]
    FrozenSetTooLong,
}

impl Default for ErrorKind {
    fn default() -> Self {
        ErrorKind::InvalidInput
    }
}
