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
    Str,
    #[strum(message = "String must have at least {min_length} characters")]
    StrTooShort,
    #[strum(message = "String must have at most {max_length} characters")]
    StrTooLong,
    #[strum(message = "String does not match pattern '{pattern}'")]
    StrPatternMismatch,
    #[strum(message = "Dictionary must have at least {min_length} items")]
    DictTooShort,
    #[strum(message = "Dictionary must have at most {max_length} items")]
    DictTooLong,
}

impl Default for ErrorKind {
    fn default() -> Self {
        ErrorKind::ValueError
    }
}
