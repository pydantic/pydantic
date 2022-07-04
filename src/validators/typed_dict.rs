use pyo3::exceptions::{PyAttributeError, PyTypeError};
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyFunction, PyList, PySet, PyString};

use ahash::AHashSet;

use crate::build_tools::{py_error, SchemaDict};
use crate::errors::{as_internal, py_err_string, ErrorKind, ValError, ValLineError, ValResult};
use crate::input::{GenericMapping, Input, JsonInput, JsonObject};
use crate::recursion_guard::RecursionGuard;
use crate::SchemaError;

use super::{build_validator, BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
struct TypedDictField {
    name: String,
    lookup_key: LookupKey,
    name_pystring: Py<PyString>,
    required: bool,
    default: Option<PyObject>,
    validator: CombinedValidator,
}

#[derive(Debug, Clone)]
pub struct TypedDictValidator {
    fields: Vec<TypedDictField>,
    check_extra: bool,
    forbid_extra: bool,
    extra_validator: Option<Box<CombinedValidator>>,
    strict: bool,
    from_attributes: bool,
    return_fields_set: bool,
}

impl BuildValidator for TypedDictValidator {
    const EXPECTED_TYPE: &'static str = "typed-dict";

    fn build(
        schema: &PyDict,
        _config: Option<&PyDict>,
        build_context: &mut BuildContext,
    ) -> PyResult<CombinedValidator> {
        // models ignore the parent config and always use the config from this model
        let config: Option<&PyDict> = schema.get_as("config")?;

        let model_full = config.get_as("model_full")?.unwrap_or(true);
        let strict = config.get_as("strict")?.unwrap_or(false);
        let from_attributes = config.get_as("from_attributes")?.unwrap_or(false);
        let return_fields_set = schema.get_as("return_fields_set")?.unwrap_or(false);

        let (check_extra, forbid_extra) = match config.get_as::<&str>("extra_behavior")? {
            Some(s) => match s {
                "allow" => (true, false),
                "ignore" => (false, false),
                "forbid" => (true, true),
                _ => return py_error!(r#"Invalid extra_behavior: "{}""#, s),
            },
            None => (false, false),
        };

        let extra_validator = match schema.get_item("extra_validator") {
            Some(v) => {
                if check_extra && !forbid_extra {
                    Some(Box::new(build_validator(v, config, build_context)?.0))
                } else {
                    return py_error!("extra_validator can only be used if extra_behavior=allow");
                }
            }
            None => None,
        };

        let populate_by_name: bool = config.get_as("populate_by_name")?.unwrap_or(false);
        let fields_dict: &PyDict = schema.get_as_req("fields")?;
        let mut fields: Vec<TypedDictField> = Vec::with_capacity(fields_dict.len());

        let py = schema.py();
        for (key, value) in fields_dict.iter() {
            let field_info: &PyDict = value.cast_as()?;
            let field_name: &str = key.extract()?;
            let schema: &PyAny = field_info
                .get_as_req("schema")
                .map_err(|err| SchemaError::new_err(format!("Field \"{}\":\n  {}", field_name, err)))?;
            let default = field_info
                .get_as("default")
                .map_err(|err| PyTypeError::new_err(format!("Field \"{}\":\n  {}", field_name, err)))?;

            fields.push(TypedDictField {
                name: field_name.to_string(),
                lookup_key: LookupKey::from_py(py, field_info, field_name, populate_by_name)?,
                name_pystring: PyString::intern(py, field_name).into(),
                validator: match build_validator(schema, config, build_context) {
                    Ok((v, _)) => v,
                    Err(err) => return py_error!("Field \"{}\":\n  {}", field_name, err),
                },
                required: match field_info.get_as::<bool>("required")? {
                    Some(required) => {
                        if required && default.is_some() {
                            return py_error!("Field \"{}\": a required field cannot have a default value", field_name);
                        }
                        required
                    }
                    None => model_full,
                },
                default,
            });
        }
        Ok(Self {
            fields,
            check_extra,
            forbid_extra,
            extra_validator,
            strict,
            from_attributes,
            return_fields_set,
        }
        .into())
    }
}

impl Validator for TypedDictValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        if let Some(field) = extra.field {
            // we're validating assignment, completely different logic
            return self.validate_assignment(py, field, input, extra, slots, recursion_guard);
        }

        let dict = input.typed_dict(self.from_attributes, !self.strict)?;

        let output_dict = PyDict::new(py);
        let mut errors: Vec<ValLineError> = Vec::with_capacity(self.fields.len());
        let mut fields_set_vec: Option<Vec<Py<PyString>>> = match self.return_fields_set {
            true => Some(Vec::with_capacity(self.fields.len())),
            false => None,
        };

        // we only care about which keys have been used if we're iterating over the object for extra after
        // the first pass
        let mut used_keys: Option<AHashSet<&str>> = match self.check_extra {
            true => Some(AHashSet::with_capacity(self.fields.len())),
            false => None,
        };

        let extra = Extra {
            data: Some(output_dict),
            field: None,
        };

        macro_rules! process {
            ($dict:ident, $get_method:ident, $iter:block) => {{
                for field in &self.fields {
                    let op_key_value = match field.lookup_key.$get_method($dict) {
                        Ok(v) => v,
                        Err(err) => {
                            errors.push(ValLineError::new_with_loc(
                                ErrorKind::GetAttributeError {
                                    error: py_err_string(py, err),
                                },
                                input,
                                field.name.clone(),
                            ));
                            continue;
                        }
                    };
                    if let Some((used_key, value)) = op_key_value {
                        if let Some(ref mut used_keys) = used_keys {
                            // key is "used" whether or not validation passes, since we want to skip this key in
                            // extra logic either way
                            used_keys.insert(used_key);
                        }
                        match field
                            .validator
                            .validate(py, value, &extra, slots, recursion_guard)
                        {
                            Ok(value) => {
                                output_dict
                                    .set_item(&field.name_pystring, value)
                                    .map_err(as_internal)?;
                                if let Some(ref mut fs) = fields_set_vec {
                                    fs.push(field.name_pystring.clone_ref(py));
                                }
                            }
                            Err(ValError::LineErrors(line_errors)) => {
                                for err in line_errors {
                                    errors.push(err.with_outer_location(field.name.clone().into()));
                                }
                            }
                            Err(err) => return Err(err),
                        }
                    } else if let Some(ref default) = field.default {
                        // TODO default needs to be copied here
                        output_dict
                            .set_item(&field.name_pystring, default.as_ref(py))
                            .map_err(as_internal)?;
                    } else if !field.required {
                        continue;
                    } else {
                        errors.push(ValLineError::new_with_loc(
                            ErrorKind::Missing,
                            input,
                            field.name.clone(),
                        ));
                    }
                }

                if self.check_extra {
                    let used_keys = match used_keys {
                        Some(v) => v,
                        None => unreachable!(),
                    };
                    for (raw_key, value) in $iter {
                        let either_str = match raw_key.strict_str() {
                            Ok(k) => k,
                            Err(ValError::LineErrors(line_errors)) => {
                                for err in line_errors {
                                    errors.push(
                                        err.with_outer_location(raw_key.as_loc_item())
                                            .with_kind(ErrorKind::InvalidKey),
                                    );
                                }
                                continue;
                            }
                            Err(err) => return Err(err),
                        };
                        if used_keys.contains(either_str.as_cow().as_ref()) {
                            continue;
                        }

                        if self.forbid_extra {
                            errors.push(ValLineError::new_with_loc(
                                ErrorKind::ExtraForbidden,
                                input,
                                raw_key.as_loc_item(),
                            ));
                            continue;
                        }

                        let py_key = either_str.as_py_string(py);
                        if let Some(ref mut fs) = fields_set_vec {
                            fs.push(py_key.into_py(py));
                        }

                        if let Some(ref validator) = self.extra_validator {
                            match validator.validate(py, value, &extra, slots, recursion_guard) {
                                Ok(value) => {
                                    output_dict.set_item(py_key, value).map_err(as_internal)?;
                                    if let Some(ref mut fs) = fields_set_vec {
                                        fs.push(py_key.into_py(py));
                                    }
                                }
                                Err(ValError::LineErrors(line_errors)) => {
                                    for err in line_errors {
                                        errors.push(err.with_outer_location(raw_key.as_loc_item()));
                                    }
                                }
                                Err(err) => return Err(err),
                            }
                        } else {
                            output_dict
                                .set_item(py_key, value.to_object(py))
                                .map_err(as_internal)?;
                            if let Some(ref mut fs) = fields_set_vec {
                                fs.push(py_key.into_py(py));
                            }
                        }
                    }
                }
            }};
        }
        match dict {
            GenericMapping::PyDict(d) => process!(d, py_get_item, { d.iter() }),
            GenericMapping::PyGetAttr(d) => process!(d, py_get_attr, { IterAttributes::new(d) }),
            GenericMapping::JsonObject(d) => process!(d, json_get, { d.iter() }),
        }

        if !errors.is_empty() {
            Err(ValError::LineErrors(errors))
        } else if let Some(fs) = fields_set_vec {
            let fields_set = PySet::new(py, &fs).map_err(as_internal)?;
            Ok((output_dict, fields_set).to_object(py))
        } else {
            Ok(output_dict.to_object(py))
        }
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }

    fn complete(&mut self, build_context: &BuildContext) -> PyResult<()> {
        self.fields
            .iter_mut()
            .try_for_each(|f| f.validator.complete(build_context))
    }
}

