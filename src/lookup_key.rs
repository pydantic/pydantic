use core::slice::Iter;
use std::fmt;

use pyo3::exceptions::{PyAttributeError, PyTypeError};
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyMapping, PyString};

use crate::build_tools::py_schema_err;
use crate::errors::{ErrorType, ValLineError};
use crate::input::{Input, JsonInput, JsonObject};
use crate::tools::{extract_i64, py_err};

/// Used for getting items from python dicts, python objects, or JSON objects, in different ways
#[derive(Debug, Clone)]
pub(crate) enum LookupKey {
    /// simply look up a key in a dict, equivalent to `d.get(key)`
    /// we save both the string and pystring to save creating the pystring for python
    Simple {
        key: String,
        py_key: Py<PyString>,
        path: LookupPath,
    },
    /// look up a key by either string, equivalent to `d.get(choice1, d.get(choice2))`
    Choice {
        key1: String,
        py_key1: Py<PyString>,
        path1: LookupPath,
        key2: String,
        py_key2: Py<PyString>,
        path2: LookupPath,
    },
    /// look up keys by one or more "paths" a path might be `['foo', 'bar']` to get `d.?foo.?bar`
    /// ints are also supported to index arrays/lists/tuples and dicts with int keys
    /// we reuse Location as the enum is the same, and the meaning is the same
    PathChoices(Vec<LookupPath>),
}

impl fmt::Display for LookupKey {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Simple { key, .. } => write!(f, "'{key}'"),
            Self::Choice { key1, key2, .. } => write!(f, "'{key1}' | '{key2}'"),
            Self::PathChoices(paths) => write!(
                f,
                "{}",
                paths.iter().map(ToString::to_string).collect::<Vec<_>>().join(" | ")
            ),
        }
    }
}

macro_rules! py_string {
    ($py:ident, $str:expr) => {
        PyString::intern($py, $str).into()
    };
}

impl LookupKey {
    pub fn from_py(py: Python, value: &PyAny, alt_alias: Option<&str>) -> PyResult<Self> {
        if let Ok(alias_py) = value.downcast::<PyString>() {
            let alias: &str = alias_py.extract()?;
            match alt_alias {
                Some(alt_alias) => Ok(Self::Choice {
                    key1: alias.to_string(),
                    py_key1: alias_py.into_py(py),
                    path1: LookupPath::from_str(py, alias, Some(alias_py)),
                    key2: alt_alias.to_string(),
                    py_key2: py_string!(py, alt_alias),
                    path2: LookupPath::from_str(py, alt_alias, None),
                }),
                None => Ok(Self::simple(py, alias, Some(alias_py))),
            }
        } else {
            let list: &PyList = value.downcast()?;
            let first = match list.get_item(0) {
                Ok(v) => v,
                Err(_) => return py_schema_err!("Lookup paths should have at least one element"),
            };
            let mut locs: Vec<LookupPath> = if first.downcast::<PyString>().is_ok() {
                // list of strings rather than list of lists
                vec![LookupPath::from_list(list)?]
            } else {
                list.iter().map(LookupPath::from_list).collect::<PyResult<_>>()?
            };

            if let Some(alt_alias) = alt_alias {
                locs.push(LookupPath::from_str(py, alt_alias, None));
            }
            Ok(Self::PathChoices(locs))
        }
    }

    pub fn from_string(py: Python, key: &str) -> Self {
        Self::simple(py, key, None)
    }

    fn simple(py: Python, key: &str, opt_py_key: Option<&PyString>) -> Self {
        let py_key = match opt_py_key {
            Some(py_key) => py_key.into_py(py),
            None => py_string!(py, key),
        };
        Self::Simple {
            key: key.to_string(),
            py_key,
            path: LookupPath::from_str(py, key, opt_py_key),
        }
    }

