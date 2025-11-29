use core::fmt;

use hashbrown::HashTable;
use pyo3::PyTraverseError;
use pyo3::PyVisit;
use pyo3::exceptions::PyKeyError;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyMapping, PyString};

use crate::PydanticUndefinedType;
use crate::py_gc::PyGcTraverse;
use jiter::{StringCacheMode, cached_py_string};

pub trait SchemaDict<'py> {
    fn get_as<T>(&self, key: &Bound<'py, PyString>) -> PyResult<Option<T>>
    where
        T: FromPyObjectOwned<'py>;

    fn get_as_req<T>(&self, key: &Bound<'py, PyString>) -> PyResult<T>
    where
        T: FromPyObjectOwned<'py>;
}

impl<'py> SchemaDict<'py> for Bound<'py, PyDict> {
    fn get_as<T>(&self, key: &Bound<'py, PyString>) -> PyResult<Option<T>>
    where
        T: FromPyObjectOwned<'py>,
    {
        match self.get_item(key)? {
            Some(t) => t.extract().map(Some).map_err(Into::into),
            None => Ok(None),
        }
    }

    fn get_as_req<T>(&self, key: &Bound<'py, PyString>) -> PyResult<T>
    where
        T: FromPyObjectOwned<'py>,
    {
        match self.get_item(key)? {
            Some(t) => t.extract().map_err(Into::into),
            None => py_err!(PyKeyError; "{}", key),
        }
    }
}

impl<'py> SchemaDict<'py> for Option<&Bound<'py, PyDict>> {
    fn get_as<T>(&self, key: &Bound<'py, PyString>) -> PyResult<Option<T>>
    where
        T: FromPyObjectOwned<'py>,
    {
        match self {
            Some(d) => d.get_as(key),
            None => Ok(None),
        }
    }

    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn get_as_req<T>(&self, key: &Bound<'py, PyString>) -> PyResult<T>
    where
        T: FromPyObjectOwned<'py>,
    {
        match self {
            Some(d) => d.get_as_req(key),
            None => py_err!(PyKeyError; "{}", key),
        }
    }
}

macro_rules! py_error_type {
    ($error_type:ty; $msg:expr) => {
        <$error_type>::new_err($msg)
    };

    ($error_type:ty; $msg:expr, $( $msg_args:expr ),+ ) => {
        <$error_type>::new_err(format!($msg, $( $msg_args ),+))
    };
}
pub(crate) use py_error_type;

macro_rules! py_err {
    ($error_type:ty; $msg:expr) => {
        Err(crate::tools::py_error_type!($error_type; $msg))
    };

    ($error_type:ty; $msg:expr, $( $msg_args:expr ),+ ) => {
        Err(crate::tools::py_error_type!($error_type; $msg, $( $msg_args ),+))
    };
}
pub(crate) use py_err;

pub fn function_name(f: &Bound<'_, PyAny>) -> PyResult<String> {
    match f.getattr(intern!(f.py(), "__name__")) {
        Ok(name) => name.extract(),
        _ => f.repr()?.extract(),
    }
}

pub enum ReprOutput<'py> {
    Python(Bound<'py, PyString>),
    Fallback(String),
}

impl std::fmt::Display for ReprOutput<'_> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ReprOutput::Python(s) => write!(f, "{}", s.to_string_lossy()),
            ReprOutput::Fallback(s) => write!(f, "{s}"),
        }
    }
}

pub fn safe_repr<'py>(v: &Bound<'py, PyAny>) -> ReprOutput<'py> {
    if let Ok(s) = v.repr() {
        ReprOutput::Python(s)
    } else if let Ok(name) = v.get_type().qualname() {
        ReprOutput::Fallback(format!("<unprintable {name} object>"))
    } else {
        ReprOutput::Fallback("<unprintable object>".to_owned())
    }
}

// warning: this function can be incredibly slow, so use with caution
pub fn truncate_safe_repr(v: &Bound<'_, PyAny>, max_len: Option<usize>) -> String {
    let max_len = max_len.unwrap_or(50); // default to 100 bytes
    let input_str = safe_repr(v);
    let mut limited_str = String::with_capacity(max_len);
    write_truncated_to_limited_bytes(&mut limited_str, &input_str.to_string(), max_len)
        .expect("Writing to a `String` failed");
    limited_str
}

pub(crate) fn new_py_string<'py>(py: Python<'py>, s: &str, cache_str: StringCacheMode) -> Bound<'py, PyString> {
    // we could use `bytecount::num_chars(s.as_bytes()) == s.len()` as orjson does, but it doesn't appear to be faster
    if matches!(cache_str, StringCacheMode::All) {
        cached_py_string(py, s)
    } else {
        PyString::new(py, s)
    }
}