impl TypedDictValidator {
    fn validate_assignment<'s, 'data>(
        &'s self,
        py: Python<'data>,
        field: &str,
        input: &'data impl Input<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject>
    where
        'data: 's,
    {
        // TODO probably we should set location on errors here
        let data = match extra.data {
            Some(data) => data,
            None => unreachable!(),
        };

        let prepare_tuple = |output: PyObject| {
            data.set_item(field, output).map_err(as_internal)?;
            if self.return_fields_set {
                let fields_set = PySet::new(py, &[field]).map_err(as_internal)?;
                Ok((data, fields_set).to_object(py))
            } else {
                Ok(data.to_object(py))
            }
        };

        let prepare_result = |result: ValResult<'data, PyObject>| match result {
            Ok(output) => prepare_tuple(output),
            Err(ValError::LineErrors(line_errors)) => {
                let errors = line_errors
                    .into_iter()
                    .map(|e| e.with_outer_location(field.to_string().into()))
                    .collect();
                Err(ValError::LineErrors(errors))
            }
            Err(err) => Err(err),
        };

        if let Some(field) = self.fields.iter().find(|f| f.name == field) {
            prepare_result(field.validator.validate(py, input, extra, slots, recursion_guard))
        } else if self.check_extra && !self.forbid_extra {
            // this is the "allow" case of extra_behavior
            match self.extra_validator {
                Some(ref validator) => prepare_result(validator.validate(py, input, extra, slots, recursion_guard)),
                None => prepare_tuple(input.to_object(py)),
            }
        } else {
            // otherwise we raise an error:
            // - with forbid this is obvious
            // - with ignore the model should never be overloaded, so an error is the clearest option
            Err(ValError::new_with_loc(
                ErrorKind::ExtraForbidden,
                input,
                field.to_string(),
            ))
        }
    }
}

