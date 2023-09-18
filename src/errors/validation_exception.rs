use std::fmt;
use std::fmt::{Display, Write};
use std::str::from_utf8;

use pyo3::exceptions::{PyKeyError, PyTypeError, PyValueError};
use pyo3::ffi;
use pyo3::once_cell::GILOnceCell;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyString};
use pyo3::{intern, AsPyPointer};
use serde::ser::{Error, SerializeMap, SerializeSeq};
use serde::{Serialize, Serializer};

use serde_json::ser::PrettyFormatter;

use crate::build_tools::py_schema_error_type;
use crate::errors::LocItem;
use crate::get_pydantic_version;
use crate::serializers::{SerMode, SerializationState};
use crate::tools::{safe_repr, SchemaDict};

use super::line_error::ValLineError;
use super::location::Location;
use super::types::{ErrorMode, ErrorType};
use super::value_exception::PydanticCustomError;
use super::{InputValue, ValError};

#[pyclass(extends=PyValueError, module="pydantic_core._pydantic_core")]
#[derive(Clone)]
#[cfg_attr(debug_assertions, derive(Debug))]
pub struct ValidationError {
    line_errors: Vec<PyLineError>,
    title: PyObject,
    error_mode: ErrorMode,
    hide_input: bool,
}

impl ValidationError {
    pub fn new(line_errors: Vec<PyLineError>, title: PyObject, error_mode: ErrorMode, hide_input: bool) -> Self {
        Self {
            line_errors,
            title,
            error_mode,
            hide_input,
        }
    }

    pub fn from_val_error(
        py: Python,
        title: PyObject,
        error_mode: ErrorMode,
        error: ValError,
        outer_location: Option<LocItem>,
        hide_input: bool,
        validation_error_cause: bool,
    ) -> PyErr {
        match error {
            ValError::LineErrors(raw_errors) => {
                let line_errors: Vec<PyLineError> = match outer_location {
                    Some(outer_location) => raw_errors
                        .into_iter()
                        .map(|e| e.with_outer_location(outer_location.clone()).into_py(py))
                        .collect(),
                    None => raw_errors.into_iter().map(|e| e.into_py(py)).collect(),
                };

                let validation_error = Self::new(line_errors, title, error_mode, hide_input);

                match Py::new(py, validation_error) {
                    Ok(err) => {
                        if validation_error_cause {
                            // Will return an import error if the backport was needed and not installed:
                            if let Some(cause_problem) = ValidationError::maybe_add_cause(err.borrow(py), py) {
                                return cause_problem;
                            }
                        }
                        PyErr::from_value(err.as_ref(py))
                    }
                    Err(err) => err,
                }
            }
            ValError::InternalErr(err) => err,
            ValError::Omit => Self::omit_error(),
            ValError::UseDefault => Self::use_default_error(),
        }
    }

    pub fn display(&self, py: Python, prefix_override: Option<&'static str>, hide_input: bool) -> String {
        let url_prefix = get_url_prefix(py, include_url_env(py));
        let line_errors = pretty_py_line_errors(py, &self.error_mode, self.line_errors.iter(), url_prefix, hide_input);
        if let Some(prefix) = prefix_override {
            format!("{prefix}\n{line_errors}")
        } else {
            let count = self.line_errors.len();
            let plural = if count == 1 { "" } else { "s" };
            let title: &str = self.title.extract(py).unwrap();
            format!("{count} validation error{plural} for {title}\n{line_errors}")
        }
    }

    pub fn omit_error() -> PyErr {
        py_schema_error_type!("Uncaught Omit error, please check your usage of `default` validators.")
    }

    pub fn use_default_error() -> PyErr {
        py_schema_error_type!("Uncaught UseDefault error, please check your usage of `default` validators.")
    }

