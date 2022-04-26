use super::Input;
use crate::errors::{err_val_error, ErrorKind, InputValue, ValResult};

#[inline]
pub fn str_as_bool<'a>(input: &'a dyn Input, str: &str) -> ValResult<'a, bool> {
    let s_lower: String = str.chars().map(|c| c.to_ascii_lowercase()).collect();
    match s_lower.as_str() {
        "0" | "off" | "f" | "false" | "n" | "no" => Ok(false),
        "1" | "on" | "t" | "true" | "y" | "yes" => Ok(true),
        _ => err_val_error!(input_value = InputValue::InputRef(input), kind = ErrorKind::BoolParsing),
    }
}

#[inline]
pub fn int_as_bool(input: &dyn Input, int: i64) -> ValResult<bool> {
    if int == 0 {
        Ok(false)
    } else if int == 1 {
        Ok(true)
    } else {
        err_val_error!(input_value = InputValue::InputRef(input), kind = ErrorKind::BoolParsing)
    }
}

#[inline]
pub fn str_as_int<'s, 'l>(input: &'s dyn Input, str: &'l str) -> ValResult<'s, i64> {
    if let Ok(i) = str.parse::<i64>() {
        Ok(i)
    } else if let Ok(f) = str.parse::<f64>() {
        float_as_int(input, f)
    } else {
        err_val_error!(input_value = InputValue::InputRef(input), kind = ErrorKind::IntParsing)
    }
}

pub fn float_as_int(input: &dyn Input, float: f64) -> ValResult<i64> {
    if float % 1.0 == 0.0 {
        Ok(float as i64)
    } else {
        err_val_error!(
            input_value = InputValue::InputRef(input),
            kind = ErrorKind::IntFromFloat
        )
    }
}
