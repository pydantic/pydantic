use std::borrow::Borrow;
use std::convert::Infallible;
use std::fmt;

use pyo3::IntoPyObjectExt;
use pyo3::exceptions::{PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::pybacked::PyBackedStr;
use pyo3::types::{PyDict, PyList, PyMapping, PyString};

use jiter::{JsonObject, JsonValue};

use crate::build_tools::py_schema_err;
use crate::errors::{ErrorType, LocItem, Location, ToErrorValue, ValError, ValLineError, ValResult, py_err_string};
use crate::input::StringMapping;
use crate::tools::{mapping_get, py_err};

/// Used for getting items from python dicts, python objects, or JSON objects, in different ways
#[derive(Debug)]
pub(crate) enum LookupKey {
    /// simply look up a key in a dict, equivalent to `d.get(key)`
    Simple(LookupPath),
    /// look up keys by one or more "paths" a path might be `['foo', 'bar']` to get `d.?foo.?bar`
    /// ints are also supported to index arrays/lists/tuples and dicts with int keys
    /// we reuse Location as the enum is the same, and the meaning is the same
    PathChoices(Vec<LookupPath>),
}

impl fmt::Display for LookupKey {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Simple(path) => write!(f, "'{key}'", key = path.first_key()),
            Self::PathChoices(paths) => write!(
                f,
                "{}",
                paths.iter().map(ToString::to_string).collect::<Vec<_>>().join(" | ")
            ),
        }
    }
}

impl LookupKey {
    pub fn from_py(value: &Bound<'_, PyAny>) -> PyResult<Self> {
        if let Ok(alias_py) = value.cast::<PyString>() {
            let path1 = LookupPath::from_str(alias_py.clone())?;
            Ok(Self::Simple(path1))
        } else {
            let list = value.cast::<PyList>()?;
            let Ok(first) = list.get_item(0) else {
                return py_schema_err!("Lookup paths should have at least one element");
            };
            let locs: Vec<LookupPath> = if first.cast::<PyString>().is_ok() {
                // list of strings rather than list of lists
                vec![LookupPath::from_list(list)?]
            } else {
                list.iter()
                    .map(|elem| LookupPath::from_list(&elem))
                    .collect::<PyResult<_>>()?
            };
            Ok(Self::PathChoices(locs))
        }
    }

    pub fn py_get_dict_item<'py, 's>(
        &'s self,
        dict: &Bound<'py, PyDict>,
    ) -> PyResult<Option<(&'s LookupPath, Bound<'py, PyAny>)>> {
        self.get_impl(dict, PyDictMethods::get_item, |d, loc| Ok(loc.py_get_item(&d)))
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
    ) -> PyResult<Option<(&'s LookupPath, Bound<'py, PyAny>)>> {
        self.get_impl(dict, mapping_get, |d, loc| Ok(loc.py_get_item(&d)))
    }

    pub fn simple_py_get_attr<'py, 's>(
        &'s self,
        obj: &Bound<'py, PyAny>,
    ) -> PyResult<Option<(&'s LookupPath, Bound<'py, PyAny>)>> {
        self.get_impl(obj, PyAnyMethods::getattr_opt, |d, loc| loc.py_get_attrs(&d))
    }

