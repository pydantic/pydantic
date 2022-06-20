use pyo3::prelude::*;
use pyo3::types::{PyDict, PyFrozenSet, PyList, PySet, PyTuple};

use crate::errors::{LocItem, ValError, ValLineError, ValResult};
use crate::validators::{CombinedValidator, Extra, Validator};

use super::parse_json::{JsonArray, JsonObject};

pub enum GenericSequence<'a> {
    List(&'a PyList),
    Tuple(&'a PyTuple),
    Set(&'a PySet),
    FrozenSet(&'a PyFrozenSet),
    JsonArray(&'a JsonArray),
}

macro_rules! derive_from {
    ($enum:ident, $type:ty, $key:ident) => {
        impl<'a> From<&'a $type> for $enum<'a> {
            fn from(s: &'a $type) -> $enum<'a> {
                Self::$key(s)
            }
        }
    };
}
derive_from!(GenericSequence, PyList, List);
derive_from!(GenericSequence, PyTuple, Tuple);
derive_from!(GenericSequence, PySet, Set);
derive_from!(GenericSequence, PyFrozenSet, FrozenSet);
derive_from!(GenericSequence, JsonArray, JsonArray);

macro_rules! build_validate_to_vec {
    ($name:ident, $sequence_type:ty) => {
        fn $name<'a, 's>(
            py: Python<'a>,
            sequence: &'a $sequence_type,
            length: usize,
            validator: &'s CombinedValidator,
            extra: &Extra,
            slots: &'a [CombinedValidator],
        ) -> ValResult<'a, Vec<PyObject>> {
            let mut output: Vec<PyObject> = Vec::with_capacity(length);
            let mut errors: Vec<ValLineError> = Vec::new();
            for (index, item) in sequence.iter().enumerate() {
                match validator.validate(py, item, extra, slots) {
                    Ok(item) => output.push(item),
                    Err(ValError::LineErrors(line_errors)) => {
                        let loc = vec![LocItem::I(index)];
                        errors.extend(line_errors.into_iter().map(|err| err.with_prefix_location(&loc)));
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
    };
}
build_validate_to_vec!(validate_to_vec_list, PyList);
build_validate_to_vec!(validate_to_vec_tuple, PyTuple);
build_validate_to_vec!(validate_to_vec_set, PySet);
build_validate_to_vec!(validate_to_vec_frozenset, PyFrozenSet);
build_validate_to_vec!(validate_to_vec_jsonarray, JsonArray);

impl<'a> GenericSequence<'a> {
    pub fn generic_len(&self) -> usize {
        match self {
            Self::List(v) => v.len(),
            Self::Tuple(v) => v.len(),
            Self::Set(v) => v.len(),
            Self::FrozenSet(v) => v.len(),
            Self::JsonArray(v) => v.len(),
        }
    }

    pub fn validate_to_vec<'s>(
        &self,
        py: Python<'a>,
        length: usize,
        validator: &'s CombinedValidator,
        extra: &Extra,
        slots: &'a [CombinedValidator],
    ) -> ValResult<'a, Vec<PyObject>> {
        match self {
            Self::List(sequence) => validate_to_vec_list(py, sequence, length, validator, extra, slots),
            Self::Tuple(sequence) => validate_to_vec_tuple(py, sequence, length, validator, extra, slots),
            Self::Set(sequence) => validate_to_vec_set(py, sequence, length, validator, extra, slots),
            Self::FrozenSet(sequence) => validate_to_vec_frozenset(py, sequence, length, validator, extra, slots),
            Self::JsonArray(sequence) => validate_to_vec_jsonarray(py, sequence, length, validator, extra, slots),
        }
    }
}

pub enum GenericMapping<'a> {
    PyDict(&'a PyDict),
    JsonObject(&'a JsonObject),
}

derive_from!(GenericMapping, PyDict, PyDict);
derive_from!(GenericMapping, JsonObject, JsonObject);