/// Used got getting items from python or JSON objects, in different ways
#[derive(Debug, Clone)]
pub enum LookupKey {
    /// simply look up a key in a dict, equivalent to `d.get(key)`
    /// we save both the string and pystring to save creating the pystring for python
    Simple(String, Py<PyString>),
    /// look up a key by either string, equivalent to `d.get(choice1, d.get(choice2))`
    /// these are interpreted as (json_key1, json_key2, py_key1, py_key2)
    Choice(String, String, Py<PyString>, Py<PyString>),
    /// look up keys buy one or more "paths" a path might be `['foo', 'bar']` to get `d.?foo.?bar`
    /// ints are also supported to index arrays/lists/tuples and dicts with int keys
    /// we reuse Location as the enum is the same, and the meaning is the same
    PathChoices(Vec<Path>),
}

macro_rules! py_string {
    ($py:ident, $str:expr) => {
        PyString::intern($py, $str).into()
    };
}

impl LookupKey {
    pub fn from_py(py: Python, field: &PyDict, field_name: &str, populate_by_name: bool) -> PyResult<Self> {
        match field.get_as::<String>("alias")? {
            Some(alias) => {
                if field.contains("aliases")? {
                    py_error!("'alias' and 'aliases' cannot be used together")
                } else {
                    let alias_py = py_string!(py, &alias);
                    match populate_by_name {
                        true => Ok(LookupKey::Choice(
                            alias,
                            field_name.to_string(),
                            alias_py,
                            py_string!(py, field_name),
                        )),
                        false => Ok(LookupKey::Simple(alias, alias_py)),
                    }
                }
            }
            None => match field.get_as::<&PyList>("aliases")? {
                Some(aliases) => {
                    let mut locs = aliases
                        .iter()
                        .map(|obj| Self::path_choice(py, obj))
                        .collect::<PyResult<Vec<Path>>>()?;

                    if locs.is_empty() {
                        py_error!("Aliases must have at least one element")
                    } else {
                        if populate_by_name {
                            locs.push(vec![PathItem::S(field_name.to_string(), py_string!(py, field_name))])
                        }
                        Ok(LookupKey::PathChoices(locs))
                    }
                }
                None => Ok(LookupKey::Simple(field_name.to_string(), py_string!(py, field_name))),
            },
        }
    }

