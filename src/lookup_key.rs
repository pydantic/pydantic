use std::convert::Infallible;
use std::fmt;

use pyo3::exceptions::{PyAttributeError, PyTypeError};
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyMapping, PyString};
use pyo3::IntoPyObjectExt;

use jiter::{JsonObject, JsonValue};

use crate::build_tools::py_schema_err;
use crate::errors::{py_err_string, ErrorType, LocItem, Location, ToErrorValue, ValError, ValLineError, ValResult};
use crate::input::StringMapping;
use crate::tools::{extract_i64, py_err};

/// Used for getting items from python dicts, python objects, or JSON objects, in different ways
#[derive(Debug)]
pub(crate) enum LookupKey {
    /// simply look up a key in a dict, equivalent to `d.get(key)`
    Simple(LookupPath),
    /// look up a key by either string, equivalent to `d.get(choice1, d.get(choice2))`
    Choice { path1: LookupPath, path2: LookupPath },
    /// look up keys by one or more "paths" a path might be `['foo', 'bar']` to get `d.?foo.?bar`
    /// ints are also supported to index arrays/lists/tuples and dicts with int keys
    /// we reuse Location as the enum is the same, and the meaning is the same
    PathChoices(Vec<LookupPath>),
}

impl fmt::Display for LookupKey {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Simple(path) => write!(f, "'{key}'", key = path.first_key()),
            Self::Choice { path1, path2 } => write!(
                f,
                "'{key1}' | '{key2}'",
                key1 = path1.first_key(),
                key2 = path2.first_key()
            ),
            Self::PathChoices(paths) => write!(
                f,
                "{}",
                paths.iter().map(ToString::to_string).collect::<Vec<_>>().join(" | ")
            ),
        }
    }
}

