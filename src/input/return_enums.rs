use std::borrow::Cow;

use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict, PyFrozenSet, PyList, PySet, PyString, PyTuple};

use crate::errors::{ErrorKind, InputValue, ValError, ValLineError, ValResult};
use crate::recursion_guard::RecursionGuard;
use crate::validators::{CombinedValidator, Extra, Validator};

use super::parse_json::{JsonArray, JsonInput, JsonObject};
use super::Input;

/// Container for all the "list-like" types which can be converted to each other in lax mode.
/// This cannot be called `GenericSequence` (as it previously was) or `GenericIterable` since it's
/// members don't match python's definition of `Sequence` or `Iterable`.
#[cfg_attr(debug_assertions, derive(Debug))]
pub enum GenericListLike<'a> {
    List(&'a PyList),
    Tuple(&'a PyTuple),
    Set(&'a PySet),
    FrozenSet(&'a PyFrozenSet),
    JsonArray(&'a [JsonInput]),
}

macro_rules! derive_from {
    ($enum:ident, $key:ident, $type:ty) => {
        impl<'a> From<&'a $type> for $enum<'a> {
            fn from(s: &'a $type) -> $enum<'a> {
                Self::$key(s)
            }
        }
    };
}
derive_from!(GenericListLike, List, PyList);
derive_from!(GenericListLike, Tuple, PyTuple);
derive_from!(GenericListLike, Set, PySet);
derive_from!(GenericListLike, FrozenSet, PyFrozenSet);
derive_from!(GenericListLike, JsonArray, JsonArray);
derive_from!(GenericListLike, JsonArray, [JsonInput]);

fn validate_iter_to_vec<'a, 's>(
    py: Python<'a>,
    iter: impl Iterator<Item = &'a (impl Input<'a> + 'a)>,
    length: usize,
    validator: &'s CombinedValidator,
    extra: &Extra,
    slots: &'a [CombinedValidator],
    recursion_guard: &'s mut RecursionGuard,
) -> ValResult<'a, Vec<PyObject>> {
    let mut output: Vec<PyObject> = Vec::with_capacity(length);
    let mut errors: Vec<ValLineError> = Vec::new();
    for (index, item) in iter.enumerate() {
        match validator.validate(py, item, extra, slots, recursion_guard) {
            Ok(item) => output.push(item),
            Err(ValError::LineErrors(line_errors)) => {
                errors.extend(line_errors.into_iter().map(|err| err.with_outer_location(index.into())));
            }
            Err(err) => return Err(err),
        }
    }

    if errors.is_empty() {
        Ok(output)
    } else {
        Err(ValError::LineErrors(errors))
    }
}

impl<'a> GenericListLike<'a> {
    pub fn generic_len(&self) -> usize {
        match self {
            Self::List(v) => v.len(),
            Self::Tuple(v) => v.len(),
            Self::Set(v) => v.len(),
            Self::FrozenSet(v) => v.len(),
            Self::JsonArray(v) => v.len(),
        }
    }

    pub fn check_len<'s, 'data>(
        &'s self,
        size_range: Option<(Option<usize>, Option<usize>)>,
        input: &'data impl Input<'data>,
    ) -> ValResult<'data, Option<usize>> {
        let mut length: Option<usize> = None;
        if let Some((min_items, max_items)) = size_range {
            let input_length = self.generic_len();
            if let Some(min_length) = min_items {
                if input_length < min_length {
                    return Err(ValError::new(
                        ErrorKind::TooShort {
                            min_length,
                            input_length,
                        },
                        input,
                    ));
                }
            }
            if let Some(max_length) = max_items {
                if input_length > max_length {
                    return Err(ValError::new(
                        ErrorKind::TooLong {
                            max_length,
                            input_length,
                        },
                        input,
                    ));
                }
            }
            length = Some(input_length);
        }
        Ok(length)
    }

    pub fn validate_to_vec<'s>(
        &self,
        py: Python<'a>,
        length: Option<usize>,
        validator: &'s CombinedValidator,
        extra: &Extra,
        slots: &'a [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'a, Vec<PyObject>> {
        let length = length.unwrap_or_else(|| self.generic_len());
        match self {
            Self::List(list_like) => {
                validate_iter_to_vec(py, list_like.iter(), length, validator, extra, slots, recursion_guard)
            }
            Self::Tuple(list_like) => {
                validate_iter_to_vec(py, list_like.iter(), length, validator, extra, slots, recursion_guard)
            }
            Self::Set(list_like) => {
                validate_iter_to_vec(py, list_like.iter(), length, validator, extra, slots, recursion_guard)
            }
            Self::FrozenSet(list_like) => {
                validate_iter_to_vec(py, list_like.iter(), length, validator, extra, slots, recursion_guard)
            }
            Self::JsonArray(list_like) => {
                validate_iter_to_vec(py, list_like.iter(), length, validator, extra, slots, recursion_guard)
            }
        }
    }

    pub fn to_vec(&self, py: Python) -> Vec<PyObject> {
        match self {
            Self::List(list_like) => list_like.iter().map(|i| i.to_object(py)).collect(),
            Self::Tuple(list_like) => list_like.iter().map(|i| i.to_object(py)).collect(),
            Self::Set(list_like) => list_like.iter().map(|i| i.to_object(py)).collect(),
            Self::FrozenSet(list_like) => list_like.iter().map(|i| i.to_object(py)).collect(),
            Self::JsonArray(list_like) => list_like.iter().map(|i| i.to_object(py)).collect(),
        }
    }
}

#[cfg_attr(debug_assertions, derive(Debug))]
pub enum GenericMapping<'a> {
    PyDict(&'a PyDict),
    PyGetAttr(&'a PyAny),
    JsonObject(&'a JsonObject),
}

derive_from!(GenericMapping, PyDict, PyDict);
derive_from!(GenericMapping, PyGetAttr, PyAny);
derive_from!(GenericMapping, JsonObject, JsonObject);

#[cfg_attr(debug_assertions, derive(Debug))]
pub struct PyArgs<'a> {
    pub args: Option<&'a PyTuple>,
    pub kwargs: Option<&'a PyDict>,
}

impl<'a> PyArgs<'a> {
    pub fn new(args: Option<&'a PyTuple>, kwargs: Option<&'a PyDict>) -> Self {
        Self { args, kwargs }
    }
}

#[cfg_attr(debug_assertions, derive(Debug))]
pub struct JsonArgs<'a> {
    pub args: Option<&'a [JsonInput]>,
    pub kwargs: Option<&'a JsonObject>,
}

impl<'a> JsonArgs<'a> {
    pub fn new(args: Option<&'a [JsonInput]>, kwargs: Option<&'a JsonObject>) -> Self {
        Self { args, kwargs }
    }
}

#[cfg_attr(debug_assertions, derive(Debug))]
pub enum GenericArguments<'a> {
    Py(PyArgs<'a>),
    Json(JsonArgs<'a>),
}

impl<'a> From<PyArgs<'a>> for GenericArguments<'a> {
    fn from(s: PyArgs<'a>) -> GenericArguments<'a> {
        Self::Py(s)
    }
}

impl<'a> From<JsonArgs<'a>> for GenericArguments<'a> {
    fn from(s: JsonArgs<'a>) -> GenericArguments<'a> {
        Self::Json(s)
    }
}

#[cfg_attr(debug_assertions, derive(Debug))]
pub enum EitherString<'a> {
    Cow(Cow<'a, str>),
    Py(&'a PyString),
}

impl<'a> EitherString<'a> {
    pub fn as_cow(&self) -> ValResult<'a, Cow<str>> {
        match self {
            Self::Cow(data) => Ok(data.clone()),
            Self::Py(py_str) => Ok(Cow::Borrowed(py_string_str(py_str)?)),
        }
    }

    pub fn as_py_string(&'a self, py: Python<'a>) -> &'a PyString {
        match self {
            Self::Cow(cow) => PyString::new(py, cow),
            Self::Py(py_string) => py_string,
        }
    }
}

impl<'a> From<&'a str> for EitherString<'a> {
    fn from(data: &'a str) -> Self {
        Self::Cow(Cow::Borrowed(data))
    }
}

impl<'a> From<&'a PyString> for EitherString<'a> {
    fn from(date: &'a PyString) -> Self {
        Self::Py(date)
    }
}