    fn maybe_add_cause(self_: PyRef<'_, Self>, py: Python) -> Option<PyErr> {
        let mut user_py_errs = vec![];
        for line_error in &self_.line_errors {
            if let ErrorType::AssertionError {
                error: Some(err),
                context: _,
            }
            | ErrorType::ValueError {
                error: Some(err),
                context: _,
            } = &line_error.error_type
            {
                let note: PyObject = if let Location::Empty = &line_error.location {
                    "Pydantic: cause of loc: root".into_py(py)
                } else {
                    format!(
                        "Pydantic: cause of loc: {}",
                        // Location formats with a newline at the end, hence the trim()
                        line_error.location.to_string().trim()
                    )
                    .into_py(py)
                };

                // Notes only support 3.11 upwards:
                #[cfg(Py_3_11)]
                {
                    // Add the location context as a note, no direct c api for this,
                    // fine performance wise, add_note() goes directly to C: "(PyCFunction)BaseException_add_note":
                    // https://github.com/python/cpython/blob/main/Objects/exceptions.c
                    if err.call_method1(py, "add_note", (format!("\n{note}"),)).is_ok() {
                        user_py_errs.push(err.clone_ref(py));
                    }
                }

                // Pre 3.11 notes support, use a UserWarning exception instead:
                #[cfg(not(Py_3_11))]
                {
                    use pyo3::exceptions::PyUserWarning;

                    let wrapped = PyUserWarning::new_err((note,));
                    wrapped.set_cause(py, Some(PyErr::from_value(err.as_ref(py))));
                    user_py_errs.push(wrapped);
                }
            }
        }

        // Only add the cause if there are actually python user exceptions to show:
        if !user_py_errs.is_empty() {
            let title = "Pydantic User Code Exceptions";

            // Native ExceptionGroup(s) only supported 3.11 and later:
            #[cfg(Py_3_11)]
            let cause = {
                use pyo3::exceptions::PyBaseExceptionGroup;
                Some(PyBaseExceptionGroup::new_err((title, user_py_errs)).into_py(py))
            };

            // Pre 3.11 ExceptionGroup support, use the python backport instead:
            // If something's gone wrong with the backport, just don't add the cause:
            #[cfg(not(Py_3_11))]
            let cause = {
                use pyo3::exceptions::PyImportError;
                match py.import("exceptiongroup") {
                Ok(py_mod) => match py_mod.getattr("ExceptionGroup") {
                    Ok(group_cls) => match group_cls.call1((title, user_py_errs)) {
                        Ok(group_instance) => Some(group_instance.into_py(py)),
                        Err(_) => None,
                    },
                    Err(_) => None,
                },
                Err(_) => return Some(PyImportError::new_err("validation_error_cause flag requires the exceptiongroup module backport to be installed when used on Python <3.11.")),
            }
            };

            // Set the cause to the ValidationError:
            if let Some(cause) = cause {
                unsafe {
                    // PyException_SetCause _steals_ a reference to cause, so must use .into_ptr()
                    ffi::PyException_SetCause(self_.as_ptr(), cause.into_ptr());
                }
            }
        }
        None
    }
}

static URL_ENV_VAR: GILOnceCell<bool> = GILOnceCell::new();

fn _get_include_url_env() -> bool {
    match std::env::var("PYDANTIC_ERRORS_OMIT_URL") {
        Ok(val) => val.is_empty(),
        Err(_) => true,
    }
}

fn include_url_env(py: Python) -> bool {
    *URL_ENV_VAR.get_or_init(py, _get_include_url_env)
}

static URL_PREFIX: GILOnceCell<String> = GILOnceCell::new();

fn get_formated_url(py: Python) -> &'static str {
    let pydantic_version = match get_pydantic_version(py) {
        // include major and minor version only
        Some(value) => value.split('.').collect::<Vec<&str>>()[..2].join("."),
        None => "latest".to_string(),
    };
    URL_PREFIX.get_or_init(py, || format!("https://errors.pydantic.dev/{pydantic_version}/v/"))
}

fn get_url_prefix(py: Python, include_url: bool) -> Option<&str> {
    if include_url {
        Some(get_formated_url(py))
    } else {
        None
    }
}

