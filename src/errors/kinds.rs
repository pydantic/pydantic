use strum::{Display, EnumMessage};

#[derive(Debug, Display, EnumMessage, Clone)]
#[strum(serialize_all = "snake_case")]
pub enum ErrorKind {
    #[strum(message = "Invalid value")]
    ValueError,
    #[strum(message = "Field required")]
    Missing,
    #[strum(message = "Extra fields are not permitted")]
    ExtraForbidden,
    #[strum(message = "Value must not be None/null")]
    NoneForbidden,
    #[strum(message = "Value must be None/null")]
    NoneRequired,
    #[strum(message = "Value must be a valid boolean")]
    Bool,
    #[strum(message = "Value must be a valid string")]
    // string errors
    StrType,
    #[strum(message = "Value must be a valid string, unable to parse raw data as a unicode string")]
    StrUnicode,
    #[strum(message = "String must have at least {min_length} characters")]
    StrTooShort,
    #[strum(message = "String must have at most {max_length} characters")]
    StrTooLong,
    #[strum(message = "String must match pattern '{pattern}'")]
    StrPatternMismatch,
    // dict errors
    #[strum(message = "Value must be a valid dictionary")]
    DictType,
    #[strum(message = "Dictionary must have at least {min_length} items")]
    DictTooShort,
    #[strum(message = "Dictionary must have at most {max_length} items")]
    DictTooLong,
    // list errors
    #[strum(message = "Value must be a valid list/array")]
    ListType,
    #[strum(message = "List must have at least {min_length} items")]
    ListTooShort,
    #[strum(message = "List must have at most {max_length} items")]
    ListTooLong,
    // int errors
    #[strum(message = "Value must be a valid integer")]
    IntType,
    #[strum(message = "Value must be a valid integer, unable to parse string as an integer")]
    IntParsing,
    #[strum(message = "Value must be a valid integer, got a number with a fractional part")]
    IntFromFloat,
    #[strum(message = "Value must be a multiple of {multiple_of}")]
    IntMultiple,
    #[strum(message = "Value must be greater than {gt}")]
    IntGreaterThan,
    #[strum(message = "Value must be greater than or equal to {ge}")]
    IntGreaterThanEqual,
    #[strum(message = "Value must be less than {lt}")]
    IntLessThan,
    #[strum(message = "Value must be less than or equal to {le}")]
    IntLessThanEqual,
    // float errors
    #[strum(message = "Value must be a valid number")]
    FloatType,
    #[strum(message = "Value must be a valid number, unable to parse string as an number")]
    FloatParsing,
    #[strum(message = "Value must be a multiple of {multiple_of}")]
    FloatMultiple,
    #[strum(message = "Value must be greater than {gt}")]
    FloatGreaterThan,
    #[strum(message = "Value must be greater than or equal to {ge}")]
    FloatGreaterThanEqual,
    #[strum(message = "Value must be less than {lt}")]
    FloatLessThan,
    #[strum(message = "Value must be less than or equal to {le}")]
    FloatLessThanEqual,
}

impl Default for ErrorKind {
    fn default() -> Self {
        ErrorKind::ValueError
    }
}
