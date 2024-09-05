use std::borrow::Cow;

use pyo3::prelude::*;
use pyo3::sync::GILOnceCell;
use pyo3::{intern, Py, PyAny, Python};

use jiter::{JsonErrorType, NumberInt};

use crate::errors::{ErrorTypeDefaults, ValError, ValResult};

use super::{EitherFloat, EitherInt, Input};
static ENUM_META_OBJECT: GILOnceCell<Py<PyAny>> = GILOnceCell::new();

pub fn get_enum_meta_object(py: Python) -> &Bound<'_, PyAny> {
    ENUM_META_OBJECT
        .get_or_init(py, || {
            py.import_bound(intern!(py, "enum"))
                .and_then(|enum_module| enum_module.getattr(intern!(py, "EnumMeta")))
                .unwrap()
                .into()
        })
        .bind(py)
}

pub fn str_as_bool<'py>(input: &(impl Input<'py> + ?Sized), str: &str) -> ValResult<bool> {
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
        Err(ValError::new(ErrorTypeDefaults::BoolParsing, input))
    }
}

pub fn int_as_bool<'py>(input: &(impl Input<'py> + ?Sized), int: i64) -> ValResult<bool> {
    if int == 0 {
        Ok(false)
    } else if int == 1 {
        Ok(true)
    } else {
        Err(ValError::new(ErrorTypeDefaults::BoolParsing, input))
    }
}

/// Strip underscores from strings so that 1_000 can be parsed to 1000
/// Ignore any unicode stuff since this has to be digits and underscores
/// and if it's not subsequent parsing will just fail
fn strip_underscores(s: &str) -> Option<String> {
    // Leading and trailing underscores are not valid in Python (e.g. `int('__1__')` fails)
    // so we match that behavior here.
    // Double consecutive underscores are also not valid
    // If there are no underscores at all, no need to replace anything
    if s.starts_with('_') || s.ends_with('_') || !s.contains('_') || s.contains("__") {
        // no underscores to strip, or underscores in the wrong place
        None
    } else {
        Some(s.replace('_', ""))
    }
}

/// parse a string as an int
/// max length of the input is 4300 which is checked by jiter, see
/// https://docs.python.org/3/whatsnew/3.11.html#other-cpython-implementation-changes and
/// https://github.com/python/cpython/issues/95778 for more info in that length bound
pub fn str_as_int<'py>(input: &(impl Input<'py> + ?Sized), str: &str) -> ValResult<EitherInt<'py>> {
    // we can't move `NumberInt::try_from` into its own function we fail fast if the string is too long
    match NumberInt::try_from(str.as_bytes()) {
        Ok(NumberInt::Int(i)) => return Ok(EitherInt::I64(i)),
        Ok(NumberInt::BigInt(i)) => return Ok(EitherInt::BigInt(i)),
        Err(e) => {
            if e.error_type == JsonErrorType::NumberOutOfRange {
                return Err(ValError::new(ErrorTypeDefaults::IntParsingSize, input));
            }
        }
    }

    if let Some(cleaned_str) = clean_int_str(str) {
        match NumberInt::try_from(cleaned_str.as_ref().as_bytes()) {
            Ok(NumberInt::Int(i)) => Ok(EitherInt::I64(i)),
            Ok(NumberInt::BigInt(i)) => Ok(EitherInt::BigInt(i)),
            Err(_) => Err(ValError::new(ErrorTypeDefaults::IntParsing, input)),
        }
    } else {
        Err(ValError::new(ErrorTypeDefaults::IntParsing, input))
    }
}

/// parse a float as a float
pub fn str_as_float<'py>(input: &(impl Input<'py> + ?Sized), str: &str) -> ValResult<EitherFloat<'py>> {
    match str.trim().parse() {
        Ok(float) => Ok(EitherFloat::F64(float)),
        Err(_) => match strip_underscores(str).and_then(|stripped| stripped.parse().ok()) {
            Some(float) => Ok(EitherFloat::F64(float)),
            None => Err(ValError::new(ErrorTypeDefaults::FloatParsing, input)),
        },
    }
}