impl LookupKey {
    pub fn from_py(py: Python, value: &Bound<'_, PyAny>, alt_alias: Option<&str>) -> PyResult<Self> {
        if let Ok(alias_py) = value.downcast::<PyString>() {
            let alias: String = alias_py.extract()?;
            let path1 = LookupPath::from_str(py, &alias, Some(alias_py.clone()));
            match alt_alias {
                Some(alt_alias) => Ok(Self::Choice {
                    path1,
                    path2: LookupPath::from_str(py, alt_alias, None),
                }),
                None => Ok(Self::Simple(path1)),
            }
        } else {
            let list = value.downcast::<PyList>()?;
            let first = match list.get_item(0) {
                Ok(v) => v,
                Err(_) => return py_schema_err!("Lookup paths should have at least one element"),
            };
            let mut locs: Vec<LookupPath> = if first.downcast::<PyString>().is_ok() {
                // list of strings rather than list of lists
                vec![LookupPath::from_list(list)?]
            } else {
                list.iter()
                    .map(|elem| LookupPath::from_list(&elem))
                    .collect::<PyResult<_>>()?
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

    fn simple(py: Python, key: &str, opt_py_key: Option<Bound<'_, PyString>>) -> Self {
        Self::Simple(LookupPath::from_str(py, key, opt_py_key))
    }

    pub fn py_get_dict_item<'py, 's>(
        &'s self,
        dict: &Bound<'py, PyDict>,
    ) -> ValResult<Option<(&'s LookupPath, Bound<'py, PyAny>)>> {
        match self {
            Self::Simple(path) => match dict.get_item(&path.first_item.py_key)? {
                Some(value) => {
                    debug_assert!(path.rest.is_empty());
                    Ok(Some((path, value)))
                }
                None => Ok(None),
            },
            Self::Choice { path1, path2, .. } => match dict.get_item(&path1.first_item.py_key)? {
                Some(value) => {
                    debug_assert!(path1.rest.is_empty());
                    Ok(Some((path1, value)))
                }
                None => match dict.get_item(&path2.first_item.py_key)? {
                    Some(value) => {
                        debug_assert!(path2.rest.is_empty());
                        Ok(Some((path2, value)))
                    }
                    None => Ok(None),
                },
            },
            Self::PathChoices(path_choices) => {
                for path in path_choices {
                    let Some(first_value) = dict.get_item(&path.first_item.py_key)? else {
                        continue;
                    };
                    // iterate over the path and plug each value into the py_any from the last step,
                    // this could just be a loop but should be somewhat faster with a functional design
                    if let Some(v) = path.rest.iter().try_fold(first_value, |d, loc| loc.py_get_item(&d)) {
                        // Successfully found an item, return it
                        return Ok(Some((path, v)));
                    }
                }
                // got to the end of path_choices, without a match, return None
                Ok(None)
            }
        }
    }

    pub fn py_get_string_mapping_item<'py, 's>(
        &'s self,
        dict: &Bound<'py, PyDict>,
    ) -> ValResult<Option<(&'s LookupPath, StringMapping<'py>)>> {
        if let Some((path, py_any)) = self.py_get_dict_item(dict)? {
            let value = StringMapping::new_value(py_any)?;
            Ok(Some((path, value)))
        } else {
            Ok(None)
        }
    }

    pub fn py_get_mapping_item<'py, 's>(
        &'s self,
        dict: &Bound<'py, PyMapping>,
    ) -> ValResult<Option<(&'s LookupPath, Bound<'py, PyAny>)>> {
        match self {
            Self::Simple(path) => match dict.get_item(&path.first_item.py_key) {
                Ok(value) => {
                    debug_assert!(path.rest.is_empty());
                    Ok(Some((path, value)))
                }
                _ => Ok(None),
            },
            Self::Choice { path1, path2, .. } => match dict.get_item(&path1.first_item.py_key) {
                Ok(value) => {
                    debug_assert!(path1.rest.is_empty());
                    Ok(Some((path1, value)))
                }
                _ => match dict.get_item(&path2.first_item.py_key) {
                    Ok(value) => {
                        debug_assert!(path2.rest.is_empty());
                        Ok(Some((path2, value)))
                    }
                    _ => Ok(None),
                },
            },
            Self::PathChoices(path_choices) => {
                for path in path_choices {
                    let Some(first_value) = dict.get_item(&path.first_item.py_key).ok() else {
                        continue;
                    };
                    // iterate over the path and plug each value into the py_any from the last step,
                    // this could just be a loop but should be somewhat faster with a functional design
                    if let Some(v) = path.rest.iter().try_fold(first_value, |d, loc| loc.py_get_item(&d)) {
                        // Successfully found an item, return it
                        return Ok(Some((path, v)));
                    }
                }
                // got to the end of path_choices, without a match, return None
                Ok(None)
            }
        }
    }

    pub fn simple_py_get_attr<'py, 's>(
        &'s self,
        obj: &Bound<'py, PyAny>,
    ) -> PyResult<Option<(&'s LookupPath, Bound<'py, PyAny>)>> {
        match self {
            Self::Simple(path) => match py_get_attrs(obj, &path.first_item.py_key)? {
                Some(value) => {
                    debug_assert!(path.rest.is_empty());
                    Ok(Some((path, value)))
                }
                None => Ok(None),
            },
            Self::Choice { path1, path2, .. } => match py_get_attrs(obj, &path1.first_item.py_key)? {
                Some(value) => {
                    debug_assert!(path1.rest.is_empty());
                    Ok(Some((path1, value)))
                }
                None => match py_get_attrs(obj, &path2.first_item.py_key)? {
                    Some(value) => {
                        debug_assert!(path2.rest.is_empty());
                        Ok(Some((path2, value)))
                    }
                    None => Ok(None),
                },
            },
            Self::PathChoices(path_choices) => {
                'outer: for path in path_choices {
                    // similar to above, but using `py_get_attrs`, we can't use try_fold because of the extra Err
                    // so we have to loop manually
                    let Some(mut v) = path.first_item.py_get_attrs(obj)? else {
                        continue;
                    };
                    for loc in &path.rest {
                        v = match loc.py_get_attrs(&v) {
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

    pub fn py_get_attr<'py, 's>(
        &'s self,
        obj: &Bound<'py, PyAny>,
        kwargs: Option<&Bound<'py, PyDict>>,
    ) -> ValResult<Option<(&'s LookupPath, Bound<'py, PyAny>)>> {
        if let Some(dict) = kwargs {
            if let Ok(Some(item)) = self.py_get_dict_item(dict) {
                return Ok(Some(item));
            }
        }

        match self.simple_py_get_attr(obj) {
            Ok(v) => Ok(v),
            Err(err) => {
                let error = py_err_string(obj.py(), err);
                Err(ValError::new(
                    ErrorType::GetAttributeError { error, context: None },
                    obj,
                ))
            }
        }
    }

    pub fn json_get<'a, 'data, 's>(
        &'s self,
        dict: &'a JsonObject<'data>,
    ) -> ValResult<Option<(&'s LookupPath, &'a JsonValue<'data>)>> {
        // FIXME: use of find_map in here probably leads to quadratic complexity
        match self {
            Self::Simple(path) => match dict
                .iter()
                .rev()
                .find_map(|(k, v)| (k == path.first_key()).then_some(v))
            {
                Some(value) => {
                    debug_assert!(path.rest.is_empty());
                    Ok(Some((path, value)))
                }
                None => Ok(None),
            },
            Self::Choice { path1, path2 } => match dict
                .iter()
                .rev()
                .find_map(|(k, v)| (k == path1.first_key()).then_some(v))
            {
                Some(value) => {
                    debug_assert!(path1.rest.is_empty());
                    Ok(Some((path1, value)))
                }
                None => match dict
                    .iter()
                    .rev()
                    .find_map(|(k, v)| (k == path2.first_key()).then_some(v))
                {
                    Some(value) => {
                        debug_assert!(path2.rest.is_empty());
                        Ok(Some((path2, value)))
                    }
                    None => Ok(None),
                },
            },
            Self::PathChoices(path_choices) => {
                for path in path_choices {
                    // first step is different from the rest as we already know dict is JsonObject
                    // because of above checks, we know that path should have at least one element, hence unwrap
                    let v: &JsonValue = match dict
                        .iter()
                        .rev()
                        .find_map(|(k, v)| (k == path.first_key()).then_some(v))
                    {
                        Some(v) => v,
                        None => continue,
                    };

                    let mut path_iter = path.rest.iter();

                    // similar to above
                    // iterate over the path and plug each value into the JsonValue from the last step, starting with v
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

    pub fn error(
        &self,
        error_type: ErrorType,
        input: impl ToErrorValue,
        loc_by_alias: bool,
        field_name: &str,
    ) -> ValLineError {
        if loc_by_alias {
            let lookup_path = match self {
                Self::Simple(path, ..) => path,
                Self::Choice { path1, .. } => path1,
                Self::PathChoices(paths) => paths.first().unwrap(),
            };

            let mut location = Vec::with_capacity(1 + lookup_path.rest.len());
            for item in lookup_path.rest.iter().rev() {
                location.push(item.to_loc_item());
            }
            location.push(LocItem::from(&lookup_path.first_item.key));

            ValLineError::new_with_full_loc(error_type, input, Location::List(location))
        } else {
            ValLineError::new_with_loc(error_type, input, field_name.to_string())
        }
    }
}

#[derive(Debug)]
pub(crate) struct LookupPath {
    /// All paths must start with a string key
    first_item: PathItemString,
    /// Most paths will have no extra items, though some do so we encode this here
    rest: Vec<PathItem>,
}

impl fmt::Display for LookupPath {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{first_key}", first_key = &self.first_item)?;
        for item in &self.rest {
            write!(f, ".{item}")?;
        }
        Ok(())
    }
}

impl LookupPath {
    fn from_str(py: Python, key: &str, py_key: Option<Bound<'_, PyString>>) -> Self {
        let py_key = match py_key {
            Some(py_key) => py_key,
            None => PyString::new(py, key),
        };
        Self {
            first_item: PathItemString {
                key: key.to_string(),
                py_key: py_key.clone().unbind(),
            },
            rest: Vec::new(),
        }
    }

    fn from_list(obj: &Bound<'_, PyAny>) -> PyResult<LookupPath> {
        let mut iter = obj.downcast::<PyList>()?.iter();

        let Some(first_item) = iter.next() else {
            return py_schema_err!("Each alias path should have at least one element");
        };

        let Ok(first_item_py_str) = first_item.downcast_into::<PyString>() else {
            return py_err!(PyTypeError; "The first item in an alias path should be a string");
        };

        let first_item = PathItemString {
            key: first_item_py_str.to_str()?.to_owned(),
            py_key: first_item_py_str.clone().unbind(),
        };

        let rest = iter.map(PathItem::from_py).collect::<PyResult<_>>()?;

        Ok(Self { first_item, rest })
    }

    pub fn apply_error_loc(&self, mut line_error: ValLineError, loc_by_alias: bool, field_name: &str) -> ValLineError {
        if loc_by_alias {
            for path_item in self.rest.iter().rev() {
                line_error = line_error.with_outer_location(path_item.to_loc_item());
            }
            line_error = line_error.with_outer_location(&self.first_item.key);
            line_error
        } else {
            line_error.with_outer_location(field_name)
        }
    }

    /// get the `str` from the first item in the path, note paths always have length > 0, and the first item
    /// is always a string
    pub fn first_key(&self) -> &str {
        &self.first_item.key
    }
}

#[derive(Debug, Clone)]
pub(crate) enum PathItem {
    S(PathItemString),
    /// integer key, used to get items from a list, tuple OR a dict with int keys `dict[int, ...]` (python only)
    Pos(usize),
    Neg(usize),
}

/// string type key, used to get or identify items from a dict or anything that implements `__getitem__`
/// we store both the string and pystring to save creating the pystring for python
#[derive(Debug, Clone)]
pub(crate) struct PathItemString {
    key: String,
    py_key: Py<PyString>,
}

impl fmt::Display for PathItem {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::S(key) => key.fmt(f),
            Self::Pos(key) => write!(f, "{key}"),
            Self::Neg(key) => write!(f, "-{key}"),
        }
    }
}

impl fmt::Display for PathItemString {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "'{key}'", key = &self.key)
    }
}

impl<'py> IntoPyObject<'py> for &'_ PathItem {
    type Target = PyAny;
    type Output = Bound<'py, PyAny>;
    type Error = PyErr;

    fn into_pyobject(self, py: Python<'py>) -> Result<Self::Output, Self::Error> {
        match self {
            PathItem::S(path_item_string) => path_item_string.into_bound_py_any(py),
            PathItem::Pos(val) => val.into_bound_py_any(py),
            PathItem::Neg(val) => {
                let neg_value = -(*val as i64);
                neg_value.into_bound_py_any(py)
            }
        }
    }
}

impl<'a, 'py> IntoPyObject<'py> for &'a PathItemString {
    type Target = PyString;
    type Output = Borrowed<'a, 'py, PyString>;
    type Error = Infallible;

    fn into_pyobject(self, py: Python<'py>) -> Result<Self::Output, Self::Error> {
        Ok(self.py_key.bind_borrowed(py))
    }
}

impl PathItem {
    pub fn from_py(obj: Bound<'_, PyAny>) -> PyResult<Self> {
        let obj = match obj.downcast_into::<PyString>() {
            Ok(py_str_key) => {
                let str_key = py_str_key.to_str()?.to_string();
                return Ok(Self::S(PathItemString {
                    key: str_key,
                    py_key: py_str_key.unbind(),
                }));
            }
            Err(e) => e.into_inner(),
        };

        if let Ok(usize_key) = obj.extract::<usize>() {
            Ok(Self::Pos(usize_key))
        } else if let Some(int_key) = extract_i64(&obj) {
            Ok(Self::Neg(int_key.unsigned_abs() as usize))
        } else {
            py_err!(PyTypeError; "Item in an alias path should be a string or int")
        }
    }

    pub fn py_get_item<'py>(&self, py_any: &Bound<'py, PyAny>) -> Option<Bound<'py, PyAny>> {
        // we definitely don't want to index strings, so explicitly omit this case
        if py_any.downcast::<PyString>().is_ok() {
            None
        } else {
            // otherwise, blindly try getitem on v since no better logic is realistic
            py_any.get_item(self).ok()
        }
    }

    pub fn py_get_attrs<'py>(&self, obj: &Bound<'py, PyAny>) -> PyResult<Option<Bound<'py, PyAny>>> {
        match self {
            Self::S(path_item_string) => path_item_string.py_get_attrs(obj),
            // int, we fall back to py_get_item - e.g. we want to use get_item for a list, tuple, dict, etc.
            _ => Ok(self.py_get_item(obj)),
        }
    }

    pub fn json_get<'a, 'data>(&self, any_json: &'a JsonValue<'data>) -> Option<&'a JsonValue<'data>> {
        match any_json {
            JsonValue::Object(v_obj) => self.json_obj_get(v_obj),
            JsonValue::Array(v_array) => match self {
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

    pub fn json_obj_get<'a, 'data>(&self, json_obj: &'a JsonObject<'data>) -> Option<&'a JsonValue<'data>> {
        match self {
            Self::S(PathItemString { key, .. }) => json_obj.iter().rev().find_map(|(k, v)| (k == key).then_some(v)),
            _ => None,
        }
    }

    fn to_loc_item(&self) -> LocItem {
        match self {
            Self::S(PathItemString { key, .. }) => LocItem::from(key),
            Self::Pos(index) => LocItem::from(*index),
            Self::Neg(index) => LocItem::from(-(*index as i64)),
        }
    }
}

impl PathItemString {
    fn py_get_attrs<'py>(&self, obj: &Bound<'py, PyAny>) -> PyResult<Option<Bound<'py, PyAny>>> {
        // if obj is a dict, we want to use get_item, not getattr
        if obj.downcast::<PyDict>().is_ok() {
            Ok(py_get_item(obj, self))
        } else {
            py_get_attrs(obj, &self.py_key)
        }
    }
}

/// wrapper around `getitem` that excludes string indexing `None` for strings
fn py_get_item<'py>(py_any: &Bound<'py, PyAny>, index: impl IntoPyObject<'py>) -> Option<Bound<'py, PyAny>> {
    // we definitely don't want to index strings, so explicitly omit this case
    if py_any.is_instance_of::<PyString>() {
        None
    } else {
        // otherwise, blindly try getitem on v since no better logic is realistic
        py_any.get_item(index).ok()
    }
}

/// wrapper around `getattr` that returns `Ok(None)` for attribute errors, but returns other errors
/// We don't check `try_from_attributes` because that check was performed on the top level object before we got here
fn py_get_attrs<'py>(obj: &Bound<'py, PyAny>, attr_name: &Py<PyString>) -> PyResult<Option<Bound<'py, PyAny>>> {
    match obj.getattr(attr_name) {
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

#[derive(Debug)]
#[allow(clippy::struct_field_names)]
pub struct LookupKeyCollection {
    by_name: LookupKey,
    by_alias: Option<LookupKey>,
    by_alias_then_name: Option<LookupKey>,
}

impl LookupKeyCollection {
    pub fn new(py: Python, validation_alias: Option<Bound<'_, PyAny>>, field_name: &str) -> PyResult<Self> {
        let by_name = LookupKey::from_string(py, field_name);

        if let Some(va) = validation_alias {
            let by_alias = Some(LookupKey::from_py(py, &va, None)?);
            let by_alias_then_name = Some(LookupKey::from_py(py, &va, Some(field_name))?);
            Ok(Self {
                by_name,
                by_alias,
                by_alias_then_name,
            })
        } else {
            Ok(Self {
                by_name,
                by_alias: None,
                by_alias_then_name: None,
            })
        }
    }

    pub fn select(&self, validate_by_alias: bool, validate_by_name: bool) -> PyResult<&LookupKey> {
        let lookup_key_selection = match (validate_by_alias, validate_by_name) {
            (true, true) => self.by_alias_then_name.as_ref().unwrap_or(&self.by_name),
            (true, false) => self.by_alias.as_ref().unwrap_or(&self.by_name),
            (false, true) => &self.by_name,
            (false, false) => {
                // Note: we shouldn't hit this branch much, as this is enforced in `pydantic` with a `PydanticUserError`
                // at config creation time / validation function call time.
                return py_schema_err!("`validate_by_name` and `validate_by_alias` cannot both be set to `False`.");
            }
        };
        Ok(lookup_key_selection)
    }
}
