use std::borrow::Cow;
use std::cmp::Ordering;
use std::ops::Rem;
use std::slice::Iter as SliceIter;
use std::str::FromStr;

use jiter::{JsonArray, JsonObject, JsonValue};
use num_bigint::BigInt;

use pyo3::exceptions::PyTypeError;
use pyo3::prelude::*;
use pyo3::types::iter::{BoundDictIterator, BoundListIterator};
use pyo3::types::{
    PyByteArray, PyBytes, PyDict, PyFloat, PyFrozenSet, PyIterator, PyList, PyMapping, PySequence, PySet, PyString,
    PyTuple,
};
use pyo3::{ffi, intern};

#[cfg(not(PyPy))]
use pyo3::types::PyFunction;
use serde::{ser::Error, Serialize, Serializer};

use crate::errors::{
    py_err_string, ErrorType, ErrorTypeDefaults, InputValue, ToErrorValue, ValError, ValLineError, ValResult,
};
use crate::tools::{extract_i64, py_err};
use crate::validators::{CombinedValidator, Exactness, ValidationState, Validator};

use super::input_string::StringMapping;
use super::{py_error_on_minusone, BorrowInput, Input};

pub struct ValidationMatch<T>(T, Exactness);

impl<T> ValidationMatch<T> {
    pub const fn new(value: T, exactness: Exactness) -> Self {
        Self(value, exactness)
    }

    pub const fn exact(value: T) -> Self {
        Self(value, Exactness::Exact)
    }

    pub const fn strict(value: T) -> Self {
        Self(value, Exactness::Strict)
    }

    pub const fn lax(value: T) -> Self {
        Self(value, Exactness::Lax)
    }

    pub fn require_exact(self) -> Option<T> {
        (self.1 == Exactness::Exact).then_some(self.0)
    }

    pub fn unpack(self, state: &mut ValidationState) -> T {
        state.floor_exactness(self.1);
        self.0
    }

    pub fn into_inner(self) -> T {
        self.0
    }
}

/// Container for all the collections (sized iterable containers) types, which
/// can mostly be converted to each other in lax mode.
/// This mostly matches python's definition of `Collection`.
#[cfg_attr(debug_assertions, derive(Debug))]
pub enum GenericIterable<'a, 'py> {
    List(&'a Bound<'py, PyList>),
    Tuple(&'a Bound<'py, PyTuple>),
    Set(&'a Bound<'py, PySet>),
    FrozenSet(&'a Bound<'py, PyFrozenSet>),
    Dict(&'a Bound<'py, PyDict>),
    // Treat dict values / keys / items as generic iterators
    // since PyPy doesn't export the concrete types
    DictKeys(Bound<'py, PyIterator>),
    DictValues(Bound<'py, PyIterator>),
    DictItems(Bound<'py, PyIterator>),
    Mapping(&'a Bound<'py, PyMapping>),
    PyString(&'a Bound<'py, PyString>),
    Bytes(&'a Bound<'py, PyBytes>),
    PyByteArray(&'a Bound<'py, PyByteArray>),
    Sequence(&'a Bound<'py, PySequence>),
    Iterator(Bound<'py, PyIterator>),
    JsonArray(&'a [JsonValue]),
    JsonObject(&'a JsonObject),
    JsonString(&'a str),
}

impl<'py> GenericIterable<'_, 'py> {
    pub fn as_sequence_iterator(
        &self,
        py: Python<'py>,
    ) -> PyResult<Box<dyn Iterator<Item = PyResult<Bound<'py, PyAny>>> + '_>> {
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
                let v = v.to_object(py).into_bound(py);
                Ok(v)
            }))),
            // Note that this iterates over only the keys, just like doing iter({}) in Python, just for consistency
            GenericIterable::JsonObject(iter) => Ok(Box::new(
                iter.iter().map(move |(k, _)| Ok(k.to_object(py).into_bound(py))),
            )),
            GenericIterable::JsonString(s) => Ok(Box::new(PyString::new_bound(py, s).iter()?)),
        }
    }
}

struct MaxLengthCheck<'a, INPUT: ?Sized> {
    current_length: usize,
    max_length: Option<usize>,
    field_type: &'a str,
    input: &'a INPUT,
    actual_length: Option<usize>,
}

