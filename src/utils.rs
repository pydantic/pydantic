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

#[pyclass]
#[derive(Debug)]
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
    fn py_new(py: Python, pattern: PyObject) -> PyResult<Self> {
        let p: RegexPattern = pattern.extract(py)?;
        Ok(p)
    }

    fn __repr__(&self) -> PyResult<String> {
        Ok(format!("RegexPattern({})", self))
    }
}

impl<'source> FromPyObject<'source> for RegexPattern {
    fn extract(obj: &'source PyAny) -> Result<Self, PyErr> {
        let pattern: &str = obj.extract()?;
        let regex = Regex::new(pattern).map_err(|e| PyValueError::new_err(e.to_string()))?;
        Ok(Self { regex })
    }
}

impl fmt::Display for RegexPattern {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}", self.regex)
    }
}