    pub fn py_get_attr<'py, 's>(
        &'s self,
        obj: &Bound<'py, PyAny>,
        kwargs: Option<&Bound<'py, PyDict>>,
    ) -> ValResult<Option<(&'s LookupPath, Bound<'py, PyAny>)>> {
        if let Some(dict) = kwargs
            && let Ok(Some(item)) = self.py_get_dict_item(dict)
        {
            return Ok(Some(item));
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

    fn get_impl<'s, 'a, SourceT, OutputT: 'a>(
        &'s self,
        source: &'a SourceT,
        lookup: impl Fn(&'a SourceT, &'s PathItemString) -> PyResult<Option<OutputT>>,
        nested_lookup: impl Fn(OutputT, &'s PathItem) -> PyResult<Option<OutputT>>,
    ) -> PyResult<Option<(&'s LookupPath, OutputT)>> {
        match self {
            Self::Simple(path) => match lookup(source, &path.first_item)? {
                Some(value) => {
                    debug_assert!(path.rest.is_empty());
                    Ok(Some((path, value)))
                }
                None => Ok(None),
            },
            Self::PathChoices(path_choices) => {
                'choices: for path in path_choices {
                    let Some(mut value) = lookup(source, &path.first_item)? else {
                        continue;
                    };

                    // iterate over the path and plug each value into the value from the last step
                    for loc in &path.rest {
                        value = match nested_lookup(value, loc) {
                            Ok(Some(v)) => v,
                            // this choice did not match, try the next one
                            Ok(None) => continue 'choices,
                            Err(e) => return Err(e),
                        }
                    }
                    // Successfully found an item, return it
                    return Ok(Some((path, value)));
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
                Self::PathChoices(paths) => paths.first().unwrap(),
            };

            let mut location = Vec::with_capacity(1 + lookup_path.rest.len());
            for item in lookup_path.rest.iter().rev() {
                location.push(item.to_loc_item());
            }
            location.push(LocItem::from(lookup_path.first_item.0.clone()));

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
    fn from_str(py_key: Bound<'_, PyString>) -> PyResult<Self> {
        Ok(Self {
            first_item: PathItemString(py_key.try_into()?),
            rest: Vec::new(),
        })
    }

    fn from_list(obj: &Bound<'_, PyAny>) -> PyResult<LookupPath> {
        let mut iter = obj.cast::<PyList>()?.iter();

        let Some(first_item) = iter.next() else {
            return py_schema_err!("Each alias path should have at least one element");
        };

        let Ok(first_item_py_str) = first_item.cast_into::<PyString>() else {
            return py_err!(PyTypeError; "The first item in an alias path should be a string");
        };

        let first_item = PathItemString(first_item_py_str.try_into()?);

        let rest = iter.map(PathItem::from_py).collect::<PyResult<_>>()?;

        Ok(Self { first_item, rest })
    }

    pub fn apply_error_loc(&self, mut line_error: ValLineError, loc_by_alias: bool, field_name: &str) -> ValLineError {
        if loc_by_alias {
            for path_item in self.rest.iter().rev() {
                line_error = line_error.with_outer_location(path_item.to_loc_item());
            }
            line_error = line_error.with_outer_location(self.first_item.0.clone());
            line_error
        } else {
            line_error.with_outer_location(field_name)
        }
    }

    /// get the `str` from the first item in the path, note paths always have length > 0, and the first item
    /// is always a string
    pub fn first_key(&self) -> &str {
        &self.first_item
    }

    /// get the first item in the path
    pub fn first_item(&self) -> &PathItemString {
        &self.first_item
    }

    pub fn rest(&self) -> &[PathItem] {
        &self.rest
    }
}

#[derive(Debug, Clone)]
pub(crate) enum PathItem {
    S(PathItemString),
    /// integer key, used to get items from a list, tuple OR a dict with int keys `dict[int, ...]` (python only)
    Pos(usize),
    Neg(usize),
}

/// String type key, used to get or identify items from a dict or anything that implements `__getitem__`
#[derive(Debug, Clone, Eq, PartialEq, Hash)]
pub(crate) struct PathItemString(
    // stores the original Python value, easily accessible as a Rust &str
    pub PyBackedStr,
);

impl Borrow<str> for PathItemString {
    fn borrow(&self) -> &str {
        &self.0
    }
}

impl fmt::Display for PathItemString {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "'{key}'", key = &self.0)
    }
}

impl std::ops::Deref for PathItemString {
    type Target = str;

    fn deref(&self) -> &Self::Target {
        &self.0
    }
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

impl<'py> IntoPyObject<'py> for &'_ PathItemString {
    type Target = PyString;
    type Output = Bound<'py, PyString>;
    type Error = Infallible;

    fn into_pyobject(self, py: Python<'py>) -> Result<Self::Output, Self::Error> {
        (&self.0).into_pyobject(py).map(|obj|
            // SAFETY: `PyBackedStr` always returns a `PyString`, should open a PyO3 issue to not
            // need this unsafe cast
            unsafe { obj.cast_into_unchecked() })
    }
}

impl PathItem {
    pub fn from_py(obj: Bound<'_, PyAny>) -> PyResult<Self> {
        let obj = match obj.cast_into::<PyString>() {
            Ok(py_str_key) => {
                return Ok(Self::S(PathItemString(py_str_key.try_into()?)));
            }
            Err(e) => e.into_inner(),
        };

        if let Ok(usize_key) = obj.extract::<usize>() {
            Ok(Self::Pos(usize_key))
        } else if let Ok(int_key) = obj.extract::<isize>() {
            // usize has more possible positive values than isize, so guaranteed negative here
            Ok(Self::Neg(int_key.unsigned_abs()))
        } else {
            py_err!(PyTypeError; "Item in an alias path should be a string or int")
        }
    }

    pub fn py_get_item<'py>(&self, py_any: &Bound<'py, PyAny>) -> Option<Bound<'py, PyAny>> {
        // we definitely don't want to index strings, so explicitly omit this case
        if py_any.cast::<PyString>().is_ok() {
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
            Self::S(PathItemString(key)) => json_obj.iter().rev().find_map(|(k, v)| (k == &**key).then_some(v)),
            _ => None,
        }
    }

