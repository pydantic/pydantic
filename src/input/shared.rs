use std::collections::HashSet;

use lazy_static::lazy_static;

use pyo3::prelude::*;

use crate::errors::{err_val_error, ErrorKind, ValResult};

use super::traits::ToPy;

lazy_static! {
    static ref BOOL_FALSE_CELL: HashSet<&'static str> = HashSet::from(["0", "off", "f", "false", "n", "no"]);
}

lazy_static! {
    static ref BOOL_TRUE_CELL: HashSet<&'static str> = HashSet::from(["1", "on", "t", "true", "y", "yes"]);
}

#[inline]
pub fn str_as_bool(py: Python, str: &str) -> ValResult<bool> {
    let s_lower = str.to_lowercase();
    if BOOL_FALSE_CELL.contains(s_lower.as_str()) {
        Ok(false)
    } else if BOOL_TRUE_CELL.contains(s_lower.as_str()) {
        Ok(true)
    } else {
        err_val_error!(py, str, kind = ErrorKind::BoolParsing)
    }
}

#[inline]
pub fn int_as_bool(py: Python, int: i64) -> ValResult<bool> {
    if int == 0 {
        Ok(false)
    } else if int == 1 {
        Ok(true)
    } else {
        err_val_error!(py, int, kind = ErrorKind::BoolParsing)
    }
}
