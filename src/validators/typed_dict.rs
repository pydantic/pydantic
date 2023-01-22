use pyo3::intern;
use pyo3::prelude::*;

use ahash::AHashSet;
use pyo3::types::{PyDict, PySet, PyString};

use crate::build_tools::{is_strict, py_err, schema_or_config, schema_or_config_same, SchemaDict};
use crate::errors::{py_err_string, ErrorType, ValError, ValLineError, ValResult};
use crate::input::{
    AttributesGenericIterator, DictGenericIterator, GenericMapping, Input, JsonObjectGenericIterator,
    MappingGenericIterator,
};
use crate::lookup_key::LookupKey;
use crate::questions::Question;
use crate::recursion_guard::RecursionGuard;

use super::with_default::get_default;
use super::{build_validator, BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
struct TypedDictField {
    name: String,
    lookup_key: LookupKey,
    name_py: Py<PyString>,
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
        build_context: &mut BuildContext<CombinedValidator>,
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
            let field_info: &PyDict = value.downcast()?;
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

            let lookup_key = match field_info.get_item(intern!(py, "validation_alias")) {
                Some(alias) => {
                    let alt_alias = if populate_by_name { Some(field_name) } else { None };
                    LookupKey::from_py(py, alias, alt_alias)?
                }
                None => LookupKey::from_string(py, field_name),
            };

            fields.push(TypedDictField {
                name: field_name.to_string(),
                lookup_key,
                name_py: PyString::intern(py, field_name).into(),
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
            ($dict:ident, $get_method:ident, $iter:ty $(,$kwargs:ident)?) => {{
                for field in &self.fields {
                    let op_key_value = match field.lookup_key.$get_method($dict $(, $kwargs )? ) {
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
                                output_dict.set_item(&field.name_py, value)?;
                                if let Some(ref mut fs) = fields_set_vec {
                                    fs.push(field.name_py.clone_ref(py));
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
                        output_dict.set_item(&field.name_py, value.as_ref())?;
                    } else if field.required {
                        errors.push(ValLineError::new_with_loc(
                            ErrorType::Missing,
                            input,
                            field.name.clone(),
                        ));
                    }
                }

                if let Some(ref mut used_keys) = used_keys {
                    for item_result in <$iter>::new($dict)? {
                        let (raw_key, value) = item_result?;
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
            GenericMapping::PyDict(d) => process!(d, py_get_dict_item, DictGenericIterator),
            GenericMapping::PyGetAttr(d, kwargs) => process!(d, py_get_attr, AttributesGenericIterator, kwargs),
            GenericMapping::PyMapping(d) => process!(d, py_get_mapping_item, MappingGenericIterator),
            GenericMapping::JsonObject(d) => process!(d, json_get, JsonObjectGenericIterator),
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

    fn complete(&mut self, build_context: &BuildContext<CombinedValidator>) -> PyResult<()> {
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