// used to convert a validation error back to ValError for wrap functions
impl ValidationError {
    pub(crate) fn into_val_error(self, py: Python<'_>) -> ValError<'_> {
        self.line_errors
            .into_iter()
            .map(|e| e.into_val_line_error(py))
            .collect::<Vec<_>>()
            .into()
    }
}

#[pymethods]
impl ValidationError {
    #[staticmethod]
    #[pyo3(signature = (title, line_errors, error_mode="python", hide_input=false))]
    fn from_exception_data(
        py: Python,
        title: PyObject,
        line_errors: &PyList,
        error_mode: &str,
        hide_input: bool,
    ) -> PyResult<Py<Self>> {
        Py::new(
            py,
            Self {
                line_errors: line_errors.iter().map(PyLineError::try_from).collect::<PyResult<_>>()?,
                title,
                error_mode: ErrorMode::try_from(error_mode)?,
                hide_input,
            },
        )
    }

    #[getter]
    fn title(&self, py: Python) -> PyObject {
        self.title.clone_ref(py)
    }

    pub fn error_count(&self) -> usize {
        self.line_errors.len()
    }

    #[pyo3(signature = (*, include_url = true, include_context = true))]
    pub fn errors(&self, py: Python, include_url: bool, include_context: bool) -> PyResult<Py<PyList>> {
        let url_prefix = get_url_prefix(py, include_url);
        let mut iteration_error = None;
        let list = PyList::new(
            py,
            // PyList::new takes ExactSizeIterator, so if an error occurs during iteration we
            // fill the list with None before returning the error; the list will then be thrown
            // away safely.
            self.line_errors.iter().map(|e| -> PyObject {
                if iteration_error.is_some() {
                    return py.None();
                }
                e.as_dict(py, url_prefix, include_context, &self.error_mode)
                    .unwrap_or_else(|err| {
                        iteration_error = Some(err);
                        py.None()
                    })
            }),
        );
        if let Some(err) = iteration_error {
            Err(err)
        } else {
            Ok(list.into())
        }
    }

    #[pyo3(signature = (*, indent = None, include_url = true, include_context = true))]
    pub fn json<'py>(
        &self,
        py: Python<'py>,
        indent: Option<usize>,
        include_url: bool,
        include_context: bool,
    ) -> PyResult<&'py PyString> {
        let state = SerializationState::new("iso8601", "utf8")?;
        let extra = state.extra(py, &SerMode::Json, true, false, false, true, None);
        let serializer = ValidationErrorSerializer {
            py,
            line_errors: &self.line_errors,
            url_prefix: get_url_prefix(py, include_url),
            include_context,
            extra: &extra,
            error_mode: &self.error_mode,
        };

        let writer: Vec<u8> = Vec::with_capacity(self.line_errors.len() * 200);
        let bytes = match indent {
            Some(indent) => {
                let indent = vec![b' '; indent];
                let formatter = PrettyFormatter::with_indent(&indent);
                let mut ser = serde_json::Serializer::with_formatter(writer, formatter);
                serializer.serialize(&mut ser).map_err(json_py_err)?;
                ser.into_inner()
            }
            None => {
                let mut ser = serde_json::Serializer::new(writer);
                serializer.serialize(&mut ser).map_err(json_py_err)?;
                ser.into_inner()
            }
        };
        let s = from_utf8(&bytes).map_err(json_py_err)?;
        Ok(PyString::new(py, s))
    }

    fn __repr__(&self, py: Python) -> String {
        self.display(py, None, self.hide_input)
    }

    fn __str__(&self, py: Python) -> String {
        self.__repr__(py)
    }
}

// TODO: is_utf8_char_boundary, floor_char_boundary and ceil_char_boundary
// with builtin methods once https://github.com/rust-lang/rust/issues/93743 is resolved
// These are just copy pasted from the current implementation
const fn is_utf8_char_boundary(value: u8) -> bool {
    // This is bit magic equivalent to: b < 128 || b >= 192
    (value as i8) >= -0x40
}