// TODO: is_utf8_char_boundary, floor_char_boundary and ceil_char_boundary
// with builtin methods once https://github.com/rust-lang/rust/issues/93743 is resolved
// These are just copy pasted from the current implementation
const fn is_utf8_char_boundary(value: u8) -> bool {
    // This is bit magic equivalent to: b < 128 || b >= 192
    (value as i8) >= -0x40
}

pub fn floor_char_boundary(value: &str, index: usize) -> usize {
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

pub fn write_truncated_to_limited_bytes<F: fmt::Write>(f: &mut F, val: &str, max_len: usize) -> std::fmt::Result {
    if val.len() > max_len {
        let mid_point = max_len.div_ceil(2);
        write!(
            f,
            "{}...{}",
            &val[0..floor_char_boundary(val, mid_point)],
            &val[ceil_char_boundary(val, val.len() - (mid_point - 1))..]
        )
    } else {
        write!(f, "{val}")
    }
}

/// Implementation of `mapping.get(key, PydanticUndefined)` which returns `None` if the key is not found
pub fn mapping_get<'py>(
    mapping: &Bound<'py, PyMapping>,
    key: impl IntoPyObject<'py>,
) -> PyResult<Option<Bound<'py, PyAny>>> {
    let undefined = PydanticUndefinedType::get(mapping.py());
    mapping
        .call_method1(intern!(mapping.py(), "get"), (key, undefined))
        .map(|value| if value.is(undefined) { None } else { Some(value) })
}

/// A hash table which uses (hashable) Python objects as keys
#[derive(Debug)]
pub struct PyHashTable<T>(HashTable<PyHashTableEntry<T>>);

#[derive(Debug)]
struct PyHashTableEntry<T> {
    key: Py<PyAny>,
    /// Precomputed hash value (from Python hash) - this avoids possibility of Python
    /// dynamic nature causing rehashing to fail
    hash: u64,
    value: T,
}

impl PyGcTraverse for PyHashTable<usize> {
    fn py_gc_traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        // traverse only the keys, as the values are just usize indices
        self.0.iter().try_for_each(|entry| entry.key.py_gc_traverse(visit))
    }
}

impl<T> PyHashTable<T> {
    /// Create a new empty hash table with the specified capacity
    pub fn with_capacity(capacity: usize) -> Self {
        Self(HashTable::with_capacity(capacity))
    }

    /// Insert a value into the hash table without checking for duplicates
    ///
    /// Errors if the key is unhashable
    pub fn insert_unique(&mut self, key: Bound<'_, PyAny>, value: T) -> PyResult<()> {
        let hash = hash_object(&key)?;
        let entry = PyHashTableEntry {
            key: key.unbind(),
            hash,
            value,
        };
        self.0.insert_unique(hash, entry, Self::get_hash);
        Ok(())
    }

    /// Find a value in the hash table by Python object key
    pub fn get(&self, value: &Bound<'_, PyAny>) -> PyResult<Option<&T>> {
        let mut searcher = HashTableSearcher::new(value);
        let hash = hash_object(value)?;
        let result = self.0.find(hash, |entry| searcher.is_equal(&entry.key));
        searcher.ensure_no_error()?;
        Ok(result.map(|entry| &entry.value))
    }

    #[inline]
    fn get_hash(entry: &PyHashTableEntry<T>) -> u64 {
        entry.hash
    }
}

/// Helper for `PyHashTable` which works around possible errors during equality checks
struct HashTableSearcher<'a, 'py> {
    target: &'a Bound<'py, PyAny>,
    eq_error: Option<PyErr>,
}

impl<'a, 'py> HashTableSearcher<'a, 'py> {
    /// Create a new searcher for the specified target
    fn new(target: &'a Bound<'py, PyAny>) -> Self {
        Self { target, eq_error: None }
    }

    /// Compare the target with another Python object for equality
    ///
    /// On error, returns true and stores the error internally to short-circuit the search
    fn is_equal(&mut self, other: &Py<PyAny>) -> bool {
        self.target.eq(other).unwrap_or_else(|e| {
            self.eq_error = Some(e);
            true
        })
    }

    /// Consumes the searcher, returning any error encountered during equality checks
    fn ensure_no_error(self) -> PyResult<()> {
        match self.eq_error {
            Some(err) => Err(err),
            None => Ok(()),
        }
    }
}

fn hash_object(value: &Bound<'_, PyAny>) -> PyResult<u64> {
    let hash_value = cast_unsigned(value.hash()?).try_into()?;
    Ok(hash_value)
}

// TODO: replace with isize::cast_unsigned on MSRV 1.87
fn cast_unsigned(x: isize) -> usize {
    x as usize
}

impl<T: PyGcTraverse> PyGcTraverse for PyHashTableEntry<T> {
    fn py_gc_traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        self.key.py_gc_traverse(visit)?;
        self.value.py_gc_traverse(visit)?;
        Ok(())
    }
}

impl PyGcTraverse for usize {
    #[inline]
    fn py_gc_traverse(&self, _visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        Ok(())
    }
}
