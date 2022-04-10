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
    #[strum(message = "'None' is not permitted")]
    NoneForbidden,
    #[strum(message = "Value must be 'None'")]
    NoneRequired,
    #[strum(message = "Value is not a valid boolean")]
    Bool,
    #[strum(message = "Value is not a valid string")]
    StrType,
    #[strum(message = "Error parsing bytes as utf8 string")]
    StrUnicode,
    #[strum(message = "String must have at least {min_length} characters")]
    StrTooShort,
    #[strum(message = "String must have at most {max_length} characters")]
    StrTooLong,
    #[strum(message = "String does not match pattern '{pattern}'")]
    StrPatternMismatch,
    #[strum(message = "Value is not a valid dictionary")]
    DictType,
    #[strum(message = "Dictionary must have at least {min_length} items")]
    DictTooShort,
    #[strum(message = "Dictionary must have at most {max_length} items")]
    DictTooLong,
    #[strum(message = "Value is not a valid integer")]
    IntType,
    #[strum(message = "Unable to parse value as an integer")]
    IntParsing,
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
}

impl Default for ErrorKind {
    fn default() -> Self {
        ErrorKind::ValueError
    }
}
