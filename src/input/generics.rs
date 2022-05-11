use enum_dispatch::enum_dispatch;
use indexmap::map::Iter;

use pyo3::types::{PyAny, PyDict, PyFrozenSet, PyList, PySet, PyTuple};
use pyo3::{ffi, AsPyPointer};

use super::parse_json::{JsonArray, JsonInput, JsonObject};
use super::Input;

#[enum_dispatch]
pub enum GenericSequence<'a> {
    List(&'a PyList),
    Tuple(&'a PyTuple),
    Set(&'a PySet),
    FrozenSet(&'a PyFrozenSet),
    JsonArray(&'a JsonArray),
}

#[enum_dispatch(GenericSequence)]
pub trait SequenceLenIter<'a> {
    fn generic_len(&self) -> usize;

    fn generic_iter(&self) -> GenericSequenceIter<'a>;
}

impl<'a> SequenceLenIter<'a> for &'a PyList {
    fn generic_len(&self) -> usize {
        self.len()
    }

    fn generic_iter(&self) -> GenericSequenceIter<'a> {
        GenericSequenceIter::List(PyListIterator {
            sequence: self,
            index: 0,
        })
    }
}

impl<'a> SequenceLenIter<'a> for &'a PyTuple {
    fn generic_len(&self) -> usize {
        self.len()
    }

    fn generic_iter(&self) -> GenericSequenceIter<'a> {
        GenericSequenceIter::Tuple(PyTupleIterator {
            sequence: self,
            index: 0,
            length: self.len(),
        })
    }
}

impl<'a> SequenceLenIter<'a> for &'a PySet {
    fn generic_len(&self) -> usize {
        self.len()
    }

    fn generic_iter(&self) -> GenericSequenceIter<'a> {
        GenericSequenceIter::Set(PySetIterator {
            sequence: self,
            index: 0,
        })
    }
}

impl<'a> SequenceLenIter<'a> for &'a PyFrozenSet {
    fn generic_len(&self) -> usize {
        self.len()
    }

    fn generic_iter(&self) -> GenericSequenceIter<'a> {
        GenericSequenceIter::Set(PySetIterator {
            sequence: self,
            index: 0,
        })
    }
}

impl<'a> SequenceLenIter<'a> for &'a JsonArray {
    fn generic_len(&self) -> usize {
        self.len()
    }

    fn generic_iter(&self) -> GenericSequenceIter<'a> {
        GenericSequenceIter::JsonArray(JsonArrayIterator {
            sequence: self,
            index: 0,
        })
    }
}

#[enum_dispatch]
pub enum GenericSequenceIter<'a> {
    List(PyListIterator<'a>),
    Tuple(PyTupleIterator<'a>),
    Set(PySetIterator<'a>),
    JsonArray(JsonArrayIterator<'a>),
}

#[enum_dispatch(GenericSequenceIter)]
pub trait SequenceNext<'a> {
    fn _next(&mut self) -> Option<(usize, &'a dyn Input)>;
}

impl<'a> Iterator for GenericSequenceIter<'a> {
    type Item = (usize, &'a dyn Input);

    #[inline]
    fn next(&mut self) -> Option<(usize, &'a dyn Input)> {
        self._next()
    }
}

pub struct PyListIterator<'a> {
    sequence: &'a PyList,
    index: usize,
}

impl<'a> SequenceNext<'a> for PyListIterator<'a> {
    #[inline]
    fn _next(&mut self) -> Option<(usize, &'a dyn Input)> {
        if self.index < self.sequence.len() {
            let item = unsafe { self.sequence.get_item_unchecked(self.index) };
            let index = self.index;
            self.index += 1;
            Some((index, item))
        } else {
            None
        }
    }
}

pub struct PyTupleIterator<'a> {
    sequence: &'a PyTuple,
    index: usize,
    length: usize,
}

impl<'a> SequenceNext<'a> for PyTupleIterator<'a> {
    #[inline]
    fn _next(&mut self) -> Option<(usize, &'a dyn Input)> {
        if self.index < self.length {
            let item = unsafe { self.sequence.get_item_unchecked(self.index) };
            let index = self.index;
            self.index += 1;
            Some((index, item))
        } else {
            None
        }
    }
}

pub struct PySetIterator<'a> {
    sequence: &'a PyAny,
    index: isize,
}

