use std::fmt;
use std::fmt::Write;

use crate::errors::LocItem;
use pyo3::exceptions::PyValueError;
use pyo3::ffi;
use pyo3::ffi::Py_ssize_t;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use crate::build_tools::{py_error_type, safe_repr};

use super::line_error::ValLineError;
use super::location::Location;
use super::types::ErrorType;
use super::ValError;

#[pyclass(extends=PyValueError, module="pydantic_core._pydantic_core")]
#[derive(Clone)]
#[cfg_attr(debug_assertions, derive(Debug))]
pub struct ValidationError {
    line_errors: Vec<PyLineError>,
    title: PyObject,
}

impl ValidationError {
    pub fn from_val_error(py: Python, title: PyObject, error: ValError, outer_location: Option<LocItem>) -> PyErr {
        match error {
            ValError::LineErrors(raw_errors) => {
                let line_errors: Vec<PyLineError> = match outer_location {
                    Some(outer_location) => raw_errors
                        .into_iter()
                        .map(|e| e.with_outer_location(outer_location.clone()).into_py(py))
                        .collect(),
                    None => raw_errors.into_iter().map(|e| e.into_py(py)).collect(),
                };
                PyErr::new::<ValidationError, _>((line_errors, title))
            }
            ValError::InternalErr(err) => err,
            ValError::Omit => Self::omit_error(),
        }
    }

    fn display(&self, py: Python) -> String {
        let count = self.line_errors.len();
        let plural = if count == 1 { "" } else { "s" };
        let title: &str = self.title.extract(py).unwrap();
        let line_errors = pretty_py_line_errors(py, self.line_errors.iter());
        format!("{count} validation error{plural} for {title}\n{line_errors}")
    }

    pub fn omit_error() -> PyErr {
        py_error_type!("Uncaught Omit error, please check your usage of `default` validators.")
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

    fn errors(&self, py: Python, include_context: Option<bool>) -> PyResult<Py<PyList>> {
        // taken approximately from the pyo3, but modified to return the error during iteration
        // https://github.com/PyO3/pyo3/blob/a3edbf4fcd595f0e234c87d4705eb600a9779130/src/types/list.rs#L27-L55
        unsafe {
            let ptr = ffi::PyList_New(self.line_errors.len() as Py_ssize_t);

            // We create the `Py` pointer here for two reasons:
            // - panics if the ptr is null
            // - its Drop cleans up the list if user code or the asserts panic.
            let list: Py<PyList> = Py::from_owned_ptr(py, ptr);

            for (index, line_error) in (0_isize..).zip(&self.line_errors) {
                let item = line_error.as_dict(py, include_context)?;
                ffi::PyList_SET_ITEM(ptr, index, item.into_ptr());
            }

            Ok(list)
        }
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
        .unwrap_or_else(|err| vec![format!("[error formatting line errors: {err}]")])
        .join("\n")
}

/// `PyLineError` are the public version of `ValLineError`, as help and used in `ValidationError`s
#[pyclass]
#[derive(Clone)]
#[cfg_attr(debug_assertions, derive(Debug))]
pub struct PyLineError {
    error_type: ErrorType,
    location: Location,
    input_value: PyObject,
}

impl<'a> IntoPy<PyLineError> for ValLineError<'a> {
    fn into_py(self, py: Python<'_>) -> PyLineError {
        PyLineError {
            error_type: self.error_type,
            location: self.location,
            input_value: self.input_value.to_object(py),
        }
    }
}

/// opposite of above, used to extract line errors from a validation error for wrap functions
impl<'a> IntoPy<ValLineError<'a>> for PyLineError {
    fn into_py(self, _py: Python) -> ValLineError<'a> {
        ValLineError {
            error_type: self.error_type,
            location: self.location,
            input_value: self.input_value.into(),
        }
    }
}

impl PyLineError {
    pub fn as_dict(&self, py: Python, include_context: Option<bool>) -> PyResult<PyObject> {
        let dict = PyDict::new(py);
        dict.set_item("type", self.error_type.type_string())?;
        dict.set_item("loc", self.location.to_object(py))?;
        dict.set_item("msg", self.error_type.render_message(py)?)?;
        dict.set_item("input", &self.input_value)?;
        if include_context.unwrap_or(true) {
            if let Some(context) = self.error_type.py_dict(py)? {
                dict.set_item("ctx", context)?;
            }
        }
        Ok(dict.into_py(py))
    }

    fn pretty(&self, py: Python) -> Result<String, fmt::Error> {
        let mut output = String::with_capacity(200);
        write!(output, "{}", self.location)?;

        let message = match self.error_type.render_message(py) {
            Ok(message) => message,
            Err(err) => format!("(error rendering message: {err})"),
        };
        write!(output, "  {message} [type={}", self.error_type.type_string())?;

        let input_value = self.input_value.as_ref(py);
        let input_str = safe_repr(input_value);
        truncate_input_value!(output, input_str);

        if let Ok(type_) = input_value.get_type().name() {
            write!(output, ", input_type={type_}")?;
        }
        output.push(']');
        Ok(output)
    }
}