    fn path_choice(py: Python, obj: &PyAny) -> PyResult<Path> {
        let path = obj
            .extract::<&PyList>()?
            .iter()
            .enumerate()
            .map(|(index, obj)| PathItem::from_py(py, index, obj))
            .collect::<PyResult<Path>>()?;

        if path.is_empty() {
            py_error!("Each alias path must have at least one element")
        } else {
            Ok(path)
        }
    }

    fn py_get_item<'data, 's>(&'s self, dict: &'data PyDict) -> PyResult<Option<(&'s str, &'data PyAny)>> {
        match self {
            LookupKey::Simple(key, py_key) => match dict.get_item(py_key) {
                Some(value) => Ok(Some((key, value))),
                None => Ok(None),
            },
            LookupKey::Choice(key1, key2, py_key1, py_key2) => match dict.get_item(py_key1) {
                Some(value) => Ok(Some((key1, value))),
                None => match dict.get_item(py_key2) {
                    Some(value) => Ok(Some((key2, value))),
                    None => Ok(None),
                },
            },
            LookupKey::PathChoices(path_choices) => {
                for path in path_choices {
                    // iterate over the path and plug each value into the py_any from the last step, starting with dict
                    // this could just be a loop but should be somewhat faster with a functional design
                    if let Some(v) = path.iter().try_fold(dict as &PyAny, |d, loc| loc.py_get_item(d)) {
                        // Successfully found an item, return it
                        let key = path.first().unwrap().get_key();
                        return Ok(Some((key, v)));
                    }
                }
                // got to the end of path_choices, without a match, return None
                Ok(None)
            }
        }
    }

    fn py_get_attr<'data, 's>(&'s self, obj: &'data PyAny) -> PyResult<Option<(&'s str, &'data PyAny)>> {
        match self {
            LookupKey::Simple(key, py_key) => match py_get_attrs(obj, &py_key)? {
                Some(value) => Ok(Some((key, value))),
                None => Ok(None),
            },
            LookupKey::Choice(key1, key2, py_key1, py_key2) => match py_get_attrs(obj, &py_key1)? {
                Some(value) => Ok(Some((key1, value))),
                None => match py_get_attrs(obj, &py_key2)? {
                    Some(value) => Ok(Some((key2, value))),
                    None => Ok(None),
                },
            },
            LookupKey::PathChoices(path_choices) => {
                'outer: for path in path_choices {
                    // similar to above, but using `py_get_attrs`, we can't use try_fold because of the extra Err
                    // so we have to loop manually
                    let mut v = obj;
                    for loc in path {
                        v = match loc.py_get_attrs(v) {
                            Ok(Some(v)) => v,
                            Ok(None) => {
                                continue 'outer;
                            }
                            Err(e) => return Err(e),
                        }
                    }
                    // Successfully found an item, return it
                    let key = path.first().unwrap().get_key();
                    return Ok(Some((key, v)));
                }
                // got to the end of path_choices, without a match, return None
                Ok(None)
            }
        }
    }

    fn json_get<'data, 's>(&'s self, dict: &'data JsonObject) -> PyResult<Option<(&'s str, &'data JsonInput)>> {
        match self {
            LookupKey::Simple(key, _) => match dict.get(key) {
                Some(value) => Ok(Some((key, value))),
                None => Ok(None),
            },
            LookupKey::Choice(key1, key2, _, _) => match dict.get(key1) {
                Some(value) => Ok(Some((key1, value))),
                None => match dict.get(key2) {
                    Some(value) => Ok(Some((key2, value))),
                    None => Ok(None),
                },
            },
            LookupKey::PathChoices(path_choices) => {
                for path in path_choices {
                    let mut path_iter = path.iter();

                    // first step is different from the rest as we already know dict is JsonObject
                    // because of above checks, we know that path must have at least one element, hence unwrap
                    let v: &JsonInput = match path_iter.next().unwrap().json_obj_get(dict) {
                        Some(v) => v,
                        None => continue,
                    };

                    // similar to above
                    // iterate over the path and plug each value into the JsonInput from the last step, starting with v
                    // from the first step, this could just be a loop but should be somewhat faster with a functional design
                    if let Some(v) = path_iter.try_fold(v, |d, loc| loc.json_get(d)) {
                        // Successfully found an item, return it
                        let key = path.first().unwrap().get_key();
                        return Ok(Some((key, v)));
                    }
                }
                // got to the end of path_choices, without a match, return None
                Ok(None)
            }
        }
    }
}

#[derive(Debug, Clone)]
pub enum PathItem {
    /// string type key, used to get or identify items from a dict or anything that implements `__getitem__`
    /// as above we store both the string and pystring to save creating the pystring for python
    S(String, Py<PyString>),
    /// integer key, used to get items from a list, tuple OR a dict with int keys `Dict[int, ...]` (python only)
    I(usize),
}