    pub fn py_get_dict_item<'data, 's>(
        &'s self,
        dict: &'data PyDict,
    ) -> PyResult<Option<(&'s LookupPath, &'data PyAny)>> {
        match self {
            Self::Simple { py_key, path, .. } => match dict.get_item(py_key) {
                Some(value) => Ok(Some((path, value))),
                None => Ok(None),
            },
            Self::Choice {
                py_key1,
                path1,
                py_key2,
                path2,
                ..
            } => match dict.get_item(py_key1) {
                Some(value) => Ok(Some((path1, value))),
                None => match dict.get_item(py_key2) {
                    Some(value) => Ok(Some((path2, value))),
                    None => Ok(None),
                },
            },
            Self::PathChoices(path_choices) => {
                for path in path_choices {
                    // iterate over the path and plug each value into the py_any from the last step, starting with dict
                    // this could just be a loop but should be somewhat faster with a functional design
                    if let Some(v) = path.iter().try_fold(dict as &PyAny, |d, loc| loc.py_get_item(d)) {
                        // Successfully found an item, return it
                        return Ok(Some((path, v)));
                    }
                }
                // got to the end of path_choices, without a match, return None
                Ok(None)
            }
        }
    }

    pub fn py_get_mapping_item<'data, 's>(
        &'s self,
        dict: &'data PyMapping,
    ) -> PyResult<Option<(&'s LookupPath, &'data PyAny)>> {
        match self {
            Self::Simple { py_key, path, .. } => match dict.get_item(py_key) {
                Ok(value) => Ok(Some((path, value))),
                _ => Ok(None),
            },
            Self::Choice {
                py_key1,
                path1,
                py_key2,
                path2,
                ..
            } => match dict.get_item(py_key1) {
                Ok(value) => Ok(Some((path1, value))),
                _ => match dict.get_item(py_key2) {
                    Ok(value) => Ok(Some((path2, value))),
                    _ => Ok(None),
                },
            },
            Self::PathChoices(path_choices) => {
                for path in path_choices {
                    // iterate over the path and plug each value into the py_any from the last step, starting with dict
                    // this could just be a loop but should be somewhat faster with a functional design
                    if let Some(v) = path.iter().try_fold(dict as &PyAny, |d, loc| loc.py_get_item(d)) {
                        // Successfully found an item, return it
                        return Ok(Some((path, v)));
                    }
                }
                // got to the end of path_choices, without a match, return None
                Ok(None)
            }
        }
    }

