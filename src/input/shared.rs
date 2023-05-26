use num_bigint::BigInt;

use crate::errors::{ErrorType, ValError, ValResult};
use crate::input::EitherInt;

use super::Input;

pub fn map_json_err<'a>(input: &'a impl Input<'a>, error: serde_json::Error) -> ValError<'a> {
    ValError::new(
        ErrorType::JsonInvalid {
            error: error.to_string(),
        },
        input,
    )
}

pub fn str_as_bool<'a>(input: &'a impl Input<'a>, str: &str) -> ValResult<'a, bool> {
    if str == "0"
        || str.eq_ignore_ascii_case("f")
        || str.eq_ignore_ascii_case("n")
        || str.eq_ignore_ascii_case("no")
        || str.eq_ignore_ascii_case("off")
        || str.eq_ignore_ascii_case("false")
    {
        Ok(false)
    } else if str == "1"
        || str.eq_ignore_ascii_case("t")
        || str.eq_ignore_ascii_case("y")
        || str.eq_ignore_ascii_case("on")
        || str.eq_ignore_ascii_case("yes")
        || str.eq_ignore_ascii_case("true")
    {
        Ok(true)
    } else {
        Err(ValError::new(ErrorType::BoolParsing, input))
    }
}

pub fn int_as_bool<'a>(input: &'a impl Input<'a>, int: i64) -> ValResult<'a, bool> {
    if int == 0 {
        Ok(false)
    } else if int == 1 {
        Ok(true)
    } else {
        Err(ValError::new(ErrorType::BoolParsing, input))
    }
}

/// parse a string as an int
///
/// max length of the input is 4300, see
/// https://docs.python.org/3/whatsnew/3.11.html#other-cpython-implementation-changes and
/// https://github.com/python/cpython/issues/95778 for more info in that length bound
pub fn str_as_int<'s, 'l>(input: &'s impl Input<'s>, str: &'l str) -> ValResult<'s, EitherInt<'s>> {
    let len = str.len();
    if len > 4300 {
        Err(ValError::new(ErrorType::IntParsingSize, input))
    } else if let Some(int) = _parse_str(input, str, len) {
        Ok(int)
    } else if let Some(str_stripped) = strip_decimal_zeros(str) {
        if let Some(int) = _parse_str(input, str_stripped, len) {
            Ok(int)
        } else {
            Err(ValError::new(ErrorType::IntParsing, input))
        }
    } else {
        Err(ValError::new(ErrorType::IntParsing, input))
    }
}

/// parse a string as an int, `input` is required here to get lifetimes to match up
///
fn _parse_str<'s, 'l>(_input: &'s impl Input<'s>, str: &'l str, len: usize) -> Option<EitherInt<'s>> {
    if len < 19 {
        if let Ok(i) = str.parse::<i64>() {
            return Some(EitherInt::I64(i));
        }
    } else if let Ok(i) = str.parse::<BigInt>() {
        return Some(EitherInt::BigInt(i));
    }
    None
}

/// we don't want to parse as f64 then call `float_as_int` as it can loose precision for large ints, therefore
/// we strip `.0+` manually instead, then parse as i64
fn strip_decimal_zeros(s: &str) -> Option<&str> {
    if let Some(i) = s.find('.') {
        if s[i + 1..].chars().all(|c| c == '0') {
            return Some(&s[..i]);
        }
    }
    None
}

pub fn float_as_int<'a>(input: &'a impl Input<'a>, float: f64) -> ValResult<'a, EitherInt<'a>> {
    if float == f64::INFINITY || float == f64::NEG_INFINITY || float.is_nan() {
        Err(ValError::new(ErrorType::FiniteNumber, input))
    } else if float % 1.0 != 0.0 {
        Err(ValError::new(ErrorType::IntFromFloat, input))
    } else if (i64::MIN as f64) < float && float < (i64::MAX as f64) {
        Ok(EitherInt::I64(float as i64))
    } else {
        Err(ValError::new(ErrorType::IntParsingSize, input))
    }
}