impl<'a, INPUT: ?Sized> MaxLengthCheck<'a, INPUT> {
    fn new(max_length: Option<usize>, field_type: &'a str, input: &'a INPUT, actual_length: Option<usize>) -> Self {
        Self {
            current_length: 0,
            max_length,
            field_type,
            input,
            actual_length,
        }
    }
}

impl<'py, INPUT: Input<'py> + ?Sized> MaxLengthCheck<'_, INPUT> {
    fn incr(&mut self) -> ValResult<()> {
        if let Some(max_length) = self.max_length {
            self.current_length += 1;
            if self.current_length > max_length {
                return Err(ValError::new_custom_input(
                    ErrorType::TooLong {
                        field_type: self.field_type.to_string(),
                        max_length,
                        actual_length: self.actual_length,
                        context: None,
                    },
                    self.input.to_error_value(),
                ));
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
fn validate_iter_to_vec<'py>(
    py: Python<'py>,
    iter: impl Iterator<Item = PyResult<impl BorrowInput<'py>>>,
    capacity: usize,
    mut max_length_check: MaxLengthCheck<'_, impl Input<'py> + ?Sized>,
    validator: &CombinedValidator,
    state: &mut ValidationState<'_, 'py>,
) -> ValResult<Vec<PyObject>> {
    let mut output: Vec<PyObject> = Vec::with_capacity(capacity);
    let mut errors: Vec<ValLineError> = Vec::new();
    for (index, item_result) in iter.enumerate() {
        let item = item_result.map_err(|e| any_next_error!(py, e, max_length_check.input, index))?;
        match validator.validate(py, item.borrow_input(), state) {
            Ok(item) => {
                max_length_check.incr()?;
                output.push(item);
            }
            Err(ValError::LineErrors(line_errors)) => {
                max_length_check.incr()?;
                errors.extend(line_errors.into_iter().map(|err| err.with_outer_location(index)));
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

impl BuildSet for Bound<'_, PySet> {
    fn build_add(&self, item: PyObject) -> PyResult<()> {
        self.add(item)
    }

    fn build_len(&self) -> usize {
        self.len()
    }
}

impl BuildSet for Bound<'_, PyFrozenSet> {
    fn build_add(&self, item: PyObject) -> PyResult<()> {
        py_error_on_minusone(self.py(), unsafe {
            // Safety: self.as_ptr() the _only_ pointer to the `frozenset`, and it's allowed
            // to mutate this via the C API when nothing else can refer to it.
            ffi::PySet_Add(self.as_ptr(), item.to_object(self.py()).as_ptr())
        })
    }

    fn build_len(&self) -> usize {
        self.len()
    }
}

#[allow(clippy::too_many_arguments)]
fn validate_iter_to_set<'py>(
    py: Python<'py>,
    set: &impl BuildSet,
    iter: impl Iterator<Item = PyResult<impl BorrowInput<'py>>>,
    input: &(impl Input<'py> + ?Sized),
    field_type: &'static str,
    max_length: Option<usize>,
    validator: &CombinedValidator,
    state: &mut ValidationState<'_, 'py>,
) -> ValResult<()> {
    let mut errors: Vec<ValLineError> = Vec::new();
    for (index, item_result) in iter.enumerate() {
        let item = item_result.map_err(|e| any_next_error!(py, e, input, index))?;
        match validator.validate(py, item.borrow_input(), state) {
            Ok(item) => {
                set.build_add(item)?;
                if let Some(max_length) = max_length {
                    if set.build_len() > max_length {
                        return Err(ValError::new(
                            ErrorType::TooLong {
                                field_type: field_type.to_string(),
                                max_length,
                                // The logic here is that it doesn't matter how many elements the
                                // input actually had; all we know is it had more than the allowed
                                // number of deduplicated elements.
                                actual_length: None,
                                context: None,
                            },
                            input,
                        ));
                    }
                }
            }
            Err(ValError::LineErrors(line_errors)) => {
                errors.extend(line_errors.into_iter().map(|err| err.with_outer_location(index)));
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

fn no_validator_iter_to_vec<'py>(
    py: Python<'py>,
    input: &(impl Input<'py> + ?Sized),
    iter: impl Iterator<Item = PyResult<impl BorrowInput<'py>>>,
    mut max_length_check: MaxLengthCheck<'_, impl Input<'py> + ?Sized>,
) -> ValResult<Vec<PyObject>> {
    iter.enumerate()
        .map(|(index, result)| {
            let v = result.map_err(|e| any_next_error!(py, e, input, index))?;
            max_length_check.incr()?;
            Ok(v.borrow_input().to_object(py))
        })
        .collect()
}

// pretty arbitrary default capacity when creating vecs from iteration
static DEFAULT_CAPACITY: usize = 10;

impl<'py> GenericIterable<'_, 'py> {
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
    pub fn validate_to_vec(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        max_length: Option<usize>,
        field_type: &'static str,
        validator: &CombinedValidator,
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Vec<PyObject>> {
        let actual_length = self.generic_len();
        let capacity = actual_length.unwrap_or(DEFAULT_CAPACITY);
        let max_length_check = MaxLengthCheck::new(max_length, field_type, input, actual_length);

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
    pub fn validate_to_set(
        &self,
        py: Python<'py>,
        set: &impl BuildSet,
        input: &(impl Input<'py> + ?Sized),
        max_length: Option<usize>,
        field_type: &'static str,
        validator: &CombinedValidator,
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<()> {
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

    pub fn to_vec(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        field_type: &'static str,
        max_length: Option<usize>,
    ) -> ValResult<Vec<PyObject>> {
        let actual_length = self.generic_len();
        let max_length_check = MaxLengthCheck::new(max_length, field_type, input, actual_length);

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
pub enum GenericMapping<'a, 'py> {
    PyDict(&'a Bound<'py, PyDict>),
    PyMapping(&'a Bound<'py, PyMapping>),
    StringMapping(&'a Bound<'py, PyDict>),
    PyGetAttr(Bound<'py, PyAny>, Option<Bound<'py, PyDict>>),
    JsonObject(&'a JsonObject),
}

macro_rules! derive_from {
    ($enum:ident, $key:ident, $type:ty $(, $extra_types:ident )*) => {
        impl<'a, 'py> From<&'a Bound<'py, $type>> for $enum<'a, 'py> {
            fn from(s: &'a Bound<'py, $type>) -> Self {
                Self::$key(s $(, $extra_types )*)
            }
        }
    };
}

derive_from!(GenericMapping, PyDict, PyDict);
derive_from!(GenericMapping, PyMapping, PyMapping);

impl<'a> From<&'a JsonObject> for GenericMapping<'a, '_> {
    fn from(s: &'a JsonObject) -> Self {
        Self::JsonObject(s)
    }
}

pub struct DictGenericIterator<'py> {
    dict_iter: BoundDictIterator<'py>,
}

impl<'py> DictGenericIterator<'py> {
    pub fn new(dict: &Bound<'py, PyDict>) -> ValResult<Self> {
        Ok(Self { dict_iter: dict.iter() })
    }
}

impl<'py> Iterator for DictGenericIterator<'py> {
    type Item = ValResult<(Bound<'py, PyAny>, Bound<'py, PyAny>)>;

    fn next(&mut self) -> Option<Self::Item> {
        self.dict_iter.next().map(Ok)
    }
    // size_hint is omitted as it isn't needed
}

pub struct MappingGenericIterator<'py> {
    input: Bound<'py, PyAny>,
    iter: Bound<'py, PyIterator>,
}

fn mapping_err<'py>(err: PyErr, py: Python<'py>, input: &'py (impl Input<'py> + ?Sized)) -> ValError {
    ValError::new(
        ErrorType::MappingType {
            error: py_err_string(py, err).into(),
            context: None,
        },
        input,
    )
}

impl<'py> MappingGenericIterator<'py> {
    pub fn new(mapping: &Bound<'py, PyMapping>) -> ValResult<Self> {
        let py = mapping.py();
        let input = mapping.as_any();
        let iter = mapping
            .items()
            .map_err(|e| mapping_err(e, py, input))?
            .iter()
            .map_err(|e| mapping_err(e, py, input))?;
        Ok(Self {
            input: input.clone(),
            iter,
        })
    }
}

const MAPPING_TUPLE_ERROR: &str = "Mapping items must be tuples of (key, value) pairs";

impl<'py> Iterator for MappingGenericIterator<'py> {
    type Item = ValResult<(Bound<'py, PyAny>, Bound<'py, PyAny>)>;

    fn next(&mut self) -> Option<Self::Item> {
        Some(match self.iter.next()? {
            Ok(item) => item.extract().map_err(|_| {
                ValError::new(
                    ErrorType::MappingType {
                        error: MAPPING_TUPLE_ERROR.into(),
                        context: None,
                    },
                    &self.input,
                )
            }),
            Err(e) => Err(mapping_err(e, self.iter.py(), &self.input)),
        })
    }
}

pub struct StringMappingGenericIterator<'py> {
    dict_iter: BoundDictIterator<'py>,
}

impl<'py> StringMappingGenericIterator<'py> {
    pub fn new(dict: &Bound<'py, PyDict>) -> ValResult<Self> {
        Ok(Self { dict_iter: dict.iter() })
    }
}

impl<'py> Iterator for StringMappingGenericIterator<'py> {
    // key (the first member of the tuple could be a simple String)
    type Item = ValResult<(StringMapping<'py>, StringMapping<'py>)>;

    fn next(&mut self) -> Option<Self::Item> {
        match self.dict_iter.next() {
            Some((py_key, py_value)) => {
                let key = match StringMapping::new_key(&py_key) {
                    Ok(key) => key,
                    Err(e) => return Some(Err(e)),
                };
                let value = match StringMapping::new_value(&py_value) {
                    Ok(value) => value,
                    Err(e) => return Some(Err(e)),
                };
                Some(Ok((key, value)))
            }
            None => None,
        }
    }
}

pub struct AttributesGenericIterator<'py> {
    object: Bound<'py, PyAny>,
    attributes_iterator: BoundListIterator<'py>,
}

impl<'py> AttributesGenericIterator<'py> {
    pub fn new(py_any: &Bound<'py, PyAny>) -> ValResult<Self> {
        let attributes_iterator = py_any.dir().into_iter();
        Ok(Self {
            object: py_any.clone(),
            attributes_iterator,
        })
    }
}

impl<'py> Iterator for AttributesGenericIterator<'py> {
    type Item = ValResult<(Bound<'py, PyAny>, Bound<'py, PyAny>)>;

    fn next(&mut self) -> Option<Self::Item> {
        // loop until we find an attribute who's name does not start with underscore,
        // or we get to the end of the list of attributes
        let name = self.attributes_iterator.next()?;
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
                if !is_bound && !attr.is_instance_of::<PyFunction>() {
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
        None
    }
    // size_hint is omitted as it isn't needed
}

pub struct JsonObjectGenericIterator<'py> {
    object_iter: SliceIter<'py, (String, JsonValue)>,
}

impl<'py> JsonObjectGenericIterator<'py> {
    pub fn new(json_object: &'py JsonObject) -> ValResult<Self> {
        Ok(Self {
            object_iter: json_object.iter(),
        })
    }
}

impl<'py> Iterator for JsonObjectGenericIterator<'py> {
    type Item = ValResult<(&'py String, &'py JsonValue)>;

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
        let json_iter = GenericJsonIterator { array, index: 0 };
        Self::JsonArray(json_iter)
    }
}

impl From<&Bound<'_, PyAny>> for GenericIterator {
    fn from(obj: &Bound<'_, PyAny>) -> Self {
        let py_iter = GenericPyIterator {
            obj: obj.clone().into(),
            iter: obj.iter().unwrap().into(),
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
    pub fn next<'py>(&mut self, py: Python<'py>) -> PyResult<Option<(Bound<'py, PyAny>, usize)>> {
        // TODO: .to_owned() is a workaround for PyO3 not allowing `.next()` to be called on
        // the reference
        match self.iter.bind(py).to_owned().next() {
            Some(Ok(next)) => {
                let a = (next, self.index);
                self.index += 1;
                Ok(Some(a))
            }
            Some(Err(err)) => Err(err),
            None => Ok(None),
        }
    }

    pub fn input_as_error_value(&self, py: Python<'_>) -> InputValue {
        InputValue::Python(self.obj.clone_ref(py))
    }

    pub fn index(&self) -> usize {
        self.index
    }
}

#[derive(Debug, Clone)]
pub struct GenericJsonIterator {
    array: JsonArray,
    index: usize,
}

impl GenericJsonIterator {
    pub fn next(&mut self, _py: Python) -> PyResult<Option<(&JsonValue, usize)>> {
        if self.index < self.array.len() {
            // panic here is impossible due to bounds check above; compiler should be
            // able to optimize it away even
            let next = &self.array[self.index];
            let a = (next, self.index);
            self.index += 1;
            Ok(Some(a))
        } else {
            Ok(None)
        }
    }

    pub fn input_as_error_value(&self, _py: Python<'_>) -> InputValue {
        InputValue::Json(JsonValue::Array(self.array.clone()))
    }

    pub fn index(&self) -> usize {
        self.index
    }
}

#[cfg_attr(debug_assertions, derive(Debug))]
pub struct PyArgs<'py> {
    pub args: Option<Bound<'py, PyTuple>>,
    pub kwargs: Option<Bound<'py, PyDict>>,
}

impl<'py> PyArgs<'py> {
    pub fn new(args: Option<Bound<'py, PyTuple>>, kwargs: Option<Bound<'py, PyDict>>) -> Self {
        Self { args, kwargs }
    }
}

#[cfg_attr(debug_assertions, derive(Debug))]
pub struct JsonArgs<'a> {
    pub args: Option<&'a [JsonValue]>,
    pub kwargs: Option<&'a JsonObject>,
}

impl<'a> JsonArgs<'a> {
    pub fn new(args: Option<&'a [JsonValue]>, kwargs: Option<&'a JsonObject>) -> Self {
        Self { args, kwargs }
    }
}

#[cfg_attr(debug_assertions, derive(Debug))]
pub enum GenericArguments<'a, 'py> {
    Py(PyArgs<'py>),
    Json(JsonArgs<'a>),
    StringMapping(Bound<'py, PyDict>),
}

impl<'py> From<PyArgs<'py>> for GenericArguments<'_, 'py> {
    fn from(s: PyArgs<'py>) -> Self {
        Self::Py(s)
    }
}

impl<'a> From<JsonArgs<'a>> for GenericArguments<'a, '_> {
    fn from(s: JsonArgs<'a>) -> Self {
        Self::Json(s)
    }
}

#[cfg_attr(debug_assertions, derive(Debug))]
pub enum EitherString<'a> {
    Cow(Cow<'a, str>),
    Py(Bound<'a, PyString>),
}

impl<'a> EitherString<'a> {
    pub fn as_cow(&self) -> ValResult<Cow<str>> {
        match self {
            Self::Cow(data) => Ok(data.clone()),
            Self::Py(py_str) => Ok(Cow::Borrowed(py_string_str(py_str)?)),
        }
    }

    pub fn as_py_string(&'a self, py: Python<'a>) -> Bound<'a, PyString> {
        match self {
            Self::Cow(cow) => PyString::new_bound(py, cow),
            Self::Py(py_string) => py_string.clone(),
        }
    }
}

impl<'a> From<&'a str> for EitherString<'a> {
    fn from(data: &'a str) -> Self {
        Self::Cow(Cow::Borrowed(data))
    }
}

impl<'a> From<String> for EitherString<'a> {
    fn from(data: String) -> Self {
        Self::Cow(Cow::Owned(data))
    }
}

impl<'a> From<Bound<'a, PyString>> for EitherString<'a> {
    fn from(date: Bound<'a, PyString>) -> Self {
        Self::Py(date)
    }
}

impl<'a> IntoPy<PyObject> for EitherString<'a> {
    fn into_py(self, py: Python<'_>) -> PyObject {
        self.as_py_string(py).into_py(py)
    }
}

pub fn py_string_str<'a>(py_str: &'a Bound<'_, PyString>) -> ValResult<&'a str> {
    py_str.to_str().map_err(|_| {
        ValError::new_custom_input(
            ErrorTypeDefaults::StringUnicode,
            InputValue::Python(py_str.clone().into()),
        )
    })
}

#[cfg_attr(debug_assertions, derive(Debug))]
pub enum EitherBytes<'a, 'py> {
    Cow(Cow<'a, [u8]>),
    Py(Bound<'py, PyBytes>),
}

impl<'a> From<Vec<u8>> for EitherBytes<'a, '_> {
    fn from(bytes: Vec<u8>) -> Self {
        Self::Cow(Cow::Owned(bytes))
    }
}

impl<'a> From<&'a [u8]> for EitherBytes<'a, '_> {
    fn from(bytes: &'a [u8]) -> Self {
        Self::Cow(Cow::Borrowed(bytes))
    }
}

impl<'a, 'py> From<&'a Bound<'py, PyBytes>> for EitherBytes<'a, 'py> {
    fn from(bytes: &'a Bound<'py, PyBytes>) -> Self {
        Self::Py(bytes.clone())
    }
}

impl EitherBytes<'_, '_> {
    pub fn as_slice(&self) -> &[u8] {
        match self {
            EitherBytes::Cow(bytes) => bytes,
            EitherBytes::Py(py_bytes) => py_bytes.as_bytes(),
        }
    }

    pub fn len(&self) -> PyResult<usize> {
        match self {
            EitherBytes::Cow(bytes) => Ok(bytes.len()),
            EitherBytes::Py(py_bytes) => py_bytes.len(),
        }
    }
}

impl IntoPy<PyObject> for EitherBytes<'_, '_> {
    fn into_py(self, py: Python<'_>) -> PyObject {
        match self {
            EitherBytes::Cow(bytes) => PyBytes::new_bound(py, &bytes).into_py(py),
            EitherBytes::Py(py_bytes) => py_bytes.into_py(py),
        }
    }
}

#[cfg_attr(debug_assertions, derive(Debug))]
pub enum EitherInt<'a> {
    I64(i64),
    U64(u64),
    BigInt(BigInt),
    Py(Bound<'a, PyAny>),
}

impl<'a> EitherInt<'a> {
    pub fn upcast(py_any: &Bound<'a, PyAny>) -> ValResult<Self> {
        // Safety: we know that py_any is a python int
        if let Some(int_64) = extract_i64(py_any) {
            Ok(Self::I64(int_64))
        } else {
            let big_int: BigInt = py_any.extract()?;
            Ok(Self::BigInt(big_int))
        }
    }
    pub fn into_i64(self, py: Python<'a>) -> ValResult<i64> {
        match self {
            EitherInt::I64(i) => Ok(i),
            EitherInt::U64(u) => match i64::try_from(u) {
                Ok(u) => Ok(u),
                Err(_) => Err(ValError::new(ErrorTypeDefaults::IntParsingSize, u.into_py(py).bind(py))),
            },
            EitherInt::BigInt(u) => match i64::try_from(u) {
                Ok(u) => Ok(u),
                Err(e) => Err(ValError::new(
                    ErrorTypeDefaults::IntParsingSize,
                    e.into_original().into_py(py).bind(py),
                )),
            },
            EitherInt::Py(i) => i
                .extract()
                .map_err(|_| ValError::new(ErrorTypeDefaults::IntParsingSize, &i)),
        }
    }

    pub fn as_int(&self) -> ValResult<Int> {
        match self {
            EitherInt::I64(i) => Ok(Int::I64(*i)),
            EitherInt::U64(u) => match i64::try_from(*u) {
                Ok(i) => Ok(Int::I64(i)),
                Err(_) => Ok(Int::Big(BigInt::from(*u))),
            },
            EitherInt::BigInt(b) => Ok(Int::Big(b.clone())),
            EitherInt::Py(i) => i
                .extract()
                .map_err(|_| ValError::new(ErrorTypeDefaults::IntParsingSize, i)),
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
#[derive(Clone)]
pub enum EitherFloat<'a> {
    F64(f64),
    Py(Bound<'a, PyFloat>),
}

impl<'a> EitherFloat<'a> {
    pub fn as_f64(&self) -> f64 {
        match self {
            EitherFloat::F64(f) => *f,
            EitherFloat::Py(f) => f.value(),
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

impl FromPyObject<'_> for Int {
    fn extract_bound(obj: &Bound<'_, PyAny>) -> PyResult<Self> {
        if let Some(i) = extract_i64(obj) {
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