fn floor_char_boundary(value: &str, index: usize) -> usize {
    if index >= value.len() {
        value.len()
    } else {
        let lower_bound = index.saturating_sub(3);
        let new_index = value.as_bytes()[lower_bound..=index]
            .iter()
            .rposition(|b| is_utf8_char_boundary(*b));

        // SAFETY: we know that the character boundary will be within four bytes
        unsafe { lower_bound + new_index.unwrap_unchecked() }
    }
}

pub fn ceil_char_boundary(value: &str, index: usize) -> usize {
    let upper_bound = Ord::min(index + 4, value.len());
    value.as_bytes()[index..upper_bound]
        .iter()
        .position(|b| is_utf8_char_boundary(*b))
        .map_or(upper_bound, |pos| pos + index)
}

macro_rules! truncate_input_value {
    ($out:expr, $value:expr) => {
        if $value.len() > 50 {
            write!(
                $out,
                ", input_value={}...{}",
                &$value[0..floor_char_boundary($value, 25)],
                &$value[ceil_char_boundary($value, $value.len() - 24)..]
            )?;
        } else {
            write!($out, ", input_value={}", $value)?;
        }
    };
}

pub fn pretty_py_line_errors<'a>(
    py: Python,
    error_mode: &ErrorMode,
    line_errors_iter: impl Iterator<Item = &'a PyLineError>,
    url_prefix: Option<&str>,
    hide_input: bool,
) -> String {
    line_errors_iter
        .map(|i| i.pretty(py, error_mode, url_prefix, hide_input))
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

impl PyLineError {
    /// Used to extract line errors from a validation error for wrap functions
    fn into_val_line_error(self, py: Python<'_>) -> ValLineError<'_> {
        ValLineError {
            error_type: self.error_type,
            location: self.location,
            input_value: InputValue::PyAny(self.input_value.into_ref(py)),
        }
    }
}

impl TryFrom<&PyAny> for PyLineError {
    type Error = PyErr;

    fn try_from(value: &PyAny) -> PyResult<Self> {
        let dict: &PyDict = value.downcast()?;
        let py = value.py();

        let type_raw = dict
            .get_item(intern!(py, "type"))
            .ok_or_else(|| PyKeyError::new_err("type"))?;

        let error_type = if let Ok(type_str) = type_raw.downcast::<PyString>() {
            let context: Option<&PyDict> = dict.get_as(intern!(py, "ctx"))?;
            ErrorType::new(py, type_str.to_str()?, context)?
        } else if let Ok(custom_error) = type_raw.extract::<PydanticCustomError>() {
            ErrorType::new_custom_error(py, custom_error)
        } else {
            return Err(PyTypeError::new_err(
                "`type` should be a `str` or `PydanticCustomError`",
            ));
        };

        let location = Location::try_from(dict.get_item("loc"))?;

        let input_value = match dict.get_item("input") {
            Some(i) => i.into_py(py),
            None => py.None(),
        };

        Ok(Self {
            error_type,
            location,
            input_value,
        })
    }
}

impl PyLineError {
    fn get_error_url(&self, url_prefix: &str) -> String {
        format!("{url_prefix}{}", self.error_type.type_string())
    }

    pub fn as_dict(
        &self,
        py: Python,
        url_prefix: Option<&str>,
        include_context: bool,
        error_mode: &ErrorMode,
    ) -> PyResult<PyObject> {
        let dict = PyDict::new(py);
        dict.set_item("type", self.error_type.type_string())?;
        dict.set_item("loc", self.location.to_object(py))?;
        dict.set_item("msg", self.error_type.render_message(py, error_mode)?)?;
        dict.set_item("input", &self.input_value)?;
        if include_context {
            if let Some(context) = self.error_type.py_dict(py)? {
                dict.set_item("ctx", context)?;
            }
        }
        if let Some(url_prefix) = url_prefix {
            match self.error_type {
                ErrorType::CustomError { .. } => {
                    // Don't add URLs for custom errors
                }
                _ => {
                    dict.set_item("url", self.get_error_url(url_prefix))?;
                }
            }
        }
        Ok(dict.into_py(py))
    }

    fn pretty(
        &self,
        py: Python,
        error_mode: &ErrorMode,
        url_prefix: Option<&str>,
        hide_input: bool,
    ) -> Result<String, fmt::Error> {
        let mut output = String::with_capacity(200);
        write!(output, "{}", self.location)?;

        let message = match self.error_type.render_message(py, error_mode) {
            Ok(message) => message,
            Err(err) => format!("(error rendering message: {err})"),
        };
        write!(output, "  {message} [type={}", self.error_type.type_string())?;

        if !hide_input {
            let input_value = self.input_value.as_ref(py);
            let input_str = safe_repr(input_value);
            truncate_input_value!(output, &input_str);

            if let Ok(type_) = input_value.get_type().name() {
                write!(output, ", input_type={type_}")?;
            }
        }
        if let Some(url_prefix) = url_prefix {
            match self.error_type {
                ErrorType::CustomError { .. } => {
                    // Don't display URLs for custom errors
                    output.push(']');
                }
                _ => {
                    write!(
                        output,
                        "]\n    For further information visit {}",
                        self.get_error_url(url_prefix)
                    )?;
                }
            }
        } else {
            output.push(']');
        }
        Ok(output)
    }
}

pub(super) fn json_py_err(error: impl Display) -> PyErr {
    PyValueError::new_err(format!("Error serializing ValidationError to JSON: {error}"))
}

pub(super) fn py_err_json<S>(error: PyErr) -> S::Error
where
    S: Serializer,
{
    S::Error::custom(error.to_string())
}

struct ValidationErrorSerializer<'py> {
    py: Python<'py>,
    line_errors: &'py [PyLineError],
    url_prefix: Option<&'py str>,
    include_context: bool,
    extra: &'py crate::serializers::Extra<'py>,
    error_mode: &'py ErrorMode,
}

impl<'py> Serialize for ValidationErrorSerializer<'py> {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut seq = serializer.serialize_seq(Some(self.line_errors.len()))?;
        for line_error in self.line_errors {
            let line_s = PyLineErrorSerializer {
                py: self.py,
                line_error,
                url_prefix: self.url_prefix,
                include_context: self.include_context,
                extra: self.extra,
                error_mode: self.error_mode,
            };
            seq.serialize_element(&line_s)?;
        }
        seq.end()
    }
}

