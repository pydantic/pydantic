use std::fmt;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use regex::Regex;

macro_rules! dict_get {
    ($dict:ident, $key:expr, $type:ty) => {
        match $dict.get_item($key) {
            Some(t) => Some(<$type>::extract(t)?),
            None => None,
        }
    };
}
pub(crate) use dict_get;

macro_rules! dict_get_required {
    ($dict:ident, $key:expr, $type:ty) => {
        match $dict.get_item($key) {
            Some(t) => Ok(<$type>::extract(t)?),
            None => py_error!(r#""{}" is required"#, $key),
        }
    };
}
pub(crate) use dict_get_required;

macro_rules! py_error {
    ($msg:expr) => {
        py_error!(crate::SchemaError; $msg)
    };
    ($msg:expr, $( $msg_args:expr ),+ ) => {
        py_error!(crate::SchemaError; $msg, $( $msg_args ),+)
    };

    ($error_type:ty; $msg:expr) => {
        Err(<$error_type>::new_err($msg))
    };

    ($error_type:ty; $msg:expr, $( $msg_args:expr ),+ ) => {
        Err(<$error_type>::new_err(format!($msg, $( $msg_args ),+)))
    };
}
pub(crate) use py_error;

macro_rules! dict_create {
    ($py:ident, $($k:expr => $v:expr),*) => {{
        pyo3::types::IntoPyDict::into_py_dict([$(($k, $v),)*], $py).into()
    }};
}
pub(crate) use dict_create;

#[pyclass]
#[derive(Debug, Clone)]
pub struct RegexPattern {
    regex: Regex,
}

impl RegexPattern {
    pub fn is_match(&self, string: &str) -> bool {
        self.regex.is_match(string)
    }
}

#[pymethods]
impl RegexPattern {
    #[new]
    pub fn py_new(pattern: &PyAny) -> PyResult<Self> {
        let pattern: &str = pattern.extract()?;
        let regex = Regex::new(pattern).map_err(|e| PyValueError::new_err(e.to_string()))?;
        Ok(Self { regex })
    }

    fn __repr__(&self) -> PyResult<String> {
        Ok(format!("RegexPattern({})", self))
    }
}

impl fmt::Display for RegexPattern {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}", self.regex)
    }
}
