use std::error::Error;
use std::fmt;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use crate::errors::ValLineError;
use pyo3::PyErrArguments;

#[pyclass(extends=PyValueError)]
#[derive(Debug)]
pub struct ValidationError {
    line_errors: Vec<ValLineError>,
    model_name: String,
}

impl ValidationError {
    #[inline]
    pub fn new_err<A>(args: A) -> PyErr
    where
        A: PyErrArguments + Send + Sync + 'static,
    {
        PyErr::new::<ValidationError, A>(args)
    }
}

impl fmt::Display for ValidationError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", display_errors(&self.line_errors, &self.model_name))
    }
}

impl Error for ValidationError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        None
    }
}

#[pymethods]
impl ValidationError {
    #[new]
    fn py_new(line_errors: Vec<ValLineError>, model_name: String) -> Self {
        Self {
            line_errors,
            model_name,
        }
    }

    fn errors(&self) -> Vec<ValLineError> {
        self.line_errors.clone()
    }

    fn __repr__(&self) -> String {
        display_errors(&self.line_errors, &self.model_name)
    }

    fn __str__(&self) -> String {
        self.__repr__()
    }
}

pub fn display_errors(errors: &[ValLineError], model_name: &str) -> String {
    let count = errors.len();
    let plural = if count == 1 { "" } else { "s" };
    let loc = errors
        .iter()
        .map(|i| i.to_string())
        .collect::<Vec<String>>()
        .join("\n  ");
    format!("{} validation error{} for {}\n  {}", count, plural, model_name, loc)
}