struct PyLineErrorSerializer<'py> {
    py: Python<'py>,
    line_error: &'py PyLineError,
    url_prefix: Option<&'py str>,
    include_context: bool,
    extra: &'py crate::serializers::Extra<'py>,
    error_mode: &'py ErrorMode,
}

impl<'py> Serialize for PyLineErrorSerializer<'py> {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let py = self.py;
        let mut size = 4;
        if self.url_prefix.is_some() {
            size += 1;
        }
        if self.include_context {
            size += 1;
        }
        let mut map = serializer.serialize_map(Some(size))?;

        map.serialize_entry("type", &self.line_error.error_type.type_string())?;

        map.serialize_entry("loc", &self.line_error.location)?;

        let msg = self
            .line_error
            .error_type
            .render_message(py, self.error_mode)
            .map_err(py_err_json::<S>)?;
        map.serialize_entry("msg", &msg)?;

        map.serialize_entry(
            "input",
            &self.extra.serialize_infer(self.line_error.input_value.as_ref(py)),
        )?;

        if self.include_context {
            if let Some(context) = self.line_error.error_type.py_dict(py).map_err(py_err_json::<S>)? {
                map.serialize_entry("ctx", &self.extra.serialize_infer(context.as_ref(py)))?;
            }
        }
        if let Some(url_prefix) = self.url_prefix {
            map.serialize_entry("url", &self.line_error.get_error_url(url_prefix))?;
        }
        map.end()
    }
}
