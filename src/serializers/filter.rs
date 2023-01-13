use std::hash::{BuildHasher, BuildHasherDefault, Hash};

use pyo3::exceptions::PyTypeError;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PySet, PyString};

use nohash_hasher::{IntSet, NoHashHasher};

use crate::build_tools::SchemaDict;

#[derive(Debug, Clone, Default)]
pub(super) struct SchemaFilter<T> {
    include: Option<IntSet<T>>,
    exclude: Option<IntSet<T>>,
}

impl SchemaFilter<usize> {
    pub fn from_schema(schema: &PyDict) -> PyResult<Self> {
        let py = schema.py();
        match schema.get_as::<&PyDict>(intern!(py, "serialization"))? {
            Some(ser) => {
                let include = Self::build_set_ints(ser.get_item(intern!(py, "include")))?;
                let exclude = Self::build_set_ints(ser.get_item(intern!(py, "exclude")))?;
                Ok(Self { include, exclude })
            }
            None => Ok(SchemaFilter::default()),
        }
    }

    fn build_set_ints(v: Option<&PyAny>) -> PyResult<Option<IntSet<usize>>> {
        match v {
            Some(value) => {
                if value.is_none() {
                    Ok(None)
                } else {
                    let py_set: &PySet = value.cast_as()?;
                    let mut set: IntSet<usize> =
                        IntSet::with_capacity_and_hasher(py_set.len(), BuildHasherDefault::default());

                    for item in py_set {
                        set.insert(item.extract()?);
                    }
                    Ok(Some(set))
                }
            }
            None => Ok(None),
        }
    }

    pub fn value_filter<'py>(
        &self,
        index: usize,
        include: Option<&'py PyAny>,
        exclude: Option<&'py PyAny>,
    ) -> PyResult<Option<(Option<&'py PyAny>, Option<&'py PyAny>)>> {
        self.filter(index, index, include, exclude)
    }
}

impl SchemaFilter<isize> {
    pub fn from_set_hash(include: Option<&PyAny>, exclude: Option<&PyAny>) -> PyResult<Self> {
        let include = Self::build_set_hashes(include)?;
        let exclude = Self::build_set_hashes(exclude)?;
        Ok(Self { include, exclude })
    }

    pub fn from_vec_hash(py: Python, exclude: Vec<Py<PyString>>) -> PyResult<Self> {
        let exclude = if exclude.is_empty() {
            None
        } else {
            let mut set: IntSet<isize> = IntSet::with_capacity_and_hasher(exclude.len(), BuildHasherDefault::default());
            for item in exclude {
                set.insert(item.as_ref(py).hash()?);
            }
            Some(set)
        };
        Ok(Self { include: None, exclude })
    }

    fn build_set_hashes(v: Option<&PyAny>) -> PyResult<Option<IntSet<isize>>> {
        match v {
            Some(value) => {
                if value.is_none() {
                    Ok(None)
                } else {
                    let py_set: &PySet = value.cast_as()?;
                    let mut set: IntSet<isize> =
                        IntSet::with_capacity_and_hasher(py_set.len(), BuildHasherDefault::default());

                    for item in py_set {
                        set.insert(item.hash()?);
                    }
                    Ok(Some(set))
                }
            }
            None => Ok(None),
        }
    }

    pub fn key_filter<'py>(
        &self,
        key: &PyAny,
        include: Option<&'py PyAny>,
        exclude: Option<&'py PyAny>,
    ) -> PyResult<Option<(Option<&'py PyAny>, Option<&'py PyAny>)>> {
        let hash = key.hash()?;
        self.filter(key, hash, include, exclude)
    }
}

trait FilterLogic<T: Eq + Copy> {
    /// whether an `index`/`key` is explicitly included, this is combined with call-time `include` below
    fn explicit_include(&self, value: T) -> bool;
    /// default decision on whether to include the item at a given `index`/`key`
    fn default_filter(&self, value: T) -> bool;

