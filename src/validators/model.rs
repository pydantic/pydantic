use pyo3::exceptions::PyTypeError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PySet, PyString};

use crate::build_tools::{py_error, SchemaDict};
use crate::errors::{as_internal, err_val_error, val_line_error, ErrorKind, ValError, ValLineError, ValResult};
use crate::input::{GenericMapping, Input, JsonInput, JsonObject};

use super::{build_validator, BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
struct ModelField {
    name: String,
    lookup_key: LookupKey,
    dict_key: Py<PyString>,
    required: bool,
    default: Option<PyObject>,
    validator: CombinedValidator,
}

#[derive(Debug, Clone)]
pub struct ModelValidator {
    fields: Vec<ModelField>,
    extra_behavior: ExtraBehavior,
    extra_validator: Option<Box<CombinedValidator>>,
}

impl BuildValidator for ModelValidator {
    const EXPECTED_TYPE: &'static str = "model";

    fn build(
        schema: &PyDict,
        _config: Option<&PyDict>,
        build_context: &mut BuildContext,
    ) -> PyResult<CombinedValidator> {
        // models ignore the parent config and always use the config from this model
        let config: Option<&PyDict> = schema.get_as("config")?;

        let model_full = config.get_as("model_full")?.unwrap_or(true);

        let extra_behavior = ExtraBehavior::from_py(config)?;
        let extra_validator = match extra_behavior {
            ExtraBehavior::Allow => match schema.get_item("extra_validator") {
                Some(v) => Some(Box::new(build_validator(v, config, build_context)?.0)),
                None => None,
            },
            _ => None,
        };

        let fields_dict: &PyDict = schema.get_as_req("fields")?;
        let mut fields: Vec<ModelField> = Vec::with_capacity(fields_dict.len());
        let allow_by_name: bool = config.get_as("allow_population_by_field_name")?.unwrap_or(false);

        let py = schema.py();
        for (key, value) in fields_dict.iter() {
            let field_info: &PyDict = value.cast_as()?;
            let schema: &PyAny = field_info.get_as_req("schema")?;
            let field_name: &str = key.extract()?;
            let default = field_info.get_as("default")?;

            fields.push(ModelField {
                name: field_name.to_string(),
                lookup_key: LookupKey::from_py(py, field_info, field_name, allow_by_name)?,
                dict_key: PyString::intern(py, field_name).into(),
                validator: match build_validator(schema, config, build_context) {
                    Ok((v, _)) => v,
                    Err(err) => return py_error!("Key \"{}\":\n  {}", key, err),
                },
                required: match field_info.get_as::<bool>("required")? {
                    Some(required) => {
                        if required && default.is_some() {
                            return py_error!("Key \"{}\":\n a required field cannot have a default value", key);
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
            extra_behavior,
            extra_validator,
        }
        .into())
    }
}

impl Validator for ModelValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        if let Some(field) = extra.field {
            // we're validating assignment, completely different logic
            return self.validate_assignment(py, field, input, extra, slots);
        }

        // TODO allow _try_instance to be configurable
        let dict = input.lax_dict(false)?;
        let output_dict = PyDict::new(py);
        let mut errors: Vec<ValLineError> = Vec::new();
        let fields_set = PySet::empty(py).map_err(as_internal)?;

        let extra = Extra {
            data: Some(output_dict),
            field: None,
        };

        macro_rules! process {
            ($dict:ident, $get_method:ident) => {{
                for field in &self.fields {
                    if let Some(value) = field.lookup_key.$get_method($dict) {
                        match field.validator.validate(py, value, &extra, slots) {
                            Ok(value) => output_dict
                                .set_item(&field.dict_key, value)
                                .map_err(as_internal)?,
                            Err(ValError::LineErrors(line_errors)) => {
                                for err in line_errors {
                                    errors.push(err.with_outer_location(field.name.clone().into()));
                                }
                            }
                            Err(err) => return Err(err),
                        }
                        fields_set.add(&field.dict_key).map_err(as_internal)?;
                    } else if let Some(ref default) = field.default {
                        output_dict
                            .set_item(&field.dict_key, default.as_ref(py))
                            .map_err(as_internal)?;
                    } else if !field.required {
                        continue;
                    } else {
                        errors.push(val_line_error!(
                            input_value = input.as_error_value(),
                            kind = ErrorKind::Missing,
                            reverse_location = vec![field.name.clone().into()]
                        ));
                    }
                }

                let (check_extra, forbid) = match self.extra_behavior {
                    ExtraBehavior::Ignore => (false, false),
                    ExtraBehavior::Allow => (true, false),
                    ExtraBehavior::Forbid => (true, true),
                };
                if check_extra {
                    for (raw_key, value) in $dict.iter() {
                        // TODO use strict_str here if the model is strict
                        let either_str = match raw_key.lax_str() {
                            Ok(k) => k,
                            Err(ValError::LineErrors(line_errors)) => {
                                for err in line_errors {
                                    errors.push(err.with_outer_location(raw_key.as_loc_item()));
                                }
                                continue;
                            }
                            Err(err) => return Err(err),
                        };
                        let py_key = either_str.as_py_string(py);
                        if fields_set.contains(py_key).map_err(as_internal)? {
                            continue;
                        }
                        fields_set.add(py_key).map_err(as_internal)?;

                        if forbid {
                            errors.push(val_line_error!(
                                input_value = input.as_error_value(),
                                kind = ErrorKind::ExtraForbidden,
                                reverse_location = vec![raw_key.as_loc_item()]
                            ));
                        } else if let Some(ref validator) = self.extra_validator {
                            match validator.validate(py, value, &extra, slots) {
                                Ok(value) => output_dict.set_item(py_key, value).map_err(as_internal)?,
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
                        }
                    }
                }
            }};
        }
        match dict {
            GenericMapping::PyDict(d) => process!(d, pydict_get),
            GenericMapping::JsonObject(d) => process!(d, jsonobject_get),
        }

        if errors.is_empty() {
            Ok((output_dict, fields_set).to_object(py))
        } else {
            Err(ValError::LineErrors(errors))
        }
    }

    fn get_name(&self, _py: Python) -> String {
        Self::EXPECTED_TYPE.to_string()
    }
}

impl ModelValidator {
    fn validate_assignment<'s, 'data>(
        &'s self,
        py: Python<'data>,
        field: &str,
        input: &'data impl Input<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject>
    where
        'data: 's,
    {
        // TODO probably we should set location on errors here
        let data = match extra.data {
            Some(data) => data,
            None => panic!("data is required when validating assignment"),
        };

        let prepare_tuple = |output: PyObject| {
            data.set_item(field, output).map_err(as_internal)?;
            let fields_set = PySet::new(py, &[field]).map_err(as_internal)?;
            Ok((data, fields_set).to_object(py))
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
            prepare_result(field.validator.validate(py, input, extra, slots))
        } else {
            match self.extra_behavior {
                // with allow we either want to set the value
                ExtraBehavior::Allow => match self.extra_validator {
                    Some(ref validator) => prepare_result(validator.validate(py, input, extra, slots)),
                    None => prepare_tuple(input.to_object(py)),
                },
                // otherwise we raise an error:
                // - with forbid this is obvious
                // - with ignore the model should never be overloaded, so an error is the clearest option
                _ => {
                    err_val_error!(
                        input_value = input.as_error_value(),
                        reverse_location = vec![field.to_string().into()],
                        kind = ErrorKind::ExtraForbidden
                    )
                }
            }
        }
    }
}

#[derive(Debug, Clone)]
enum ExtraBehavior {
    Allow,
    Ignore,
    Forbid,
}

impl ExtraBehavior {
    pub fn from_py(config: Option<&PyDict>) -> PyResult<Self> {
        match config.get_as::<&str>("extra")? {
            Some(s) => match s {
                "allow" => Ok(ExtraBehavior::Allow),
                "ignore" => Ok(ExtraBehavior::Ignore),
                "forbid" => Ok(ExtraBehavior::Forbid),
                _ => py_error!(r#"Invalid extra_behavior: "{}""#, s),
            },
            None => Ok(ExtraBehavior::Ignore),
        }
    }
}

/// Used got getting items from python or JSON objects, in different ways
#[derive(Debug, Clone)]
pub enum LookupKey {
    /// simply look up a key in a dict, equivalent to `d.get(key)`
    /// we save both the string and pystring to save creating the pystring for python
    Simple(String, PyObject),
    /// look up a key by either string, equivalent to `d.get(choice1, d.get(choice2))`
    /// these are interpreted as (json_key1, json_key2, py_key1, py_key2)
    Choice(String, String, PyObject, PyObject),
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
    pub fn from_py(py: Python, field: &PyDict, field_name: &str, allow_by_name: bool) -> PyResult<Self> {
        match field.get_as::<String>("alias")? {
            Some(alias) => {
                if field.contains("aliases")? {
                    py_error!("'alias' and 'aliases' cannot be used together")
                } else {
                    let alias_py = py_string!(py, &alias);
                    match allow_by_name {
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
                        if allow_by_name {
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

    fn pydict_get<'data, 's>(&'s self, dict: &'data PyDict) -> Option<&'data PyAny> {
        match self {
            LookupKey::Simple(_, py_key) => dict.get_item(py_key),
            LookupKey::Choice(_, _, py_key1, py_key2) => match dict.get_item(py_key1) {
                Some(v) => Some(v),
                None => dict.get_item(py_key2),
            },
            LookupKey::PathChoices(path_choices) => {
                for path in path_choices {
                    // iterate over the path and plug each value into the py_any from the last step, starting with dict
                    // this could just be a loop but should be somewhat faster with a functional design
                    if let Some(v) = path.iter().try_fold(dict as &PyAny, |d, loc| loc.py_get(d)) {
                        // Successfully found an item, return it
                        return Some(v);
                    }
                }
                // got to the end of path_choices, without a match, return None
                None
            }
        }
    }

    fn jsonobject_get<'data, 's>(&'s self, dict: &'data JsonObject) -> Option<&'data JsonInput> {
        match self {
            LookupKey::Simple(key, _) => dict.get(key),
            LookupKey::Choice(key1, key2, _, _) => match dict.get(key1) {
                Some(v) => Some(v),
                None => dict.get(key2),
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
                        return Some(v);
                    }
                }
                // got to the end of path_choices, without a match, return None
                None
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

    pub fn py_get<'a>(&self, py_any: &'a PyAny) -> Option<&'a PyAny> {
        // we definitely don't want to index strings, so explicitly omit this case
        if py_any.cast_as::<PyString>().is_ok() {
            None
        } else {
            // otherwise, blindly try getitem on v since no better logic is realistic
            // TODO we could perhaps try getattr for StrKey depending on try_instance
            match py_any.get_item(self) {
                Ok(v_next) => Some(v_next),
                // key/index not found, try next path
                Err(_) => None,
            }
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