impl<'a> SequenceNext<'a> for PySetIterator<'a> {
    #[inline]
    fn _next(&mut self) -> Option<(usize, &'a dyn Input)> {
        unsafe {
            let mut key: *mut ffi::PyObject = std::ptr::null_mut();
            let mut hash: ffi::Py_hash_t = 0;
            let index = self.index as usize;
            if ffi::_PySet_NextEntry(self.sequence.as_ptr(), &mut self.index, &mut key, &mut hash) != 0 {
                // _PySet_NextEntry returns borrowed object; for safety must make owned (see #890)
                let item: &PyAny = self.sequence.py().from_owned_ptr(ffi::_Py_NewRef(key));
                Some((index, item))
            } else {
                None
            }
        }
    }
}

pub struct JsonArrayIterator<'a> {
    sequence: &'a JsonArray,
    index: usize,
}

impl<'a> SequenceNext<'a> for JsonArrayIterator<'a> {
    #[inline]
    fn _next(&mut self) -> Option<(usize, &'a dyn Input)> {
        match self.sequence.get(self.index) {
            Some(item) => {
                let index = self.index;
                self.index += 1;
                Some((index, item))
            }
            None => None,
        }
    }
}

#[enum_dispatch]
pub enum GenericMapping<'a> {
    PyDict(&'a PyDict),
    JsonObject(&'a JsonObject),
}

// TODO work out how to avoid recursive error - should be `len`, `get` and `iter`
#[enum_dispatch(GenericMapping)]
pub trait MappingLenIter<'a> {
    fn generic_len(&self) -> usize;

    fn generic_get(&self, key: &str) -> Option<&'a dyn Input>;

    fn generic_iter(&self) -> GenericMappingIter<'a>;
}

impl<'a> MappingLenIter<'a> for &'a PyDict {
    #[inline]
    fn generic_len(&self) -> usize {
        self.len()
    }

    #[inline]
    fn generic_get(&self, key: &str) -> Option<&'a dyn Input> {
        self.get_item(key).map(|v| v as &dyn Input)
    }

    #[inline]
    fn generic_iter(&self) -> GenericMappingIter<'a> {
        GenericMappingIter::PyDict(PyDictIterator { dict: self, index: 0 })
    }
}

impl<'a> MappingLenIter<'a> for &'a JsonObject {
    #[inline]
    fn generic_len(&self) -> usize {
        self.len()
    }

    #[inline]
    fn generic_get(&self, key: &str) -> Option<&'a dyn Input> {
        self.get(key).map(|v| v as &dyn Input)
    }

    #[inline]
    fn generic_iter(&self) -> GenericMappingIter<'a> {
        GenericMappingIter::JsonObject(JsonObjectIterator { iter: self.iter() })
    }
}

#[enum_dispatch]
pub enum GenericMappingIter<'a> {
    PyDict(PyDictIterator<'a>),
    JsonObject(JsonObjectIterator<'a>),
}

/// helper trait implemented by all types in GenericMappingIter which is used when for the shared implementation of
/// `Iterator` for `GenericMappingIter`
#[enum_dispatch(GenericMappingIter)]
pub trait DictNext<'a> {
    fn _next(&mut self) -> Option<(&'a dyn Input, &'a dyn Input)>;
}

impl<'a> Iterator for GenericMappingIter<'a> {
    type Item = (&'a dyn Input, &'a dyn Input);

    #[inline]
    fn next(&mut self) -> Option<(&'a dyn Input, &'a dyn Input)> {
        self._next()
    }
}

pub struct PyDictIterator<'a> {
    dict: &'a PyDict,
    index: isize,
}

impl<'a> DictNext<'a> for PyDictIterator<'a> {
    #[inline]
    fn _next(&mut self) -> Option<(&'a dyn Input, &'a dyn Input)> {
        unsafe {
            let mut key: *mut ffi::PyObject = std::ptr::null_mut();
            let mut value: *mut ffi::PyObject = std::ptr::null_mut();
            if ffi::PyDict_Next(self.dict.as_ptr(), &mut self.index, &mut key, &mut value) != 0 {
                // PyDict_Next returns borrowed values; for safety must make them owned (see #890)
                let py = self.dict.py();
                let key: &PyAny = py.from_owned_ptr(ffi::_Py_NewRef(key));
                let value: &PyAny = py.from_owned_ptr(ffi::_Py_NewRef(value));
                Some((key, value))
            } else {
                None
            }
        }
    }
}

pub struct JsonObjectIterator<'a> {
    iter: Iter<'a, String, JsonInput>,
}

impl<'a> DictNext<'a> for JsonObjectIterator<'a> {
    #[inline]
    fn _next(&mut self) -> Option<(&'a dyn Input, &'a dyn Input)> {
        self.iter.next().map(|(k, v)| (k as &dyn Input, v as &dyn Input))
    }
}
