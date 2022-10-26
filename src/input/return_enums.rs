use std::borrow::Cow;

use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict, PyFrozenSet, PyIterator, PyList, PySet, PyString, PyTuple};

use crate::errors::{py_err_string, ErrorType, InputValue, ValError, ValLineError, ValResult};
use crate::recursion_guard::RecursionGuard;
use crate::validators::{CombinedValidator, Extra, Validator};

use super::parse_json::{JsonArray, JsonInput, JsonObject};
use super::Input;

/// Container for all the collections (sized iterable containers) types, which
/// can mostly be converted to each other in lax mode.
/// This mostly matches python's definition of `Collection`.
#[cfg_attr(debug_assertions, derive(Debug))]
pub enum GenericCollection<'a> {
    List(&'a PyList),
    Tuple(&'a PyTuple),
    Set(&'a PySet),
    FrozenSet(&'a PyFrozenSet),
    PyAny(&'a PyAny),
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
derive_from!(GenericCollection, List, PyList);
derive_from!(GenericCollection, Tuple, PyTuple);
derive_from!(GenericCollection, Set, PySet);
derive_from!(GenericCollection, FrozenSet, PyFrozenSet);
derive_from!(GenericCollection, PyAny, PyAny);
derive_from!(GenericCollection, JsonArray, JsonArray);
derive_from!(GenericCollection, JsonArray, [JsonInput]);

fn validate_iter_to_vec<'a, 's>(
    py: Python<'a>,
    iter: impl Iterator<Item = &'a (impl Input<'a> + 'a)>,
    capacity: usize,
    validator: &'s CombinedValidator,
    extra: &Extra,
    slots: &'a [CombinedValidator],
    recursion_guard: &'s mut RecursionGuard,
) -> ValResult<'a, Vec<PyObject>> {
    let mut output: Vec<PyObject> = Vec::with_capacity(capacity);
    let mut errors: Vec<ValLineError> = Vec::new();
    for (index, item) in iter.enumerate() {
        match validator.validate(py, item, extra, slots, recursion_guard) {
            Ok(item) => output.push(item),
            Err(ValError::LineErrors(line_errors)) => {
                errors.extend(line_errors.into_iter().map(|err| err.with_outer_location(index.into())));
            }
            Err(ValError::Omit) => (),
            Err(err) => return Err(err),
        }
    }

    if errors.is_empty() {
        Ok(output)
    } else {
        Err(ValError::LineErrors(errors))
    }
}

macro_rules! any_next_error {
    ($py:expr, $err:ident, $input:ident, $index:ident) => {
        ValError::new_with_loc(
            ErrorType::IterationError {
                error: py_err_string($py, $err),
            },
            $input,
            $index,
        )
    };
}

macro_rules! generator_too_long {
    ($input:ident, $index:ident, $max_length:expr, $field_type:ident) => {
        if let Some(max_length) = $max_length {
            if $index > max_length {
                return Err(ValError::new(
                    ErrorType::TooLong {
                        field_type: $field_type.to_string(),
                        max_length,
                        actual_length: $index,
                    },
                    $input,
                ));
            }
        }
    };
}

// pretty arbitrary default capacity when creating vecs from iteration
static DEFAULT_CAPACITY: usize = 10;

impl<'a> GenericCollection<'a> {
    pub fn generic_len(&self) -> PyResult<usize> {
        match self {
            Self::List(v) => Ok(v.len()),
            Self::Tuple(v) => Ok(v.len()),
            Self::Set(v) => Ok(v.len()),
            Self::FrozenSet(v) => Ok(v.len()),
            Self::PyAny(v) => v.len(),
            Self::JsonArray(v) => Ok(v.len()),
        }
    }

    #[allow(clippy::too_many_arguments)]
    pub fn validate_to_vec<'s>(
        &'s self,
        py: Python<'a>,
        input: &'a impl Input<'a>,
        max_length: Option<usize>,
        field_type: &'static str,
        generator_max_length: Option<usize>,
        validator: &'s CombinedValidator,
        extra: &Extra,
        slots: &'a [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'a, Vec<PyObject>> {
        let capacity = self
            .generic_len()
            .unwrap_or_else(|_| max_length.unwrap_or(DEFAULT_CAPACITY));
        match self {
            Self::List(collection) => validate_iter_to_vec(
                py,
                collection.iter(),
                capacity,
                validator,
                extra,
                slots,
                recursion_guard,
            ),
            Self::Tuple(collection) => validate_iter_to_vec(
                py,
                collection.iter(),
                capacity,
                validator,
                extra,
                slots,
                recursion_guard,
            ),
            Self::Set(collection) => validate_iter_to_vec(
                py,
                collection.iter(),
                capacity,
                validator,
                extra,
                slots,
                recursion_guard,
            ),
            Self::FrozenSet(collection) => validate_iter_to_vec(
                py,
                collection.iter(),
                capacity,
                validator,
                extra,
                slots,
                recursion_guard,
            ),
            Self::PyAny(collection) => {
                let iter = collection.iter()?;
                let mut output: Vec<PyObject> = Vec::with_capacity(capacity);
                let mut errors: Vec<ValLineError> = Vec::new();
                for (index, item_result) in iter.enumerate() {
                    let item = item_result.map_err(|e| any_next_error!(collection.py(), e, input, index))?;
                    match validator.validate(py, item, extra, slots, recursion_guard) {
                        Ok(item) => {
                            generator_too_long!(input, index, generator_max_length, field_type);
                            output.push(item);
                        }
                        Err(ValError::LineErrors(line_errors)) => {
                            errors.extend(line_errors.into_iter().map(|err| err.with_outer_location(index.into())));
                        }
                        Err(ValError::Omit) => (),
                        Err(err) => return Err(err),
                    }
                }
                // TODO do too small check here

                if errors.is_empty() {
                    Ok(output)
                } else {
                    Err(ValError::LineErrors(errors))
                }
            }
            Self::JsonArray(collection) => validate_iter_to_vec(
                py,
                collection.iter(),
                capacity,
                validator,
                extra,
                slots,
                recursion_guard,
            ),
        }
    }

    pub fn to_vec<'s>(
        &'s self,
        py: Python<'a>,
        input: &'a impl Input<'a>,
        field_type: &'static str,
        generator_max_length: Option<usize>,
    ) -> ValResult<'a, Vec<PyObject>> {
        match self {
            Self::List(collection) => Ok(collection.iter().map(|i| i.to_object(py)).collect()),
            Self::Tuple(collection) => Ok(collection.iter().map(|i| i.to_object(py)).collect()),
            Self::Set(collection) => Ok(collection.iter().map(|i| i.to_object(py)).collect()),
            Self::FrozenSet(collection) => Ok(collection.iter().map(|i| i.to_object(py)).collect()),
            Self::PyAny(collection) => collection
                .iter()?
                .enumerate()
                .map(|(index, item_result)| {
                    generator_too_long!(input, index, generator_max_length, field_type);
                    let item = item_result.map_err(|e| any_next_error!(collection.py(), e, input, index))?;
                    Ok(item.to_object(py))
                })
                .collect(),
            Self::JsonArray(collection) => Ok(collection.iter().map(|i| i.to_object(py)).collect()),
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

#[derive(Debug, Clone)]
pub enum GenericIterator {
    PyIterator(GenericPyIterator),
    JsonArray(GenericJsonIterator),
}

impl From<JsonArray> for GenericIterator {
    fn from(array: JsonArray) -> Self {
        let length = array.len();
        let json_iter = GenericJsonIterator {
            array,
            length,
            index: 0,
        };
        Self::JsonArray(json_iter)
    }
}

impl From<&PyAny> for GenericIterator {
    fn from(obj: &PyAny) -> Self {
        let py_iter = GenericPyIterator {
            obj: obj.to_object(obj.py()),
            iter: obj.iter().unwrap().into_py(obj.py()),
            index: 0,
        };
        Self::PyIterator(py_iter)
    }
}

#[derive(Debug, Clone)]
pub struct GenericPyIterator {
    obj: PyObject,
    iter: Py<PyIterator>,
    index: usize,
}

impl GenericPyIterator {
    pub fn next<'a>(&'a mut self, py: Python<'a>) -> PyResult<Option<(&'a PyAny, usize)>> {
        match self.iter.as_ref(py).next() {
            Some(Ok(next)) => {
                let a = (next, self.index);
                self.index += 1;
                Ok(Some(a))
            }
            Some(Err(err)) => Err(err),
            None => Ok(None),
        }
    }

    pub fn input<'a>(&'a self, py: Python<'a>) -> &'a PyAny {
        self.obj.as_ref(py)
    }

    pub fn index(&self) -> usize {
        self.index
    }
}

#[derive(Debug, Clone)]
pub struct GenericJsonIterator {
    array: JsonArray,
    length: usize,
    index: usize,
}

impl GenericJsonIterator {
    pub fn next(&mut self, _py: Python) -> PyResult<Option<(&JsonInput, usize)>> {
        if self.index < self.length {
            let next = unsafe { self.array.get_unchecked(self.index) };
            let a = (next, self.index);
            self.index += 1;
            Ok(Some(a))
        } else {
            Ok(None)
        }
    }

    pub fn input<'a>(&'a self, py: Python<'a>) -> &'a PyAny {
        let input = JsonInput::Array(self.array.clone());
        input.to_object(py).into_ref(py)
    }

    pub fn index(&self) -> usize {
        self.index
    }
}

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
        .map_err(|_| ValError::new_custom_input(ErrorType::StringUnicode, InputValue::PyAny(py_str as &PyAny)))
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
