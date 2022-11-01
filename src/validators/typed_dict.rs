use pyo3::intern;
use pyo3::prelude::*;
#[cfg(not(PyPy))]
use pyo3::types::PyFunction;
use pyo3::types::{PyDict, PyList, PySet, PyString};
#[cfg(not(PyPy))]
use pyo3::PyTypeInfo;

use ahash::AHashSet;

use crate::build_tools::{is_strict, py_err, schema_or_config, schema_or_config_same, SchemaDict};
use crate::errors::{py_err_string, ErrorType, ValError, ValLineError, ValResult};
use crate::input::{GenericMapping, Input};
use crate::lookup_key::LookupKey;
use crate::questions::Question;
use crate::recursion_guard::RecursionGuard;

use super::with_default::get_default;
use super::{build_validator, BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
struct TypedDictField {
    name: String,
    lookup_key: LookupKey,
    name_pystring: Py<PyString>,
    required: bool,
    validator: CombinedValidator,
    frozen: bool,
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
        config: Option<&PyDict>,
        build_context: &mut BuildContext,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let strict = is_strict(schema, config)?;

        let extra_behavior = schema_or_config::<&str>(
            schema,
            config,
            intern!(py, "extra_behavior"),
            intern!(py, "typed_dict_extra_behavior"),
        )?;
        let total =
            schema_or_config(schema, config, intern!(py, "total"), intern!(py, "typed_dict_total"))?.unwrap_or(true);
        let from_attributes = schema_or_config_same(schema, config, intern!(py, "from_attributes"))?.unwrap_or(false);
        let populate_by_name = schema_or_config_same(schema, config, intern!(py, "populate_by_name"))?.unwrap_or(false);

        let return_fields_set = schema.get_as(intern!(py, "return_fields_set"))?.unwrap_or(false);

        let (check_extra, forbid_extra) = match extra_behavior {
            Some(s) => match s {
                "allow" => (true, false),
                "ignore" => (false, false),
                "forbid" => (true, true),
                _ => return py_err!(r#"Invalid extra_behavior: "{}""#, s),
            },
            None => (false, false),
        };

        let extra_validator = match schema.get_item(intern!(py, "extra_validator")) {
            Some(v) => {
                if check_extra && !forbid_extra {
                    Some(Box::new(build_validator(v, config, build_context)?))
                } else {
                    return py_err!("extra_validator can only be used if extra_behavior=allow");
                }
            }
            None => None,
        };

        let fields_dict: &PyDict = schema.get_as_req(intern!(py, "fields"))?;
        let mut fields: Vec<TypedDictField> = Vec::with_capacity(fields_dict.len());

        for (key, value) in fields_dict.iter() {
            let field_info: &PyDict = value.cast_as()?;
            let field_name: &str = key.extract()?;

            let schema = field_info.get_as_req(intern!(py, "schema"))?;

            let validator = match build_validator(schema, config, build_context) {
                Ok(v) => v,
                Err(err) => return py_err!("Field \"{}\":\n  {}", field_name, err),
            };

            let required = match field_info.get_as::<bool>(intern!(py, "required"))? {
                Some(required) => {
                    if required {
                        if let CombinedValidator::WithDefault(ref val) = validator {
                            if val.has_default() {
                                return py_err!("Field '{}': a required field cannot have a default value", field_name);
                            }
                        }
                    }
                    required
                }
                None => total,
            };

            if required {
                if let CombinedValidator::WithDefault(ref val) = validator {
                    if val.omit_on_error() {
                        return py_err!(
                            "Field '{}': 'on_error = omit' cannot be set for required fields",
                            field_name
                        );
                    }
                }
            }

            let lookup_key = match field_info.get_item(intern!(py, "alias")) {
                Some(alias) => {
                    let alt_alias = if populate_by_name { Some(field_name) } else { None };
                    LookupKey::from_py(py, alias, alt_alias)?
                }
                None => LookupKey::from_string(py, field_name),
            };

            fields.push(TypedDictField {
                name: field_name.to_string(),
                lookup_key,
                name_pystring: PyString::intern(py, field_name).into(),
                validator,
                required,
                frozen: field_info.get_as::<bool>(intern!(py, "frozen"))?.unwrap_or(false),
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
        let strict = extra.strict.unwrap_or(self.strict);
        let dict = input.validate_typed_dict(strict, self.from_attributes)?;

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
            strict: extra.strict,
            context: extra.context,
        };

        macro_rules! process {
            ($dict:ident, $get_method:ident, $iter_method:ident) => {{
                for field in &self.fields {
                    let op_key_value = match field.lookup_key.$get_method($dict) {
                        Ok(v) => v,
                        Err(err) => {
                            errors.push(ValLineError::new_with_loc(
                                ErrorType::GetAttributeError {
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
                                output_dict.set_item(&field.name_pystring, value)?;
                                if let Some(ref mut fs) = fields_set_vec {
                                    fs.push(field.name_pystring.clone_ref(py));
                                }
                            }
                            Err(ValError::Omit) => continue,
                            Err(ValError::LineErrors(line_errors)) => {
                                for err in line_errors {
                                    errors.push(err.with_outer_location(field.name.clone().into()));
                                }
                            }
                            Err(err) => return Err(err),
                        }
                        continue;
                    } else if let Some(value) = get_default(py, &field.validator)? {
                        output_dict.set_item(&field.name_pystring, value.as_ref())?;
                    } else if field.required {
                        errors.push(ValLineError::new_with_loc(
                            ErrorType::Missing,
                            input,
                            field.name.clone(),
                        ));
                    }
                }

                if let Some(ref mut used_keys) = used_keys {
                    for (raw_key, value) in $dict.$iter_method() {
                        let either_str = match raw_key.strict_str() {
                            Ok(k) => k,
                            Err(ValError::LineErrors(line_errors)) => {
                                for err in line_errors {
                                    errors.push(
                                        err.with_outer_location(raw_key.as_loc_item())
                                            .with_type(ErrorType::InvalidKey),
                                    );
                                }
                                continue;
                            }
                            Err(err) => return Err(err),
                        };
                        if used_keys.contains(either_str.as_cow()?.as_ref()) {
                            continue;
                        }

                        if self.forbid_extra {
                            errors.push(ValLineError::new_with_loc(
                                ErrorType::ExtraForbidden,
                                value,
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
                                    output_dict.set_item(py_key, value)?;
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
                            output_dict.set_item(py_key, value.to_object(py))?;
                            if let Some(ref mut fs) = fields_set_vec {
                                fs.push(py_key.into_py(py));
                            }
                        }
                    }
                }
            }};
        }
        match dict {
            GenericMapping::PyDict(d) => process!(d, py_get_item, iter),
            GenericMapping::PyGetAttr(d) => process!(d, py_get_attr, iter_attrs),
            GenericMapping::JsonObject(d) => process!(d, json_get, iter),
        }

        if !errors.is_empty() {
            Err(ValError::LineErrors(errors))
        } else if let Some(fs) = fields_set_vec {
            let fields_set = PySet::new(py, &fs)?;
            Ok((output_dict, fields_set).to_object(py))
        } else {
            Ok(output_dict.to_object(py))
        }
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }

    fn ask(&self, question: &Question) -> bool {
        match question {
            Question::ReturnFieldsSet => self.return_fields_set,
        }
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
            data.set_item(field, output)?;
            if self.return_fields_set {
                let fields_set = PySet::new(py, &[field])?;
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
            if field.frozen {
                Err(ValError::new_with_loc(ErrorType::Frozen, input, field.name.to_string()))
            } else {
                prepare_result(field.validator.validate(py, input, extra, slots, recursion_guard))
            }
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
                ErrorType::ExtraForbidden,
                input,
                field.to_string(),
            ))
        }
    }
}

trait IterAttributes<'a> {
    fn iter_attrs(&self) -> AttributesIterator<'a>;
}

impl<'a> IterAttributes<'a> for &'a PyAny {
    fn iter_attrs(&self) -> AttributesIterator<'a> {
        AttributesIterator {
            object: self,
            attributes: self.dir(),
            index: 0,
        }
    }
}

struct AttributesIterator<'a> {
    object: &'a PyAny,
    attributes: &'a PyList,
    index: usize,
}

impl<'a> Iterator for AttributesIterator<'a> {
    type Item = (&'a PyAny, &'a PyAny);

    fn next(&mut self) -> Option<(&'a PyAny, &'a PyAny)> {
        // loop until we find an attribute who's name does not start with underscore,
        // or we get to the end of the list of attributes
        loop {
            if self.index < self.attributes.len() {
                #[cfg(PyPy)]
                let name: &PyAny = self.attributes.get_item(self.index).unwrap();
                #[cfg(not(PyPy))]
                let name: &PyAny = unsafe { self.attributes.get_item_unchecked(self.index) };
                self.index += 1;
                // from benchmarks this is 14x faster than using the python `startswith` method
                let name_cow = name
                    .cast_as::<PyString>()
                    .expect("dir didn't return a PyString")
                    .to_string_lossy();
                if !name_cow.as_ref().starts_with('_') {
                    // getattr is most likely to fail due to an exception in a @property, skip
                    if let Ok(attr) = self.object.getattr(name_cow.as_ref()) {
                        // we don't want bound methods to be included, is there a better way to check?
                        // ref https://stackoverflow.com/a/18955425/949890
                        let is_bound = matches!(attr.hasattr(intern!(attr.py(), "__self__")), Ok(true));
                        // the PyFunction::is_type_of(attr) catches `staticmethod`, but also any other function,
                        // I think that's better than including static methods in the yielded attributes,
                        // if someone really wants fields, they can use an explicit field, or a function to modify input
                        #[cfg(not(PyPy))]
                        if !is_bound && !PyFunction::is_type_of(attr) {
                            return Some((name, attr));
                        }
                        // MASSIVE HACK! PyFunction doesn't exist for PyPy,
                        // is_instance_of::<PyFunction> crashes with a null pointer, hence this hack, see
                        // https://github.com/pydantic/pydantic-core/pull/161#discussion_r917257635
                        #[cfg(PyPy)]
                        if !is_bound && attr.get_type().to_string() != "<class 'function'>" {
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