    pub fn py_get_attr<'data, 's>(
        &'s self,
        obj: &'data PyAny,
        kwargs: Option<&'data PyDict>,
    ) -> PyResult<Option<(&'s LookupPath, &'data PyAny)>> {
        if let Some(dict) = kwargs {
            if let Ok(Some(item)) = self.py_get_dict_item(dict) {
                return Ok(Some(item));
            }
        }

        match self {
            Self::Simple { py_key, path, .. } => match py_get_attrs(obj, py_key)? {
                Some(value) => Ok(Some((path, value))),
                None => Ok(None),
            },
            Self::Choice {
                py_key1,
                path1,
                py_key2,
                path2,
                ..
            } => match py_get_attrs(obj, py_key1)? {
                Some(value) => Ok(Some((path1, value))),
                None => match py_get_attrs(obj, py_key2)? {
                    Some(value) => Ok(Some((path2, value))),
                    None => Ok(None),
                },
            },
            Self::PathChoices(path_choices) => {
                'outer: for path in path_choices {
                    // similar to above, but using `py_get_attrs`, we can't use try_fold because of the extra Err
                    // so we have to loop manually
                    let mut v = obj;
                    for loc in path.iter() {
                        v = match loc.py_get_attrs(v) {
                            Ok(Some(v)) => v,
                            Ok(None) => {
                                continue 'outer;
                            }
                            Err(e) => return Err(e),
                        }
                    }
                    // Successfully found an item, return it
                    return Ok(Some((path, v)));
                }
                // got to the end of path_choices, without a match, return None
                Ok(None)
            }
        }
    }

    pub fn json_get<'data, 's>(
        &'s self,
        dict: &'data JsonObject,
    ) -> PyResult<Option<(&'s LookupPath, &'data JsonInput)>> {
        match self {
            Self::Simple { key, path, .. } => match dict.get(key) {
                Some(value) => Ok(Some((path, value))),
                None => Ok(None),
            },
            Self::Choice {
                key1,
                path1,
                key2,
                path2,
                ..
            } => match dict.get(key1) {
                Some(value) => Ok(Some((path1, value))),
                None => match dict.get(key2) {
                    Some(value) => Ok(Some((path2, value))),
                    None => Ok(None),
                },
            },
            Self::PathChoices(path_choices) => {
                for path in path_choices {
                    let mut path_iter = path.iter();

                    // first step is different from the rest as we already know dict is JsonObject
                    // because of above checks, we know that path should have at least one element, hence unwrap
                    let v: &JsonInput = match path_iter.next().unwrap().json_obj_get(dict) {
                        Some(v) => v,
                        None => continue,
                    };

                    // similar to above
                    // iterate over the path and plug each value into the JsonInput from the last step, starting with v
                    // from the first step, this could just be a loop but should be somewhat faster with a functional design
                    if let Some(v) = path_iter.try_fold(v, |d, loc| loc.json_get(d)) {
                        // Successfully found an item, return it
                        return Ok(Some((path, v)));
                    }
                }
                // got to the end of path_choices, without a match, return None
                Ok(None)
            }
        }
    }

    pub fn error<'d>(
        &self,
        error_type: ErrorType,
        input: &'d impl Input<'d>,
        loc_by_alias: bool,
        field_name: &str,
    ) -> ValLineError<'d> {
        if loc_by_alias {
            let lookup_path = match self {
                Self::Simple { path, .. } => path,
                Self::Choice { path1, .. } => path1,
                Self::PathChoices(paths) => paths.first().unwrap(),
            };
            ValLineError::new_with_full_loc(error_type, input, lookup_path.into())
        } else {
            ValLineError::new_with_loc(error_type, input, field_name.to_string())
        }
    }
}

#[derive(Debug, Clone)]
pub(crate) struct LookupPath(Vec<PathItem>);

impl fmt::Display for LookupPath {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        for (i, item) in self.0.iter().enumerate() {
            if i != 0 {
                write!(f, ".")?;
            }
            write!(f, "{item}")?;
        }
        Ok(())
    }
}

impl LookupPath {
    fn from_str(py: Python, key: &str, py_key: Option<&PyString>) -> Self {
        let py_key = match py_key {
            Some(py_key) => py_key.into_py(py),
            None => py_string!(py, key),
        };
        Self(vec![PathItem::S(key.to_string(), py_key)])
    }

    fn from_list(obj: &PyAny) -> PyResult<LookupPath> {
        let v = obj
            .extract::<&PyList>()?
            .iter()
            .enumerate()
            .map(|(index, obj)| PathItem::from_py(index, obj))
            .collect::<PyResult<Vec<PathItem>>>()?;

        if v.is_empty() {
            py_schema_err!("Each alias path should have at least one element")
        } else {
            Ok(Self(v))
        }
    }

    pub fn apply_error_loc<'a>(
        &self,
        mut line_error: ValLineError<'a>,
        loc_by_alias: bool,
        field_name: &str,
    ) -> ValLineError<'a> {
        if loc_by_alias {
            for path_item in self.iter().rev() {
                line_error = line_error.with_outer_location(path_item.clone().into());
            }
            line_error
        } else {
            line_error.with_outer_location(field_name.to_string().into())
        }
    }

    pub fn iter(&self) -> Iter<PathItem> {
        self.0.iter()
    }

    /// get the `str` from the first item in the path, note paths always have length > 0, and the first item
    /// is always a string
    pub fn first_key(&self) -> &str {
        self.0.first().unwrap().get_key()
    }
}

#[derive(Debug, Clone)]
pub(crate) enum PathItem {
    /// string type key, used to get or identify items from a dict or anything that implements `__getitem__`
    /// as above we store both the string and pystring to save creating the pystring for python
    S(String, Py<PyString>),
    /// integer key, used to get items from a list, tuple OR a dict with int keys `Dict[int, ...]` (python only)
    Pos(usize),
    Neg(usize),
}