    fn to_loc_item(&self) -> LocItem {
        match self {
            Self::S(PathItemString(key)) => LocItem::from(key.clone()),
            Self::Pos(index) => LocItem::from(*index),
            Self::Neg(index) => LocItem::from(-(*index as i64)),
        }
    }
}

impl PathItemString {
    fn py_get_attrs<'py>(&self, obj: &Bound<'py, PyAny>) -> PyResult<Option<Bound<'py, PyAny>>> {
        // if obj is a dict, we want to use get_item, not getattr
        if let Ok(d) = obj.cast_exact::<PyDict>() {
            d.get_item(self)
        } else if obj.is_instance_of::<PyDict>() {
            // NB this deliberately goes through PyAnyMethods::get_item to allow subclasses of dict to override getitem
            // FIXME: should this instance check be for Mapping instead of Dict, and use `mapping_get`?
            Ok(obj.get_item(self).ok())
        } else {
            obj.getattr_opt(self)
        }
    }
}

#[derive(Debug)]
#[allow(clippy::struct_field_names)]
pub struct LookupKeyCollection {
    pub by_name: LookupKey,
    pub by_alias: Option<LookupKey>,
}

impl LookupKeyCollection {
    pub fn new(validation_alias: Option<Bound<'_, PyAny>>, field_name: &Bound<'_, PyString>) -> PyResult<Self> {
        let by_name = LookupKey::from_py(field_name)?;
        let by_alias = validation_alias.map(|va| LookupKey::from_py(&va)).transpose()?;
        Ok(Self { by_name, by_alias })
    }

    /// Returns the lookup keys to use based on the provided `lookup_type`. At least one key will always be returned.
    pub fn lookup_keys(&self, lookup_type: LookupType) -> impl Iterator<Item = &LookupKey> + use<'_> {
        let by_alias = self
            .by_alias
            .as_ref()
            .filter(|_| lookup_type.matches(LookupType::Alias));

        let by_name = Some(&self.by_name).filter(
            // always use the name if no alias is defined
            |_| self.by_alias.is_none() || lookup_type.matches(LookupType::Name),
        );

        by_alias.into_iter().chain(by_name)
    }

    /// Returns the first lookup key that matches the provided `lookup_type`.
    pub fn first_key_matching(&self, lookup_type: LookupType) -> &LookupKey {
        if lookup_type.matches(LookupType::Alias) {
            if let Some(by_alias) = &self.by_alias {
                return by_alias;
            }
        }
        &self.by_name
    }
}

/// Whether this lookup represents a name or an alias
#[derive(Debug, Clone, Copy, Eq, PartialEq)]
#[repr(u8)]
pub enum LookupType {
    Name = 1,
    Alias = 2,
    Both = 3,
}

impl LookupType {
    pub fn from_bools(validate_by_alias: bool, validate_by_name: bool) -> PyResult<LookupType> {
        match (validate_by_alias, validate_by_name) {
            (true, true) => Ok(LookupType::Both),
            (true, false) => Ok(LookupType::Alias),
            (false, true) => Ok(LookupType::Name),
            (false, false) => Err(PyValueError::new_err(
                "`validate_by_name` and `validate_by_alias` cannot both be set to `False`.",
            )),
        }
    }

    pub fn matches(self, other: LookupType) -> bool {
        (self as u8 & other as u8) != 0
    }
}
