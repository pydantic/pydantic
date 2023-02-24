use ahash::AHashSet;
use std::hash::Hash;

use pyo3::exceptions::PyTypeError;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyBool, PyDict, PySet, PyString};

use crate::build_tools::SchemaDict;

#[derive(Debug, Clone, Default)]
pub(crate) struct SchemaFilter<T> {
    include: Option<AHashSet<T>>,
    exclude: Option<AHashSet<T>>,
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

    fn build_set_ints(v: Option<&PyAny>) -> PyResult<Option<AHashSet<usize>>> {
        match v {
            Some(value) => {
                if value.is_none() {
                    Ok(None)
                } else {
                    let py_set: &PySet = value.downcast()?;
                    let mut set: AHashSet<usize> = AHashSet::with_capacity(py_set.len());

                    for item in py_set {
                        set.insert(item.extract()?);
                    }
                    Ok(Some(set))
                }
            }
            None => Ok(None),
        }
    }

    pub fn index_filter<'py>(
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
            let mut set: AHashSet<isize> = AHashSet::with_capacity(exclude.len());
            for item in exclude {
                set.insert(item.as_ref(py).hash()?);
            }
            Some(set)
        };
        Ok(Self { include: None, exclude })
    }

    fn build_set_hashes(v: Option<&PyAny>) -> PyResult<Option<AHashSet<isize>>> {
        match v {
            Some(value) => {
                if value.is_none() {
                    Ok(None)
                } else {
                    let py_set: &PySet = value.downcast()?;
                    let mut set: AHashSet<isize> = AHashSet::with_capacity(py_set.len());

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
            if exclude.is_none() {
                // Do nothing; place this check at the top for performance in the common case
            } else if let Ok(exclude_dict) = exclude.downcast::<PyDict>() {
                let op_exc_value = merge_all_value(exclude_dict, py_key)?;
                if let Some(exc_value) = op_exc_value {
                    if is_ellipsis_like(exc_value) {
                        // if the index is in exclude, and the exclude value is `None`, we want to omit this index/item
                        return Ok(None);
                    } else {
                        // if the index is in exclude, and the exclude-value is not `None`,
                        // we want to return `Some((..., Some(next_exclude))`
                        next_exclude = Some(exc_value);
                    }
                }
            } else if let Ok(exclude_set) = exclude.downcast::<PySet>() {
                if exclude_set.contains(py_key)? || exclude_set.contains(intern!(exclude_set.py(), "__all__"))? {
                    // index is in the exclude set, we return Ok(None) to omit this index
                    return Ok(None);
                }
            } else if let Some(contains) = check_contains(exclude, py_key)? {
                if contains {
                    return Ok(None);
                }
            } else {
                return Err(PyTypeError::new_err("`exclude` argument must be a set or dict."));
            }
        }

        if let Some(include) = include {
            if include.is_none() {
                // Do nothing; place this check at the top for performance in the common case
            } else if let Ok(include_dict) = include.downcast::<PyDict>() {
                let op_inc_value = merge_all_value(include_dict, py_key)?;

                if let Some(inc_value) = op_inc_value {
                    // if the index is in include, we definitely want to include this index
                    return if is_ellipsis_like(inc_value) {
                        Ok(Some((None, next_exclude)))
                    } else {
                        Ok(Some((Some(inc_value), next_exclude)))
                    };
                } else if !self.explicit_include(int_key) {
                    // if the index is not in include, include exists, AND it's not in schema include,
                    // this index should be omitted
                    return Ok(None);
                }
            } else if let Ok(include_set) = include.downcast::<PySet>() {
                if include_set.contains(py_key)? || include_set.contains(intern!(include_set.py(), "__all__"))? {
                    return Ok(Some((None, next_exclude)));
                } else if !self.explicit_include(int_key) {
                    // if the index is not in include, include exists, AND it's not in schema include,
                    // this index should be omitted
                    return Ok(None);
                }
            } else if let Some(contains) = check_contains(include, py_key)? {
                if contains {
                    return Ok(Some((None, next_exclude)));
                } else if !self.explicit_include(int_key) {
                    // if the index is not in include, include exists, AND it's not in schema include,
                    // this index should be omitted
                    return Ok(None);
                }
            } else {
                return Err(PyTypeError::new_err("`include` argument must be a set or dict."));
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

    pub fn index_filter<'py>(
        &self,
        index: usize,
        include: Option<&'py PyAny>,
        exclude: Option<&'py PyAny>,
    ) -> PyResult<Option<(Option<&'py PyAny>, Option<&'py PyAny>)>> {
        self.filter(index, index, include, exclude)
    }
}

/// if a `__contains__` method exists, call it with the key and `__all__`, and return the result
/// if it doesn't exist, or calling it fails (e.g. it's not a function), return `None`
fn check_contains(obj: &PyAny, py_key: impl ToPyObject + Copy) -> PyResult<Option<bool>> {
    let py = obj.py();
    match obj.getattr(intern!(py, "__contains__")) {
        Ok(contains_method) => {
            if let Ok(result) = contains_method.call1((py_key.to_object(py),)) {
                Ok(Some(
                    result.is_true()? || contains_method.call1((intern!(py, "__all__"),))?.is_true()?,
                ))
            } else {
                Ok(None)
            }
        }
        Err(_) => Ok(None),
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

/// detect both ellipsis and `True` to be compatible with pydantic V1
fn is_ellipsis_like(v: &PyAny) -> bool {
    v.is_ellipsis()
        || match v.downcast::<PyBool>() {
            Ok(b) => b.is_true(),
            Err(_) => false,
        }
}

/// lookup the dict, for the key and "__all__" key, and merge them following the same rules as pydantic V1
fn merge_all_value(dict: &PyDict, py_key: impl ToPyObject + Copy) -> PyResult<Option<&PyAny>> {
    let op_item_value = dict.get_item(py_key);
    let op_all_value = dict.get_item(intern!(dict.py(), "__all__"));

    match (op_item_value, op_all_value) {
        (Some(item_value), Some(all_value)) => {
            if is_ellipsis_like(item_value) || is_ellipsis_like(all_value) {
                Ok(op_item_value)
            } else {
                let item_dict = as_dict(item_value)?;
                let item_dict_merged = merge_dicts(item_dict, all_value)?;
                Ok(Some(item_dict_merged))
            }
        }
        (Some(_), None) => Ok(op_item_value),
        (None, Some(_)) => Ok(op_all_value),
        (None, None) => Ok(None),
    }
}

fn as_dict(value: &PyAny) -> PyResult<&PyDict> {
    if let Ok(dict) = value.downcast::<PyDict>() {
        dict.copy()
    } else if let Ok(set) = value.downcast::<PySet>() {
        let py = value.py();
        let dict = PyDict::new(py);
        for item in set {
            dict.set_item(item, py.Ellipsis())?;
        }
        Ok(dict)
    } else {
        Err(PyTypeError::new_err(
            "`include` and `exclude` must be of type `dict[str | int, <recursive> | ...] | set[str | int | ...]`",
        ))
    }
}

fn merge_dicts<'py>(item_dict: &'py PyDict, all_value: &'py PyAny) -> PyResult<&'py PyDict> {
    let item_dict = item_dict.copy()?;
    if let Ok(all_dict) = all_value.downcast::<PyDict>() {
        for (all_key, all_value) in all_dict {
            if let Some(item_value) = item_dict.get_item(all_key) {
                if is_ellipsis_like(item_value) {
                    continue;
                } else {
                    let item_value_dict = as_dict(item_value)?;
                    // if the all value is an ellipsis, we don't overwrite the item value
                    if !is_ellipsis_like(all_value) {
                        item_dict.set_item(all_key, merge_dicts(item_value_dict, all_value)?)?;
                    }
                }
            } else {
                item_dict.set_item(all_key, all_value)?;
            }
        }
    } else if let Ok(set) = all_value.downcast::<PySet>() {
        for item in set {
            if !item_dict.contains(item)? {
                item_dict.set_item(item, set.py().Ellipsis())?;
            }
        }
    } else {
        return Err(PyTypeError::new_err(
            "'__all__' key of `include` and `exclude` must be of type `dict[str | int, <recursive> | ...] | set[str | int | ...]`",
        ));
    }
    Ok(item_dict)
}