impl fmt::Display for PathItem {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::S(key, _) => write!(f, "'{key}'"),
            Self::Pos(key) => write!(f, "{key}"),
            Self::Neg(key) => write!(f, "-{key}"),
        }
    }
}

impl ToPyObject for PathItem {
    fn to_object(&self, py: Python<'_>) -> PyObject {
        match self {
            Self::S(_, val) => val.to_object(py),
            Self::Pos(val) => val.to_object(py),
            Self::Neg(val) => {
                let neg_value = -(*val as i64);
                neg_value.to_object(py)
            }
        }
    }
}

impl PathItem {
    pub fn from_py(index: usize, obj: &PyAny) -> PyResult<Self> {
        if let Ok(py_str_key) = obj.downcast::<PyString>() {
            let str_key = py_str_key.to_str()?.to_string();
            Ok(Self::S(str_key, py_str_key.into()))
        } else if let Ok(usize_key) = obj.extract::<usize>() {
            if index == 0 {
                py_err!(PyTypeError; "The first item in an alias path should be a string")
            } else {
                Ok(Self::Pos(usize_key))
            }
        } else if let Ok(int_key) = extract_i64(obj) {
            if index == 0 {
                py_err!(PyTypeError; "The first item in an alias path should be a string")
            } else {
                Ok(Self::Neg(int_key.unsigned_abs() as usize))
            }
        } else {
            py_err!(PyTypeError; "Item in an alias path should be a string or int")
        }
    }

    pub fn py_get_item<'a>(&self, py_any: &'a PyAny) -> Option<&'a PyAny> {
        // we definitely don't want to index strings, so explicitly omit this case
        if py_any.downcast::<PyString>().is_ok() {
            None
        } else {
            // otherwise, blindly try getitem on v since no better logic is realistic
            py_any.get_item(self).ok()
        }
    }

    pub fn get_key(&self) -> &str {
        match self {
            Self::S(key, _) => key.as_str(),
            _ => unreachable!(),
        }
    }

    pub fn py_get_attrs<'a>(&self, obj: &'a PyAny) -> PyResult<Option<&'a PyAny>> {
        match self {
            Self::S(_, py_key) => {
                // if obj is a dict, we want to use get_item, not getattr
                if obj.downcast::<PyDict>().is_ok() {
                    Ok(self.py_get_item(obj))
                } else {
                    py_get_attrs(obj, py_key)
                }
            }
            // int, we fall back to py_get_item - e.g. we want to use get_item for a list, tuple, dict, etc.
            _ => Ok(self.py_get_item(obj)),
        }
    }

    pub fn json_get<'a>(&self, any_json: &'a JsonInput) -> Option<&'a JsonInput> {
        match any_json {
            JsonInput::Object(v_obj) => self.json_obj_get(v_obj),
            JsonInput::Array(v_array) => match self {
                Self::Pos(index) => v_array.get(*index),
                Self::Neg(index) => {
                    if let Some(index) = v_array.len().checked_sub(*index) {
                        v_array.get(index)
                    } else {
                        None
                    }
                }
                Self::S(..) => None,
            },
            _ => None,
        }
    }

    pub fn json_obj_get<'a>(&self, json_obj: &'a JsonObject) -> Option<&'a JsonInput> {
        match self {
            Self::S(key, _) => json_obj.get(key),
            _ => None,
        }
    }
}

/// wrapper around `getattr` that returns `Ok(None)` for attribute errors, but returns other errors
/// We don't check `try_from_attributes` because that check was performed on the top level object before we got here
fn py_get_attrs<'a>(obj: &'a PyAny, attr_name: &Py<PyString>) -> PyResult<Option<&'a PyAny>> {
    match obj.getattr(attr_name.extract::<&PyString>(obj.py())?) {
        Ok(attr) => Ok(Some(attr)),
        Err(err) => {
            if err.get_type(obj.py()).is_subclass_of::<PyAttributeError>()? {
                Ok(None)
            } else {
                Err(err)
            }
        }
    }
}