impl<'a> IntoPy<PyObject> for EitherString<'a> {
    fn into_py(self, py: Python<'_>) -> PyObject {
        self.as_py_string(py).into_py(py)
    }
}

pub fn py_string_str(py_str: &PyString) -> ValResult<&str> {
    py_str
        .to_str()
        .map_err(|_| ValError::new_custom_input(ErrorKind::StrUnicode, InputValue::PyAny(py_str as &PyAny)))
}

#[cfg_attr(debug_assertions, derive(Debug))]
pub enum EitherBytes<'a> {
    Cow(Cow<'a, [u8]>),
    Py(&'a PyBytes),
}

impl<'a> From<Vec<u8>> for EitherBytes<'a> {
    fn from(date: Vec<u8>) -> Self {
        Self::Cow(Cow::Owned(date))
    }
}

impl<'a> From<&'a [u8]> for EitherBytes<'a> {
    fn from(date: &'a [u8]) -> Self {
        Self::Cow(Cow::Borrowed(date))
    }
}

impl<'a> From<&'a PyBytes> for EitherBytes<'a> {
    fn from(date: &'a PyBytes) -> Self {
        Self::Py(date)
    }
}

impl<'a> EitherBytes<'a> {
    pub fn len(&'a self) -> PyResult<usize> {
        match self {
            EitherBytes::Cow(bytes) => Ok(bytes.len()),
            EitherBytes::Py(py_bytes) => py_bytes.len(),
        }
    }
}

impl<'a> IntoPy<PyObject> for EitherBytes<'a> {
    fn into_py(self, py: Python<'_>) -> PyObject {
        match self {
            EitherBytes::Cow(bytes) => PyBytes::new(py, &bytes).into_py(py),
            EitherBytes::Py(py_bytes) => py_bytes.into_py(py),
        }
    }
}