    /// this is the somewhat hellish logic for deciding:
    /// 1. whether we should omit a value at a particular index/key - returning `Ok(None)` here
    /// 2. or include it, in which case, what values of `include` and `exclude` should be passed to it
    fn filter<'py>(
        &self,
        py_key: impl ToPyObject + Copy,
        int_key: T,
        include: Option<&'py PyAny>,
        exclude: Option<&'py PyAny>,
    ) -> PyResult<Option<(Option<&'py PyAny>, Option<&'py PyAny>)>> {
        let mut next_exclude: Option<&PyAny> = None;
        if let Some(exclude) = exclude {
            if let Ok(exclude_dict) = exclude.cast_as::<PyDict>() {
                if let Some(exc_value) = exclude_dict.get_item(py_key) {
                    if exc_value.is_none() {
                        // if the index is in exclude, and the exclude value is `None`, we want to omit this index
                        return Ok(None);
                    } else {
                        // if the index is in exclude, and the exclude-value is not `None`,
                        // we want to return `Some((..., Some(next_exclude))`
                        next_exclude = Some(exc_value);
                    }
                }
            } else if let Ok(exclude_set) = exclude.cast_as::<PySet>() {
                // question: should we `unwrap_or(false)` instead of raise an error here?
                if exclude_set.contains(py_key)? {
                    // index is in the exclude set, we return Ok(None) to omit this index
                    return Ok(None);
                }
            } else if !exclude.is_none() {
                return Err(PyTypeError::new_err("`exclude` argument must a set or dict."));
            }
        }

        if let Some(include) = include {
            if let Ok(include_dict) = include.cast_as::<PyDict>() {
                if let Some(inc_value) = include_dict.get_item(py_key) {
                    // if the index is in include, we definitely want to include this index
                    return if inc_value.is_none() {
                        Ok(Some((None, next_exclude)))
                    } else {
                        Ok(Some((Some(inc_value), next_exclude)))
                    };
                } else if !self.explicit_include(int_key) {
                    // if the index is not in include, include exists, AND it's not in schema include,
                    // this index should be omitted
                    return Ok(None);
                }
            } else if let Ok(include_set) = include.cast_as::<PySet>() {
                // question: as above
                if include_set.contains(py_key)? {
                    return Ok(Some((None, next_exclude)));
                } else if !self.explicit_include(int_key) {
                    // if the index is not in include, include exists, AND it's not in schema include,
                    // this index should be omitted
                    return Ok(None);
                }
            } else if !include.is_none() {
                return Err(PyTypeError::new_err("`include` argument must a set or dict."));
            }
        }

        if next_exclude.is_some() {
            Ok(Some((None, next_exclude)))
        } else if self.default_filter(int_key) {
            Ok(Some((None, None)))
        } else {
            Ok(None)
        }
    }
}

impl<T> FilterLogic<T> for SchemaFilter<T>
where
    T: Hash + Eq + Copy,
    BuildHasherDefault<NoHashHasher<T>>: BuildHasher,
{
    fn explicit_include(&self, value: T) -> bool {
        match self.include {
            Some(ref include) => include.contains(&value),
            None => false,
        }
    }

    fn default_filter(&self, value: T) -> bool {
        match (&self.include, &self.exclude) {
            (Some(include), Some(exclude)) => include.contains(&value) && !exclude.contains(&value),
            (Some(include), None) => include.contains(&value),
            (None, Some(exclude)) => !exclude.contains(&value),
            (None, None) => true,
        }
    }
}

#[derive(Debug, Clone)]
pub(super) struct AnyFilter;

impl AnyFilter {
    pub fn new() -> Self {
        AnyFilter {}
    }

    pub fn key_filter<'py>(
        &self,
        key: &PyAny,
        include: Option<&'py PyAny>,
        exclude: Option<&'py PyAny>,
    ) -> PyResult<Option<(Option<&'py PyAny>, Option<&'py PyAny>)>> {
        // just use 0 for the int_key, it's always ignored in the implementation here
        self.filter(key, 0, include, exclude)
    }

    pub fn value_filter<'py>(
        &self,
        index: usize,
        include: Option<&'py PyAny>,
        exclude: Option<&'py PyAny>,
    ) -> PyResult<Option<(Option<&'py PyAny>, Option<&'py PyAny>)>> {
        self.filter(index, index, include, exclude)
    }
}

impl<T> FilterLogic<T> for AnyFilter
where
    T: Eq + Copy,
{
    fn explicit_include(&self, _value: T) -> bool {
        false
    }

    fn default_filter(&self, _value: T) -> bool {
        true
    }
}
