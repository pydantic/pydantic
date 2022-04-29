use std::error::Error;
use std::fmt;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use pyo3::PyErrArguments;

use strum::EnumMessage;

use super::kinds::ErrorKind;
use super::line_error::{Context, LocItem, Location, ValLineError};

use super::ValError;

#[pyclass(extends=PyValueError)]
#[derive(Debug)]
pub struct ValidationError {
    line_errors: Vec<PyLineError>,
    title: String,
}

pub fn as_validation_err(py: Python, model_name: &str, error: ValError) -> PyErr {
    match error {
        ValError::LineErrors(raw_errors) => {
            let line_errors: Vec<PyLineError> = raw_errors.into_iter().map(|e| PyLineError::new(py, e)).collect();
            ValidationError::new_err((line_errors, model_name.to_string()))
        }
        ValError::InternalErr(err) => err,
    }
}

impl fmt::Display for ValidationError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.display(None))
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

    fn display(&self, py: Option<Python>) -> String {
        let count = self.line_errors.len();
        let plural = if count == 1 { "" } else { "s" };
        let loc = self
            .line_errors
            .iter()
            .map(|i| i.pretty(py))
            .collect::<Vec<String>>()
            .join("\n");
        format!("{} validation error{} for {}\n{}", count, plural, self.title, loc)
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
    fn py_new(line_errors: Vec<PyLineError>, title: String) -> Self {
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
        self.display(Some(py))
    }

    fn __str__(&self, py: Python) -> String {
        self.__repr__(py)
    }
}

/// `PyLineError` are the public version of `ValLineError`, as help and used in `ValidationError`s
#[pyclass]
#[derive(Debug, Clone)]
pub struct PyLineError {
    kind: ErrorKind,
    location: Location,
    message: Option<String>,
    input_value: PyObject,
    context: Context,
}

impl PyLineError {
    pub fn new(py: Python, raw_error: ValLineError) -> Self {
        Self {
            kind: raw_error.kind,
            location: raw_error.location,
            message: raw_error.message,
            input_value: raw_error.input_value.to_py(py),
            context: raw_error.context,
        }
    }

    pub fn as_dict(&self, py: Python) -> PyResult<PyObject> {
        let dict = PyDict::new(py);
        dict.set_item("kind", self.kind())?;
        dict.set_item("loc", self.location(py))?;
        dict.set_item("message", self.message())?;
        dict.set_item("input_value", &self.input_value)?;
        if !self.context.is_empty() {
            dict.set_item("context", &self.context)?;
        }
        Ok(dict.into_py(py))
    }

    fn kind(&self) -> String {
        self.kind.to_string()
    }

    fn location(&self, py: Python) -> PyObject {
        let mut loc: Vec<PyObject> = Vec::with_capacity(self.location.len());
        for location in &self.location {
            let item: PyObject = match location {
                LocItem::S(key) => key.into_py(py),
                LocItem::I(index) => index.into_py(py),
            };
            loc.push(item);
        }
        loc.into_py(py)
    }

    fn message(&self) -> String {
        let raw = self.raw_message();
        if self.context.is_empty() {
            raw
        } else {
            self.context.render(raw)
        }
    }

    fn raw_message(&self) -> String {
        // TODO string substitution
        if let Some(ref message) = self.message {
            message.to_string()
        } else {
            match self.kind.get_message() {
                Some(message) => message.to_string(),
                None => self.kind(),
            }
        }
    }

    fn pretty(&self, py: Option<Python>) -> String {
        let mut output = String::with_capacity(200);
        if !self.location.is_empty() {
            let loc = self
                .location
                .iter()
                .map(|i| i.to_string())
                .collect::<Vec<String>>()
                .join(" -> ");
            output.push_str(&loc);
            output.push('\n');
        }

        output.push_str(&format!("  {} [kind={}", self.message(), self.kind()));

        if !self.context.is_empty() {
            output.push_str(&format!(", context={}", self.context));
        }
        if let Some(py) = py {
            let input_value = self.input_value.as_ref(py);
            let input_str = match repr(input_value) {
                Ok(s) => s,
                Err(_) => input_value.to_string(),
            };
            output.push_str(", input_value=");
            output.push_str(&truncate(input_str));

            if let Ok(type_) = input_value.get_type().name() {
                output.push_str(&format!(", input_type={}", type_));
            }
        } else {
            output.push_str(&truncate(self.input_value.to_string()));
        }
        output.push(']');
        output
    }
}

fn truncate(s: String) -> String {
    if s.len() > 50 {
        format!("{}...{}", &s[0..25], &s[s.len() - 24..])
    } else {
        s
    }
}

fn repr(v: &PyAny) -> PyResult<String> {
    v.repr()?.extract()
}