fn clean_int_str(mut s: &str) -> Option<Cow<str>> {
    let len_before = s.len();

    // strip leading and trailing whitespace
    s = s.trim();

    // Check for and remove a leading unary plus and ensure the next character is not a unary minus. e.g.: '+-1'.
    if let Some(suffix) = s.strip_prefix('+') {
        if suffix.starts_with('-') {
            return None;
        }
        s = suffix;
    }

    // Remember if the number is negative
    // the `strip_leading_zeros` function will not strip leading zeros for negative numbers
    // therefore we simply "take away" the unary minus sign temporarily and add it back before
    // returning. This allows consistent handling of leading zeros for both positive and negative numbers.
    let mut is_negative = false;
    if let Some(suffix) = s.strip_prefix('-') {
        // Invalidate "--" and "-+" as an integer prefix by returning None
        if suffix.starts_with('-') | suffix.starts_with('+') {
            return None;
        }

        is_negative = true;
        // Continue as usual without the unary minus sign
        s = suffix;
    }

    // strip loading zeros
    s = strip_leading_zeros(s)?;

    // we don't want to parse as f64 then call `float_as_int` as it can lose precision for large ints, therefore
    // we strip `.0+` manually instead
    if let Some(i) = s.find('.') {
        let decimal_part = &s[i + 1..];
        if !decimal_part.is_empty() && decimal_part.chars().all(|c| c == '0') {
            s = &s[..i];
        }
    }

    // remove underscores
    if let Some(str_stripped) = strip_underscores(s) {
        match is_negative {
            true => return Some(("-".to_string() + &str_stripped).into()),
            false => return Some(str_stripped.into()),
        }
    }

    if len_before == s.len() {
        return None;
    }

    match is_negative {
        true => Some(("-".to_string() + s).into()),
        false => Some(s.into()),
    }
}

/// strip leading zeros from a string, we can't simple use `s.trim_start_matches('0')`, because:
/// - we need to keep one zero if the string is only zeros e.g. `000` -> `0`
/// - we need to keep one zero if the string is a float which is an exact int e.g. `00.0` -> `0.0`
/// - underscores within leading zeros should also be stripped e.g. `0_000` -> `0`, but not `_000`
fn strip_leading_zeros(s: &str) -> Option<&str> {
    let mut char_iter = s.char_indices();
    match char_iter.next() {
        // if we get a leading zero we continue
        Some((_, '0')) => (),
        // if we get another digit or unary minus we return the whole string
        Some((_, c)) if ('1'..='9').contains(&c) || c == '-' => return Some(s),
        // anything else is invalid, we return None
        _ => return None,
    };
    for (i, c) in char_iter {
        match c {
            // continue on more leading zeros or if we get an underscore we continue - we're "within the number"
            '0' | '_' => (),
            // any other digit or unary minus we return the rest of the string
            '1'..='9' | '-' => return Some(&s[i..]),
            // if we get a dot we return the rest of the string but include the last zero
            '.' => return Some(&s[(i - 1)..]),
            // anything else is invalid, we return None
            _ => return None,
        }
    }
    // if the string is all zeros (or underscores), we return the last character
    // generally this will be zero, but could be an underscore, which will fail
    Some(&s[s.len() - 1..])
}

pub fn float_as_int<'py>(input: &(impl Input<'py> + ?Sized), float: f64) -> ValResult<EitherInt<'py>> {
    if float.is_infinite() || float.is_nan() {
        Err(ValError::new(ErrorTypeDefaults::FiniteNumber, input))
    } else if float % 1.0 != 0.0 {
        Err(ValError::new(ErrorTypeDefaults::IntFromFloat, input))
    } else if (i64::MIN as f64) < float && float < (i64::MAX as f64) {
        Ok(EitherInt::I64(float as i64))
    } else {
        Err(ValError::new(ErrorTypeDefaults::IntParsingSize, input))
    }
}

pub fn decimal_as_int<'py>(
    input: &(impl Input<'py> + ?Sized),
    decimal: &Bound<'py, PyAny>,
) -> ValResult<EitherInt<'py>> {
    let py = decimal.py();
    if !decimal.call_method0(intern!(py, "is_finite"))?.extract::<bool>()? {
        return Err(ValError::new(ErrorTypeDefaults::FiniteNumber, input));
    }
    let (numerator, denominator) = decimal
        .call_method0(intern!(py, "as_integer_ratio"))?
        .extract::<(Bound<'_, PyAny>, Bound<'_, PyAny>)>()?;
    if denominator.extract::<i64>().map_or(true, |d| d != 1) {
        return Err(ValError::new(ErrorTypeDefaults::IntFromFloat, input));
    }
    Ok(EitherInt::Py(numerator))
}
