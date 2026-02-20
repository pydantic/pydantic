use std::borrow::Borrow;
use std::convert::Infallible;
use std::fmt;

use pyo3::IntoPyObjectExt;
use pyo3::exceptions::{PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::pybacked::PyBackedStr;
use pyo3::types::{PyDict, PyList, PyMapping, PyString};

use jiter::{JsonObject, JsonValue};
use smallvec::SmallVec;

use crate::build_tools::py_schema_err;
use crate::errors::{ErrorType, LocItem, Location, ValError, ValLineError, ValResult, py_err_string};
use crate::input::StringMapping;
use crate::tools::{mapping_get, py_err};

/// The possible choices for an alias value in Python
#[derive(FromPyObject)]
pub(crate) enum ValidationAlias {
    /// `str`
    Str(PyBackedStr),
    /// `list[int | str]`
    AliasPath(LookupPath),
    /// `list[list[int | str]]`
    AliasChoices(#[pyo3(from_py_with = LookupPath::from_mulitiple_list)] SmallVec<[LookupPath; 1]>),
}

impl ValidationAlias {
    pub fn into_paths(self) -> SmallVec<[LookupPath; 1]> {
        match self {
            Self::Str(py_str) => SmallVec::from_buf([LookupPath {
                first_item: PathItemString(py_str),
                rest: Vec::new(),
            }]),
            Self::AliasPath(path) => SmallVec::from_buf([path]),
            Self::AliasChoices(paths) => paths,
        }
    }
}

impl FromPyObject<'_, '_> for LookupPath {
    type Error = PyErr;

    fn extract(obj: Borrowed<'_, '_, PyAny>) -> Result<Self, Self::Error> {
        LookupPath::from_list(&obj)
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

    fn from_mulitiple_list(obj: &Bound<'_, PyAny>) -> PyResult<SmallVec<[LookupPath; 1]>> {
        let list = obj.cast::<PyList>()?;
        if list.is_empty() {
            return py_schema_err!("Lookup paths should have at least one element");
        }
        list.extract()
    }

    pub fn py_get_dict_item<'py>(&self, dict: &Bound<'py, PyDict>) -> PyResult<Option<Bound<'py, PyAny>>> {
        self.get_impl(dict, PyDictMethods::get_item, |d, loc| Ok(loc.py_get_item(&d)))
    }

    pub fn py_get_string_mapping_item<'py>(&self, dict: &Bound<'py, PyDict>) -> ValResult<Option<StringMapping<'py>>> {
        if let Some(py_any) = self.py_get_dict_item(dict)? {
            let value = StringMapping::new_value(py_any)?;
            Ok(Some(value))
        } else {
            Ok(None)
        }
    }

    pub fn py_get_mapping_item<'py>(&self, dict: &Bound<'py, PyMapping>) -> PyResult<Option<Bound<'py, PyAny>>> {
        self.get_impl(dict, mapping_get, |d, loc| Ok(loc.py_get_item(&d)))
    }

    pub fn simple_py_get_attr<'py>(&self, obj: &Bound<'py, PyAny>) -> PyResult<Option<Bound<'py, PyAny>>> {
        self.get_impl(obj, PyAnyMethods::getattr_opt, |d, loc| loc.py_get_attrs(&d))
    }

    pub fn py_get_attr<'py>(
        &self,
        obj: &Bound<'py, PyAny>,
        kwargs: Option<&Bound<'py, PyDict>>,
    ) -> ValResult<Option<Bound<'py, PyAny>>> {
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

    pub fn json_get<'a, 'data>(&self, dict: &'a JsonObject<'data>) -> ValResult<Option<&'a JsonValue<'data>>> {
        // FIXME: use of find_map in here probably leads to quadratic complexity

        // first step is different as the first step is a key lookup
        if let Some(v) = dict
            .iter()
            .rev()
            .find_map(|(k, v)| (k == self.first_key()).then_some(v))
        // fold the rest of the path over the found value
            && let Some(v) = self.rest.iter().try_fold(v, |d, loc| loc.json_get(d))
        {
            return Ok(Some(v));
        }

        Ok(None)
    }

    fn get_impl<'s, 'a, SourceT, OutputT: 'a>(
        &'s self,
        source: &'a SourceT,
        lookup: impl Fn(&'a SourceT, &'s PathItemString) -> PyResult<Option<OutputT>>,
        nested_lookup: impl Fn(OutputT, &'s PathItem) -> PyResult<Option<OutputT>>,
    ) -> PyResult<Option<OutputT>> {
        let Some(mut value) = lookup(source, &self.first_item)? else {
            return Ok(None);
        };

        // iterate over the path and plug each value into the value from the last step
        for loc in &self.rest {
            value = match nested_lookup(value, loc)? {
                Some(v) => v,
                None => return Ok(None),
            }
        }

        // Successfully found an item, return it
        Ok(Some(value))
    }

    pub fn loc(&self) -> Location {
        let mut location = Vec::with_capacity(1 + self.rest.len());
        for item in self.rest.iter().rev() {
            location.push(item.to_loc_item());
        }
        location.push(LocItem::from(self.first_item.0.clone()));
        Location::List(location)
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
        (&self.0).into_pyobject(py)
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
pub struct LookupPathCollection {
    pub by_name: LookupPath,
    pub by_alias: SmallVec<[LookupPath; 1]>,
}

impl LookupPathCollection {
    pub fn new(validation_alias: Option<ValidationAlias>, field_name: PyBackedStr) -> PyResult<Self> {
        let by_name = LookupPath {
            first_item: PathItemString(field_name),
            rest: Vec::new(),
        };
        let by_alias = validation_alias.map(ValidationAlias::into_paths).unwrap_or_default();
        Ok(Self { by_name, by_alias })
    }

    /// Returns the lookup paths to use based on the provided `lookup_type`. At least one path will always be returned.
    pub fn lookup_paths(&self, lookup_type: LookupType) -> impl Iterator<Item = &LookupPath> + use<'_> {
        let by_alias = lookup_type
            .matches(LookupType::Alias)
            .then_some(&self.by_alias)
            .into_iter()
            .flatten();

        // always use the name if no alias is defined
        let by_name = (self.by_alias.is_empty() || lookup_type.matches(LookupType::Name)).then_some(&self.by_name);

        by_alias.into_iter().chain(by_name)
    }

    /// Attempts lookups in order based on the provided `lookup_type`, returning the first successful lookup, or the first error encountered.
    pub fn try_lookup<T, E>(
        &self,
        lookup_type: LookupType,
        mut lookup_fn: impl FnMut(&LookupPath) -> Result<Option<T>, E>,
    ) -> Result<Option<(&LookupPath, T)>, E> {
        self.lookup_paths(lookup_type)
            .find_map(|path| match lookup_fn(path) {
                Ok(Some(value)) => Some(Ok((path, value))),
                Ok(None) => None,
                Err(err) => Some(Err(err)),
            })
            .transpose()
    }

    /// Returns the error location to use based on the provided `lookup_type` and `loc_by_alias`.
    pub fn error_loc(&self, lookup_type: LookupType, loc_by_alias: bool) -> Location {
        if loc_by_alias
            && lookup_type.matches(LookupType::Alias)
            && let Some(first_alias) = &self.by_alias.first()
        {
            return first_alias.loc();
        }
        self.by_name.loc()
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
