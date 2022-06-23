use std::error::Error;
use std::fmt;
use std::fmt::Write;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use strum::EnumMessage;

use crate::input::repr_string;

use super::kinds::ErrorKind;
use super::line_error::{Context, ValLineError};
use super::location::Location;
use super::ValError;

#[pyclass(extends=PyValueError, module="pydantic_core._pydantic_core")]
#[derive(Debug)]
pub struct ValidationError {
    line_errors: Vec<PyLineError>,
    title: PyObject,
}

impl fmt::Display for ValidationError {
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.display(None))
    }
}

impl ValidationError {
    pub fn from_val_error(py: Python, title: PyObject, error: ValError) -> PyErr {
        match error {
            ValError::LineErrors(raw_errors) => {
                let line_errors: Vec<PyLineError> = raw_errors.into_iter().map(|e| PyLineError::new(py, e)).collect();
                PyErr::new::<ValidationError, _>((line_errors, title))
            }
            ValError::InternalErr(err) => err,
        }
    }

    fn display(&self, py: Option<Python>) -> String {
        let count = self.line_errors.len();
        let plural = if count == 1 { "" } else { "s" };
        let title: &str = match py {
            Some(py) => self.title.extract(py).unwrap(),
            None => "Schema",
        };
        let line_errors = self
            .line_errors
            .iter()
            .map(|i| i.pretty(py))
            .collect::<Result<Vec<_>, _>>()
            .unwrap_or_else(|err| vec![format!("[error formatting line errors: {}]", err)])
            .join("\n");
        format!("{} validation error{} for {}\n{}", count, plural, title, line_errors)
    }
}

impl Error for ValidationError {
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        // we could in theory set self.source as `ValError::LineErrors(line_errors.clone())`, then return that here
        // source is not used, and I can't imagine why it would be
        None
    }
}

#[pymethods]
impl ValidationError {
    #[new]
    fn py_new(line_errors: Vec<PyLineError>, title: PyObject) -> Self {
        Self { line_errors, title }
    }

    #[getter]
    fn title(&self, py: Python) -> PyObject {
        self.title.clone_ref(py)
    }

    fn error_count(&self) -> usize {
        self.line_errors.len()
    }

    fn errors(&self, py: Python) -> PyResult<PyObject> {
        Ok(self
            .line_errors
            .iter()
            .map(|e| e.as_dict(py))
            .collect::<PyResult<Vec<PyObject>>>()?
            .into_py(py))
    }

    fn __repr__(&self, py: Python) -> String {
        self.display(Some(py))
    }

    fn __str__(&self, py: Python) -> String {
        self.__repr__(py)
    }
}

macro_rules! truncate_input_value {
    ($out:expr, $value:expr) => {
        if $value.len() > 50 {
            write!(
                $out,
                ", input_value={}...{}",
                &$value[0..25],
                &$value[$value.len() - 24..]
            )?;
        } else {
            write!($out, ", input_value={}", $value)?;
        }
    };
}

/// `PyLineError` are the public version of `ValLineError`, as help and used in `ValidationError`s
#[pyclass]
#[derive(Debug, Clone)]
pub struct PyLineError {
    kind: ErrorKind,
    location: Location,
    input_value: PyObject,
    context: Context,
}

impl PyLineError {
    pub fn new(py: Python, raw_error: ValLineError) -> Self {
        Self {
            kind: raw_error.kind,
            location: match raw_error.reverse_location.len() {
                0..=1 => raw_error.reverse_location,
                _ => raw_error.reverse_location.into_iter().rev().collect(),
            },
            input_value: raw_error.input_value.to_object(py),
            context: raw_error.context,
        }
    }

    pub fn as_dict(&self, py: Python) -> PyResult<PyObject> {
        let dict = PyDict::new(py);
        dict.set_item("kind", self.kind())?;
        dict.set_item("loc", self.location.to_object(py))?;
        dict.set_item("message", self.get_message())?;
        dict.set_item("input_value", &self.input_value)?;
        if !self.context.is_empty() {
            dict.set_item("context", &self.context)?;
        }
        Ok(dict.into_py(py))
    }

    fn kind(&self) -> String {
        self.kind.to_string()
    }

    fn get_message(&self) -> String {
        let raw = match self.kind.get_message() {
            Some(message) => message.to_string(),
            None => self.kind(),
        };
        if self.context.is_empty() {
            raw
        } else {
            self.context.render(raw)
        }
    }

    fn pretty(&self, py: Option<Python>) -> Result<String, fmt::Error> {
        let mut output = String::with_capacity(200);
        if !self.location.is_empty() {
            let loc = self
                .location
                .iter()
                .map(|i| i.to_string())
                .collect::<Vec<String>>()
                .join(" -> ");
            writeln!(output, "{}", &loc)?;
        }

        write!(output, "  {} [kind={}", self.get_message(), self.kind())?;

        if !self.context.is_empty() {
            write!(output, ", context={}", self.context)?;
        }
        if let Some(py) = py {
            let input_value = self.input_value.as_ref(py);
            let input_str = match repr_string(input_value) {
                Ok(s) => s,
                Err(_) => input_value.to_string(),
            };
            truncate_input_value!(output, input_str);

            if let Ok(type_) = input_value.get_type().name() {
                write!(output, ", input_type={}", type_)?;
            }
        } else {
            truncate_input_value!(output, self.input_value.to_string());
        }
        output.push(']');
        Ok(output)
    }
}
