use std::borrow::Cow;
use std::cmp::Ordering;
use std::ops::Rem;
use std::slice::Iter as SliceIter;
use std::str::FromStr;

use num_bigint::BigInt;

use pyo3::exceptions::PyTypeError;
use pyo3::prelude::*;
use pyo3::types::iter::PyDictIterator;
use pyo3::types::{
    PyByteArray, PyBytes, PyDict, PyFloat, PyFrozenSet, PyIterator, PyList, PyMapping, PySequence, PySet, PyString,
    PyTuple,
};
use pyo3::{ffi, intern, AsPyPointer, PyNativeType};

#[cfg(not(PyPy))]
use pyo3::types::PyFunction;
#[cfg(not(PyPy))]
use pyo3::PyTypeInfo;
use serde::{ser::Error, Serialize, Serializer};

use crate::errors::{py_err_string, ErrorType, ErrorTypeDefaults, InputValue, ValError, ValLineError, ValResult};
use crate::tools::py_err;
use crate::validators::{CombinedValidator, ValidationState, Validator};

use super::parse_json::{JsonArray, JsonInput, JsonObject};
use super::{py_error_on_minusone, Input};

/// Container for all the collections (sized iterable containers) types, which
/// can mostly be converted to each other in lax mode.
/// This mostly matches python's definition of `Collection`.
#[cfg_attr(debug_assertions, derive(Debug))]
pub enum GenericIterable<'a> {
    List(&'a PyList),
    Tuple(&'a PyTuple),
    Set(&'a PySet),
    FrozenSet(&'a PyFrozenSet),
    Dict(&'a PyDict),
    // Treat dict values / keys / items as generic iterators
    // since PyPy doesn't export the concrete types
    DictKeys(&'a PyIterator),
    DictValues(&'a PyIterator),
    DictItems(&'a PyIterator),
    Mapping(&'a PyMapping),
    PyString(&'a PyString),
    Bytes(&'a PyBytes),
    PyByteArray(&'a PyByteArray),
    Sequence(&'a PySequence),
    Iterator(&'a PyIterator),
    JsonArray(&'a [JsonInput]),
    JsonObject(&'a JsonObject),
    JsonString(&'a String),
}

impl<'a, 'py: 'a> GenericIterable<'a> {
    pub fn as_sequence_iterator(
        &self,
        py: Python<'py>,
    ) -> PyResult<Box<dyn Iterator<Item = PyResult<&'a PyAny>> + 'a>> {
        match self {
            GenericIterable::List(iter) => Ok(Box::new(iter.iter().map(Ok))),
            GenericIterable::Tuple(iter) => Ok(Box::new(iter.iter().map(Ok))),
            GenericIterable::Set(iter) => Ok(Box::new(iter.iter().map(Ok))),
            GenericIterable::FrozenSet(iter) => Ok(Box::new(iter.iter().map(Ok))),
            // Note that this iterates over only the keys, just like doing iter({}) in Python
            GenericIterable::Dict(iter) => Ok(Box::new(iter.iter().map(|(k, _)| Ok(k)))),
            GenericIterable::DictKeys(iter) => Ok(Box::new(iter.iter()?)),
            GenericIterable::DictValues(iter) => Ok(Box::new(iter.iter()?)),
            GenericIterable::DictItems(iter) => Ok(Box::new(iter.iter()?)),
            // Note that this iterates over only the keys, just like doing iter({}) in Python
            GenericIterable::Mapping(iter) => Ok(Box::new(iter.keys()?.iter()?)),
            GenericIterable::PyString(iter) => Ok(Box::new(iter.iter()?)),
            GenericIterable::Bytes(iter) => Ok(Box::new(iter.iter()?)),
            GenericIterable::PyByteArray(iter) => Ok(Box::new(iter.iter()?)),
            GenericIterable::Sequence(iter) => Ok(Box::new(iter.iter()?)),
            GenericIterable::Iterator(iter) => Ok(Box::new(iter.iter()?)),
            GenericIterable::JsonArray(iter) => Ok(Box::new(iter.iter().map(move |v| {
                let v = v.to_object(py);
                Ok(v.into_ref(py))
            }))),
            // Note that this iterates over only the keys, just like doing iter({}) in Python, just for consistency
            GenericIterable::JsonObject(iter) => Ok(Box::new(
                iter.iter().map(move |(k, _)| Ok(k.to_object(py).into_ref(py))),
            )),
            GenericIterable::JsonString(s) => Ok(Box::new(PyString::new(py, s).iter()?)),
        }
    }
}

macro_rules! derive_from {
    ($enum:ident, $key:ident, $type:ty $(, $extra_types:ident )*) => {
        impl<'a> From<&'a $type> for $enum<'a> {
            fn from(s: &'a $type) -> $enum<'a> {
                Self::$key(s $(, $extra_types )*)
            }
        }
    };
}

#[derive(Debug)]
struct MaxLengthCheck<'a, INPUT> {
    current_length: usize,
    max_length: Option<usize>,
    field_type: &'a str,
    input: &'a INPUT,
    known_input_length: usize,
}

impl<'a, INPUT: Input<'a>> MaxLengthCheck<'a, INPUT> {
    fn new(max_length: Option<usize>, field_type: &'a str, input: &'a INPUT, known_input_length: usize) -> Self {
        Self {
            current_length: 0,
            max_length,
            field_type,
            input,
            known_input_length,
        }
    }

    fn incr(&mut self) -> ValResult<'a, ()> {
        match self.max_length {
            Some(max_length) => {
                self.current_length += 1;
                if self.current_length > max_length {
                    let biggest_length = if self.known_input_length > self.current_length {
                        self.known_input_length
                    } else {
                        self.current_length
                    };
                    return Err(ValError::new(
                        ErrorType::TooLong {
                            field_type: self.field_type.to_string(),
                            max_length,
                            actual_length: biggest_length,
                            context: None,
                        },
                        self.input,
                    ));
                }
            }
            None => {
                self.current_length += 1;
                if self.current_length > self.known_input_length {
                    return Err(ValError::new(
                        ErrorType::TooLong {
                            field_type: self.field_type.to_string(),
                            max_length: self.known_input_length,
                            actual_length: self.current_length,
                            context: None,
                        },
                        self.input,
                    ));
                }
            }
        }
        Ok(())
    }
}

macro_rules! any_next_error {
    ($py:expr, $err:ident, $input:expr, $index:ident) => {
        ValError::new_with_loc(
            ErrorType::IterationError {
                error: py_err_string($py, $err),
                context: None,
            },
            $input,
            $index,
        )
    };
}

#[allow(clippy::too_many_arguments)]
fn validate_iter_to_vec<'a, 's>(
    py: Python<'a>,
    iter: impl Iterator<Item = PyResult<&'a (impl Input<'a> + 'a)>>,
    capacity: usize,
    mut max_length_check: MaxLengthCheck<'a, impl Input<'a>>,
    validator: &'s CombinedValidator,
    state: &mut ValidationState,
) -> ValResult<'a, Vec<PyObject>> {
    let mut output: Vec<PyObject> = Vec::with_capacity(capacity);
    let mut errors: Vec<ValLineError> = Vec::new();
    for (index, item_result) in iter.enumerate() {
        let item = item_result.map_err(|e| any_next_error!(py, e, max_length_check.input, index))?;
        match validator.validate(py, item, state) {
            Ok(item) => {
                max_length_check.incr()?;
                output.push(item);
            }
            Err(ValError::LineErrors(line_errors)) => {
                max_length_check.incr()?;
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

pub trait BuildSet {
    fn build_add(&self, item: PyObject) -> PyResult<()>;

    fn build_len(&self) -> usize;
}

impl BuildSet for &PySet {
    fn build_add(&self, item: PyObject) -> PyResult<()> {
        self.add(item)
    }

    fn build_len(&self) -> usize {
        self.len()
    }
}

impl BuildSet for &PyFrozenSet {
    fn build_add(&self, item: PyObject) -> PyResult<()> {
        unsafe {
            py_error_on_minusone(
                self.py(),
                ffi::PySet_Add(self.as_ptr(), item.to_object(self.py()).as_ptr()),
            )
        }
    }

    fn build_len(&self) -> usize {
        self.len()
    }
}

#[allow(clippy::too_many_arguments)]
fn validate_iter_to_set<'a, 's>(
    py: Python<'a>,
    set: impl BuildSet,
    iter: impl Iterator<Item = PyResult<&'a (impl Input<'a> + 'a)>>,
    input: &'a (impl Input<'a> + 'a),
    field_type: &'static str,
    max_length: Option<usize>,
    validator: &'s CombinedValidator,
    state: &mut ValidationState,
) -> ValResult<'a, ()> {
    let mut errors: Vec<ValLineError> = Vec::new();
    for (index, item_result) in iter.enumerate() {
        let item = item_result.map_err(|e| any_next_error!(py, e, input, index))?;
        match validator.validate(py, item, state) {
            Ok(item) => {
                set.build_add(item)?;
                if let Some(max_length) = max_length {
                    let actual_length = set.build_len();
                    if actual_length > max_length {
                        return Err(ValError::new(
                            ErrorType::TooLong {
                                field_type: field_type.to_string(),
                                max_length,
                                actual_length,
                                context: None,
                            },
                            input,
                        ));
                    }
                }
            }
            Err(ValError::LineErrors(line_errors)) => {
                errors.extend(line_errors.into_iter().map(|err| err.with_outer_location(index.into())));
            }
            Err(ValError::Omit) => (),
            Err(err) => return Err(err),
        }
    }

    if errors.is_empty() {
        Ok(())
    } else {
        Err(ValError::LineErrors(errors))
    }
}

fn no_validator_iter_to_vec<'a, 's>(
    py: Python<'a>,
    input: &'a (impl Input<'a> + 'a),
    iter: impl Iterator<Item = PyResult<&'a (impl Input<'a> + 'a)>>,
    mut max_length_check: MaxLengthCheck<'a, impl Input<'a>>,
) -> ValResult<'a, Vec<PyObject>> {
    iter.enumerate()
        .map(|(index, result)| {
            let v = result.map_err(|e| any_next_error!(py, e, input, index))?;
            max_length_check.incr()?;
            Ok(v.to_object(py))
        })
        .collect()
}

// pretty arbitrary default capacity when creating vecs from iteration
static DEFAULT_CAPACITY: usize = 10;

impl<'a> GenericIterable<'a> {
    pub fn generic_len(&self) -> Option<usize> {
        match &self {
            GenericIterable::List(iter) => Some(iter.len()),
            GenericIterable::Tuple(iter) => Some(iter.len()),
            GenericIterable::Set(iter) => Some(iter.len()),
            GenericIterable::FrozenSet(iter) => Some(iter.len()),
            GenericIterable::Dict(iter) => Some(iter.len()),
            GenericIterable::DictKeys(iter) => iter.len().ok(),
            GenericIterable::DictValues(iter) => iter.len().ok(),
            GenericIterable::DictItems(iter) => iter.len().ok(),
            GenericIterable::Mapping(iter) => iter.len().ok(),
            GenericIterable::PyString(iter) => iter.len().ok(),
            GenericIterable::Bytes(iter) => iter.len().ok(),
            GenericIterable::PyByteArray(iter) => Some(iter.len()),
            GenericIterable::Sequence(iter) => iter.len().ok(),
            GenericIterable::Iterator(iter) => iter.len().ok(),
            GenericIterable::JsonArray(iter) => Some(iter.len()),
            GenericIterable::JsonObject(iter) => Some(iter.len()),
            GenericIterable::JsonString(iter) => Some(iter.len()),
        }
    }

    #[allow(clippy::too_many_arguments)]
    pub fn validate_to_vec<'s>(
        &'s self,
        py: Python<'a>,
        input: &'a impl Input<'a>,
        max_length: Option<usize>,
        field_type: &'static str,
        validator: &'s CombinedValidator,
        state: &mut ValidationState,
    ) -> ValResult<'a, Vec<PyObject>> {
        let capacity = self
            .generic_len()
            .unwrap_or_else(|| max_length.unwrap_or(DEFAULT_CAPACITY));
        let max_length_check = MaxLengthCheck::new(max_length, field_type, input, capacity);

        macro_rules! validate {
            ($iter:expr) => {
                validate_iter_to_vec(py, $iter, capacity, max_length_check, validator, state)
            };
        }

        match self {
            GenericIterable::List(collection) => validate!(collection.iter().map(Ok)),
            GenericIterable::Tuple(collection) => validate!(collection.iter().map(Ok)),
            GenericIterable::Set(collection) => validate!(collection.iter().map(Ok)),
            GenericIterable::FrozenSet(collection) => validate!(collection.iter().map(Ok)),
            GenericIterable::Sequence(collection) => validate!(collection.iter()?),
            GenericIterable::Iterator(collection) => validate!(collection.iter()?),
            GenericIterable::JsonArray(collection) => validate!(collection.iter().map(Ok)),
            other => validate!(other.as_sequence_iterator(py)?),
        }
    }

    #[allow(clippy::too_many_arguments)]
    pub fn validate_to_set<'s>(
        &'s self,
        py: Python<'a>,
        set: impl BuildSet,
        input: &'a impl Input<'a>,
        max_length: Option<usize>,
        field_type: &'static str,
        validator: &'s CombinedValidator,
        state: &mut ValidationState,
    ) -> ValResult<'a, ()> {
        macro_rules! validate_set {
            ($iter:expr) => {
                validate_iter_to_set(py, set, $iter, input, field_type, max_length, validator, state)
            };
        }

        match self {
            GenericIterable::List(collection) => validate_set!(collection.iter().map(Ok)),
            GenericIterable::Tuple(collection) => validate_set!(collection.iter().map(Ok)),
            GenericIterable::Set(collection) => validate_set!(collection.iter().map(Ok)),
            GenericIterable::FrozenSet(collection) => validate_set!(collection.iter().map(Ok)),
            GenericIterable::Sequence(collection) => validate_set!(collection.iter()?),
            GenericIterable::Iterator(collection) => validate_set!(collection.iter()?),
            GenericIterable::JsonArray(collection) => validate_set!(collection.iter().map(Ok)),
            other => validate_set!(other.as_sequence_iterator(py)?),
        }
    }

    pub fn to_vec<'s>(
        &'s self,
        py: Python<'a>,
        input: &'a impl Input<'a>,
        field_type: &'static str,
        max_length: Option<usize>,
    ) -> ValResult<'a, Vec<PyObject>> {
        let capacity = self
            .generic_len()
            .unwrap_or_else(|| max_length.unwrap_or(DEFAULT_CAPACITY));
        let max_length_check = MaxLengthCheck::new(max_length, field_type, input, capacity);

        match self {
            GenericIterable::List(collection) => {
                no_validator_iter_to_vec(py, input, collection.iter().map(Ok), max_length_check)
            }
            GenericIterable::Tuple(collection) => {
                no_validator_iter_to_vec(py, input, collection.iter().map(Ok), max_length_check)
            }
            GenericIterable::Set(collection) => {
                no_validator_iter_to_vec(py, input, collection.iter().map(Ok), max_length_check)
            }
            GenericIterable::FrozenSet(collection) => {
                no_validator_iter_to_vec(py, input, collection.iter().map(Ok), max_length_check)
            }
            GenericIterable::Sequence(collection) => {
                no_validator_iter_to_vec(py, input, collection.iter()?, max_length_check)
            }
            GenericIterable::Iterator(collection) => {
                no_validator_iter_to_vec(py, input, collection.iter()?, max_length_check)
            }
            GenericIterable::JsonArray(collection) => {
                no_validator_iter_to_vec(py, input, collection.iter().map(Ok), max_length_check)
            }
            other => no_validator_iter_to_vec(py, input, other.as_sequence_iterator(py)?, max_length_check),
        }
    }
}

#[cfg_attr(debug_assertions, derive(Debug))]
pub enum GenericMapping<'a> {
    PyDict(&'a PyDict),
    PyMapping(&'a PyMapping),
    PyGetAttr(&'a PyAny, Option<&'a PyDict>),
    JsonObject(&'a JsonObject),
}

derive_from!(GenericMapping, PyDict, PyDict);
derive_from!(GenericMapping, PyMapping, PyMapping);
derive_from!(GenericMapping, PyGetAttr, PyAny, None);
derive_from!(GenericMapping, JsonObject, JsonObject);

pub struct DictGenericIterator<'py> {
    dict_iter: PyDictIterator<'py>,
}

impl<'py> DictGenericIterator<'py> {
    pub fn new(dict: &'py PyDict) -> ValResult<'py, Self> {
        Ok(Self { dict_iter: dict.iter() })
    }
}

impl<'py> Iterator for DictGenericIterator<'py> {
    type Item = ValResult<'py, (&'py PyAny, &'py PyAny)>;

    fn next(&mut self) -> Option<Self::Item> {
        self.dict_iter.next().map(Ok)
    }
    // size_hint is omitted as it isn't needed
}

pub struct MappingGenericIterator<'py> {
    input: &'py PyAny,
    iter: &'py PyIterator,
}

fn mapping_err<'py>(err: PyErr, py: Python<'py>, input: &'py impl Input<'py>) -> ValError<'py> {
    ValError::new(
        ErrorType::MappingType {
            error: py_err_string(py, err).into(),
            context: None,
        },
        input,
    )
}

impl<'py> MappingGenericIterator<'py> {
    pub fn new(mapping: &'py PyMapping) -> ValResult<'py, Self> {
        let py = mapping.py();
        let input: &PyAny = mapping;
        let iter = mapping
            .items()
            .map_err(|e| mapping_err(e, py, input))?
            .iter()
            .map_err(|e| mapping_err(e, py, input))?;
        Ok(Self { input, iter })
    }
}

const MAPPING_TUPLE_ERROR: &str = "Mapping items must be tuples of (key, value) pairs";

impl<'py> Iterator for MappingGenericIterator<'py> {
    type Item = ValResult<'py, (&'py PyAny, &'py PyAny)>;

    fn next(&mut self) -> Option<Self::Item> {
        let item = match self.iter.next() {
            Some(Err(e)) => return Some(Err(mapping_err(e, self.iter.py(), self.input))),
            Some(Ok(item)) => item,
            None => return None,
        };
        let tuple: &PyTuple = match item.downcast() {
            Ok(tuple) => tuple,
            Err(_) => {
                return Some(Err(ValError::new(
                    ErrorType::MappingType {
                        error: MAPPING_TUPLE_ERROR.into(),
                        context: None,
                    },
                    self.input,
                )))
            }
        };
        if tuple.len() != 2 {
            return Some(Err(ValError::new(
                ErrorType::MappingType {
                    error: MAPPING_TUPLE_ERROR.into(),
                    context: None,
                },
                self.input,
            )));
        };
        #[cfg(PyPy)]
        let key = tuple.get_item(0).unwrap();
        #[cfg(PyPy)]
        let value = tuple.get_item(1).unwrap();
        #[cfg(not(PyPy))]
        let key = unsafe { tuple.get_item_unchecked(0) };
        #[cfg(not(PyPy))]
        let value = unsafe { tuple.get_item_unchecked(1) };
        Some(Ok((key, value)))
    }
    // size_hint is omitted as it isn't needed
}

pub struct AttributesGenericIterator<'py> {
    object: &'py PyAny,
    attributes: &'py PyList,
    index: usize,
}

impl<'py> AttributesGenericIterator<'py> {
    pub fn new(py_any: &'py PyAny) -> ValResult<'py, Self> {
        Ok(Self {
            object: py_any,
            attributes: py_any.dir(),
            index: 0,
        })
    }
}

impl<'py> Iterator for AttributesGenericIterator<'py> {
    type Item = ValResult<'py, (&'py PyAny, &'py PyAny)>;

    fn next(&mut self) -> Option<Self::Item> {
        // loop until we find an attribute who's name does not start with underscore,
        // or we get to the end of the list of attributes
        while self.index < self.attributes.len() {
            #[cfg(PyPy)]
            let name: &PyAny = self.attributes.get_item(self.index).unwrap();
            #[cfg(not(PyPy))]
            let name: &PyAny = unsafe { self.attributes.get_item_unchecked(self.index) };
            self.index += 1;
            // from benchmarks this is 14x faster than using the python `startswith` method
            let name_cow = match name.downcast::<PyString>() {
                Ok(name) => name.to_string_lossy(),
                Err(e) => return Some(Err(e.into())),
            };
            if !name_cow.as_ref().starts_with('_') {
                // getattr is most likely to fail due to an exception in a @property, skip
                if let Ok(attr) = self.object.getattr(name_cow.as_ref()) {
                    // we don't want bound methods to be included, is there a better way to check?
                    // ref https://stackoverflow.com/a/18955425/949890
                    let is_bound = matches!(attr.hasattr(intern!(attr.py(), "__self__")), Ok(true));
                    // the PyFunction::is_type_of(attr) catches `staticmethod`, but also any other function,
                    // I think that's better than including static methods in the yielded attributes,
                    // if someone really wants fields, they can use an explicit field, or a function to modify input
                    #[cfg(not(PyPy))]
                    if !is_bound && !PyFunction::is_type_of(attr) {
                        return Some(Ok((name, attr)));
                    }
                    // MASSIVE HACK! PyFunction doesn't exist for PyPy,
                    // is_instance_of::<PyFunction> crashes with a null pointer, hence this hack, see
                    // https://github.com/pydantic/pydantic-core/pull/161#discussion_r917257635
                    #[cfg(PyPy)]
                    if !is_bound && attr.get_type().to_string() != "<class 'function'>" {
                        return Some(Ok((name, attr)));
                    }
                }
            }
        }
        None
    }
    // size_hint is omitted as it isn't needed
}

pub struct JsonObjectGenericIterator<'py> {
    object_iter: SliceIter<'py, (String, JsonInput)>,
}

impl<'py> JsonObjectGenericIterator<'py> {
    pub fn new(json_object: &'py JsonObject) -> ValResult<'py, Self> {
        Ok(Self {
            object_iter: json_object.iter(),
        })
    }
}

impl<'py> Iterator for JsonObjectGenericIterator<'py> {
    type Item = ValResult<'py, (&'py String, &'py JsonInput)>;

    fn next(&mut self) -> Option<Self::Item> {
        self.object_iter.next().map(|(key, value)| Ok((key, value)))
    }
    // size_hint is omitted as it isn't needed
}

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
        .map_err(|_| ValError::new_custom_input(ErrorTypeDefaults::StringUnicode, InputValue::PyAny(py_str as &PyAny)))
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
    pub fn as_slice(&'a self) -> &[u8] {
        match self {
            EitherBytes::Cow(bytes) => bytes,
            EitherBytes::Py(py_bytes) => py_bytes.as_bytes(),
        }
    }

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

#[cfg_attr(debug_assertions, derive(Debug))]
pub enum EitherInt<'a> {
    I64(i64),
    U64(u64),
    BigInt(BigInt),
    Py(&'a PyAny),
}

impl<'a> EitherInt<'a> {
    pub fn upcast(py_any: &'a PyAny) -> ValResult<Self> {
        // Safety: we know that py_any is a python int
        if let Ok(int_64) = py_any.extract::<i64>() {
            Ok(Self::I64(int_64))
        } else {
            let big_int: BigInt = py_any.extract()?;
            Ok(Self::BigInt(big_int))
        }
    }
    pub fn into_i64(self, py: Python<'a>) -> ValResult<'a, i64> {
        match self {
            EitherInt::I64(i) => Ok(i),
            EitherInt::U64(u) => match i64::try_from(u) {
                Ok(u) => Ok(u),
                Err(_) => Err(ValError::new(
                    ErrorTypeDefaults::IntParsingSize,
                    u.into_py(py).into_ref(py),
                )),
            },
            EitherInt::BigInt(u) => match i64::try_from(u) {
                Ok(u) => Ok(u),
                Err(e) => Err(ValError::new(
                    ErrorTypeDefaults::IntParsingSize,
                    e.into_original().into_py(py).into_ref(py),
                )),
            },
            EitherInt::Py(i) => i
                .extract()
                .map_err(|_| ValError::new(ErrorTypeDefaults::IntParsingSize, i)),
        }
    }

    pub fn as_int(&self) -> ValResult<'a, Int> {
        match self {
            EitherInt::I64(i) => Ok(Int::I64(*i)),
            EitherInt::U64(u) => match i64::try_from(*u) {
                Ok(i) => Ok(Int::I64(i)),
                Err(_) => Ok(Int::Big(BigInt::from(*u))),
            },
            EitherInt::BigInt(b) => Ok(Int::Big(b.clone())),
            EitherInt::Py(i) => i
                .extract()
                .map_err(|_| ValError::new(ErrorTypeDefaults::IntParsingSize, *i)),
        }
    }

    pub fn as_bool(&self) -> Option<bool> {
        match self {
            EitherInt::I64(i) => match i {
                0 => Some(false),
                1 => Some(true),
                _ => None,
            },
            EitherInt::U64(u) => match u {
                0 => Some(false),
                1 => Some(true),
                _ => None,
            },
            EitherInt::BigInt(i) => match u8::try_from(i) {
                Ok(0) => Some(false),
                Ok(1) => Some(true),
                _ => None,
            },
            EitherInt::Py(i) => match i.extract::<u8>() {
                Ok(0) => Some(false),
                Ok(1) => Some(true),
                _ => None,
            },
        }
    }
}

impl<'a> IntoPy<PyObject> for EitherInt<'a> {
    fn into_py(self, py: Python<'_>) -> PyObject {
        match self {
            Self::I64(int) => int.into_py(py),
            Self::U64(int) => int.into_py(py),
            Self::BigInt(int) => int.into_py(py),
            Self::Py(int) => int.into_py(py),
        }
    }
}

#[cfg_attr(debug_assertions, derive(Debug))]
#[derive(Copy, Clone)]
pub enum EitherFloat<'a> {
    F64(f64),
    Py(&'a PyFloat),
}

impl<'a> EitherFloat<'a> {
    pub fn as_f64(self) -> f64 {
        match self {
            EitherFloat::F64(f) => f,

            EitherFloat::Py(f) => {
                {
                    // Safety: known to be a python float
                    unsafe { ffi::PyFloat_AS_DOUBLE(f.as_ptr()) }
                }
            }
        }
    }
}

impl<'a> IntoPy<PyObject> for EitherFloat<'a> {
    fn into_py(self, py: Python<'_>) -> PyObject {
        match self {
            Self::F64(float) => float.into_py(py),
            Self::Py(float) => float.into_py(py),
        }
    }
}

#[derive(Debug, Clone, Serialize)]
#[serde(untagged)]
pub enum Int {
    I64(i64),
    #[serde(serialize_with = "serialize_bigint_as_number")]
    Big(BigInt),
}

// The default serialization for BigInt is some internal representation which roundtrips efficiently
// but is not the JSON value which users would expect to see.
fn serialize_bigint_as_number<S>(big_int: &BigInt, serializer: S) -> Result<S::Ok, S::Error>
where
    S: Serializer,
{
    serde_json::Number::from_str(&big_int.to_string())
        .map_err(S::Error::custom)
        .expect("a valid number")
        .serialize(serializer)
}

impl PartialOrd for Int {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        match (self, other) {
            (Int::I64(i1), Int::I64(i2)) => Some(i1.cmp(i2)),
            (Int::Big(b1), Int::Big(b2)) => Some(b1.cmp(b2)),
            (Int::I64(i), Int::Big(b)) => Some(BigInt::from(*i).cmp(b)),
            (Int::Big(b), Int::I64(i)) => Some(b.cmp(&BigInt::from(*i))),
        }
    }
}

impl PartialEq for Int {
    fn eq(&self, other: &Self) -> bool {
        self.partial_cmp(other) == Some(Ordering::Equal)
    }
}

impl<'a> Rem for &'a Int {
    type Output = Int;

    fn rem(self, rhs: Self) -> Self::Output {
        match (self, rhs) {
            (Int::I64(i1), Int::I64(i2)) => Int::I64(i1 % i2),
            (Int::Big(b1), Int::Big(b2)) => Int::Big(b1 % b2),
            (Int::I64(i), Int::Big(b)) => Int::Big(BigInt::from(*i) % b),
            (Int::Big(b), Int::I64(i)) => Int::Big(b % BigInt::from(*i)),
        }
    }
}

impl<'a> FromPyObject<'a> for Int {
    fn extract(obj: &'a PyAny) -> PyResult<Self> {
        if let Ok(i) = obj.extract::<i64>() {
            Ok(Int::I64(i))
        } else if let Ok(b) = obj.extract::<BigInt>() {
            Ok(Int::Big(b))
        } else {
            py_err!(PyTypeError; "Expected int, got {}", obj.get_type())
        }
    }
}

impl ToPyObject for Int {
    fn to_object(&self, py: Python<'_>) -> PyObject {
        match self {
            Self::I64(i) => i.to_object(py),
            Self::Big(big_i) => big_i.to_object(py),
        }
    }
}
