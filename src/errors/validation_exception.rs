use std::error::Error;
use std::fmt;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::PyErrArguments;

use crate::errors::ValLineError;

#[pyclass(extends=PyValueError)]
#[derive(Debug)]
pub struct ValidationError {
    line_errors: Vec<ValLineError>,
    title: String,
}

impl fmt::Display for ValidationError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", display_errors(&self.line_errors, &self.title, None))
    }
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

impl Error for ValidationError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        // we could in theory set self.source as `ValError::LineErrors(line_errors.clone())`, then return that here
        // source is not used, and I can't imagine why it would be
        None
    }
}

#[pymethods]
impl ValidationError {
    #[new]
    fn py_new(line_errors: Vec<ValLineError>, title: String) -> Self {
        Self { line_errors, title }
    }

    #[getter]
    fn title(&self) -> String {
        self.title.clone()
    }

    fn error_count(&self) -> usize {
        self.line_errors.len()
    }

    fn errors(&self, py: Python) -> PyResult<PyObject> {
        let mut errors: Vec<PyObject> = Vec::with_capacity(self.line_errors.len());
        for line_error in &self.line_errors {
            errors.push(line_error.as_dict(py)?);
        }
        Ok(errors.into_py(py))
    }

    fn __repr__(&self, py: Python) -> String {
        display_errors(&self.line_errors, &self.title, Some(py))
    }

    fn __str__(&self, py: Python) -> String {
        self.__repr__(py)
    }
}

pub fn display_errors(errors: &[ValLineError], title: &str, py: Option<Python>) -> String {
    let count = errors.len();
    let plural = if count == 1 { "" } else { "s" };
    let loc = errors.iter().map(|i| i.pretty(py)).collect::<Vec<String>>().join("\n");
    format!("{} validation error{} for {}\n{}", count, plural, title, loc)
}
