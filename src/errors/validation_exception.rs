use std::fmt;
use std::fmt::Write;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::input::repr_string;

use super::kinds::ErrorKind;
use super::line_error::ValLineError;
use super::location::Location;
use super::ValError;

#[pyclass(extends=PyValueError, module="pydantic_core._pydantic_core")]
#[derive(Clone)]
#[cfg_attr(debug_assertions, derive(Debug))]
pub struct ValidationError {
    line_errors: Vec<PyLineError>,
    title: PyObject,
}

impl ValidationError {
    pub fn from_val_error(py: Python, title: PyObject, error: ValError) -> PyErr {
        match error {
            ValError::LineErrors(raw_errors) => {
                let line_errors: Vec<PyLineError> = raw_errors.into_iter().map(|e| e.into_py(py)).collect();
                PyErr::new::<ValidationError, _>((line_errors, title))
            }
            ValError::InternalErr(err) => err,
        }
    }

    fn display(&self, py: Python) -> String {
        let count = self.line_errors.len();
        let plural = if count == 1 { "" } else { "s" };
        let title: &str = self.title.extract(py).unwrap();
        let line_errors = pretty_py_line_errors(py, self.line_errors.iter());
        format!("{} validation error{} for {}\n{}", count, plural, title, line_errors)
    }
}

// used to convert a validation error back to ValError for wrap functions
impl<'a> IntoPy<ValError<'a>> for ValidationError {
    fn into_py(self, py: Python) -> ValError<'a> {
        self.line_errors
            .into_iter()
            .map(|e| e.into_py(py))
            .collect::<Vec<_>>()
            .into()
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
        self.display(py)
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

pub fn pretty_py_line_errors<'a>(py: Python, line_errors_iter: impl Iterator<Item = &'a PyLineError>) -> String {
    line_errors_iter
        .map(|i| i.pretty(py))
        .collect::<Result<Vec<_>, _>>()
        .unwrap_or_else(|err| vec![format!("[error formatting line errors: {}]", err)])
        .join("\n")
}

/// `PyLineError` are the public version of `ValLineError`, as help and used in `ValidationError`s
#[pyclass]
#[derive(Clone)]
#[cfg_attr(debug_assertions, derive(Debug))]
pub struct PyLineError {
    kind: ErrorKind,
    location: Location,
    input_value: PyObject,
}

impl<'a> IntoPy<PyLineError> for ValLineError<'a> {
    fn into_py(self, py: Python<'_>) -> PyLineError {
        PyLineError {
            kind: self.kind,
            location: self.location,
            input_value: self.input_value.to_object(py),
        }
    }
}

/// opposite of above, used to extract line errors from a validation error for wrap functions
impl<'a> IntoPy<ValLineError<'a>> for PyLineError {
    fn into_py(self, _py: Python) -> ValLineError<'a> {
        ValLineError {
            kind: self.kind,
            location: self.location,
            input_value: self.input_value.into(),
        }
    }
}

impl PyLineError {
    pub fn as_dict(&self, py: Python) -> PyResult<PyObject> {
        let dict = PyDict::new(py);
        dict.set_item("kind", self.kind.kind())?;
        dict.set_item("loc", self.location.to_object(py))?;
        dict.set_item("message", self.kind.render_message(py)?)?;
        dict.set_item("input_value", &self.input_value)?;
        if let Some(context) = self.kind.py_dict(py)? {
            dict.set_item("context", context)?;
        }
        Ok(dict.into_py(py))
    }

    fn pretty(&self, py: Python) -> Result<String, fmt::Error> {
        let mut output = String::with_capacity(200);
        write!(output, "{}", self.location)?;

        let message = match self.kind.render_message(py) {
            Ok(message) => message,
            Err(err) => format!("(error rendering message: {})", err),
        };
        write!(output, "  {} [kind={}", message, self.kind.kind())?;

        let input_value = self.input_value.as_ref(py);
        let input_str = match repr_string(input_value) {
            Ok(s) => s,
            Err(_) => input_value.to_string(),
        };
        truncate_input_value!(output, input_str);

        if let Ok(type_) = input_value.get_type().name() {
            write!(output, ", input_type={}", type_)?;
        }
        output.push(']');
        Ok(output)
    }
}