impl ToPyObject for PathItem {
    fn to_object(&self, py: Python<'_>) -> PyObject {
        match self {
            Self::S(_, val) => val.to_object(py),
            Self::I(val) => val.to_object(py),
        }
    }
}

type Path = Vec<PathItem>;

impl PathItem {
    pub fn from_py(py: Python, index: usize, obj: &PyAny) -> PyResult<Self> {
        if let Ok(str_key) = obj.extract::<String>() {
            let py_str_key = py_string!(py, &str_key);
            Ok(Self::S(str_key, py_str_key))
        } else if let Ok(int_key) = obj.extract::<usize>() {
            if index == 0 {
                py_error!(PyTypeError; "The first item in an alias path must be a string")
            } else {
                Ok(Self::I(int_key))
            }
        } else {
            py_error!(PyTypeError; "Alias path items must be with a string or int")
        }
    }

    pub fn py_get_item<'a>(&self, py_any: &'a PyAny) -> Option<&'a PyAny> {
        // we definitely don't want to index strings, so explicitly omit this case
        if py_any.cast_as::<PyString>().is_ok() {
            None
        } else {
            // otherwise, blindly try getitem on v since no better logic is realistic
            py_any.get_item(self).ok()
        }
    }

    pub fn get_key(&self) -> &str {
        match self {
            Self::S(key, _) => key.as_str(),
            Self::I(_) => unreachable!(),
        }
    }

    pub fn py_get_attrs<'a>(&self, obj: &'a PyAny) -> PyResult<Option<&'a PyAny>> {
        match self {
            Self::S(_, py_key) => {
                // if obj is a dict, we want to use get_item, not getattr
                if obj.cast_as::<PyDict>().is_ok() {
                    Ok(self.py_get_item(obj))
                } else {
                    py_get_attrs(obj, py_key)
                }
            }
            // int, we fall back to py_get_item - e.g. we want to use get_item for a list, tuple, dict, etc.
            Self::I(_) => Ok(self.py_get_item(obj)),
        }
    }

    pub fn json_get<'a>(&self, any_json: &'a JsonInput) -> Option<&'a JsonInput> {
        match any_json {
            JsonInput::Object(v_obj) => self.json_obj_get(v_obj),
            JsonInput::Array(v_array) => match self {
                Self::I(index) => v_array.get(*index),
                _ => None,
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
/// We dont check `try_from_attributes` because that check was performed on the top level object before we got here
fn py_get_attrs<N>(obj: &PyAny, attr_name: N) -> PyResult<Option<&PyAny>>
where
    N: ToPyObject,
{
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

pub struct IterAttributes<'a> {
    object: &'a PyAny,
    attributes: &'a PyList,
    index: usize,
}

impl<'a> IterAttributes<'a> {
    pub fn new(object: &'a PyAny) -> Self {
        Self {
            object,
            attributes: object.dir(),
            index: 0,
        }
    }
}

impl<'a> Iterator for IterAttributes<'a> {
    type Item = (&'a PyAny, &'a PyAny);

    fn next(&mut self) -> Option<(&'a PyAny, &'a PyAny)> {
        // loop until we find an attribute who's name does not start with underscore,
        // or we get to the end of the list of attributes
        loop {
            if self.index < self.attributes.len() {
                let name: &PyAny = unsafe { self.attributes.get_item_unchecked(self.index) };
                self.index += 1;
                // from benchmarks this is 14x faster than using the python `startswith` method
                let name_cow = name
                    .cast_as::<PyString>()
                    .expect("dir didn't return a PyString")
                    .to_string_lossy();
                if !name_cow.as_ref().starts_with('_') {
                    // getattr is most likely to fail due to an exception in a @property, skip
                    if let Ok(attr) = self.object.getattr(name) {
                        // we don't want bound methods to be included, is there a better way to check?
                        // ref https://stackoverflow.com/a/18955425/949890
                        let is_bound = matches!(attr.hasattr(intern!(attr.py(), "__self__")), Ok(true));
                        // the is_instance_of::<PyFunction> catches `staticmethod`, but also any other function,
                        // I think that's better than including static methods in the yielded attributes,
                        // if someone really wants fields, they can use an explicit field, or a function to modify input
                        if !is_bound && !matches!(attr.is_instance_of::<PyFunction>(), Ok(true)) {
                            return Some((name, attr));
                        }
                    }
                }
            } else {
                return None;
            }
        }
    }
    // size_hint is omitted as it isn't needed
}
