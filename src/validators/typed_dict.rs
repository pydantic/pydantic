use pyo3::intern;
use pyo3::prelude::*;

use ahash::AHashSet;
use pyo3::exceptions::PyKeyError;
use pyo3::types::PyTuple;
use pyo3::types::{PyDict, PySet, PyString, PyType};

use crate::build_tools::{is_strict, py_err, schema_or_config, schema_or_config_same, ExtraBehavior, SchemaDict};
use crate::errors::{py_err_string, ErrorType, ValError, ValLineError, ValResult};
use crate::input::{
    AttributesGenericIterator, DictGenericIterator, GenericMapping, Input, JsonObjectGenericIterator,
    MappingGenericIterator,
};
use crate::lookup_key::LookupKey;
use crate::recursion_guard::RecursionGuard;

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
    extra_behavior: ExtraBehavior,
    extra_validator: Option<Box<CombinedValidator>>,
    strict: bool,
    from_attributes: bool,
    return_fields_set: bool,
    loc_by_alias: bool,
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

        let total =
            schema_or_config(schema, config, intern!(py, "total"), intern!(py, "typed_dict_total"))?.unwrap_or(true);
        let from_attributes = schema_or_config_same(schema, config, intern!(py, "from_attributes"))?.unwrap_or(false);
        let populate_by_name = schema_or_config_same(schema, config, intern!(py, "populate_by_name"))?.unwrap_or(false);

        let return_fields_set = schema.get_as(intern!(py, "return_fields_set"))?.unwrap_or(false);

        let extra_behavior = ExtraBehavior::from_schema_or_config(py, schema, config, ExtraBehavior::Ignore)?;

        let extra_validator = match (schema.get_item(intern!(py, "extra_validator")), &extra_behavior) {
            (Some(v), ExtraBehavior::Allow) => Some(Box::new(build_validator(v, config, build_context)?)),
            (Some(_), _) => return py_err!("extra_validator can only be used if extra_behavior=allow"),
            (_, _) => None,
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
            extra_behavior,
            extra_validator,
            strict,
            from_attributes,
            return_fields_set,
            loc_by_alias: config.get_as(intern!(py, "loc_by_alias"))?.unwrap_or(true),
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
        let mut used_keys: Option<AHashSet<&str>> = match (&self.extra_behavior, &dict) {
            (_, GenericMapping::PyGetAttr(_, _)) => None,
            (ExtraBehavior::Allow | ExtraBehavior::Forbid, _) => Some(AHashSet::with_capacity(self.fields.len())),
            _ => None,
        };

        macro_rules! process {
            ($dict:ident, $get_method:ident, $iter:ty $(,$kwargs:ident)?) => {{
                for field in &self.fields {
                    let extra = Extra {
                        data: Some(output_dict),
                        field_name: Some(&field.name),
                        ..*extra
                    };
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
                    if let Some((lookup_path, value)) = op_key_value {
                        if let Some(ref mut used_keys) = used_keys {
                            // key is "used" whether or not validation passes, since we want to skip this key in
                            // extra logic either way
                            used_keys.insert(lookup_path.first_key());
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
                                    errors.push(lookup_path.apply_error_loc(err, self.loc_by_alias, &field.name));
                                }
                            }
                            Err(err) => return Err(err),
                        }
                        continue;
                    } else if let Some(value) = field.validator.default_value(py, Some(field.name.as_str()), &extra, slots, recursion_guard)? {
                        output_dict.set_item(&field.name_py, value)?;
                    } else if field.required {
                        errors.push(field.lookup_key.error(
                            ErrorType::Missing,
                            input,
                            self.loc_by_alias,
                            &field.name
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

                        // Unknown / extra field
                        match self.extra_behavior {
                            ExtraBehavior::Forbid => {
                                errors.push(ValLineError::new_with_loc(
                                    ErrorType::ExtraForbidden,
                                    value,
                                    raw_key.as_loc_item(),
                                ));
                            }
                            ExtraBehavior::Ignore => {}
                            ExtraBehavior::Allow => {
                            let py_key = either_str.as_py_string(py);
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
                                };
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

    fn validate_assignment<'s, 'data: 's>(
        &'s self,
        py: Python<'data>,
        obj: &'data PyAny,
        field_name: &'data str,
        field_value: &'data PyAny,
        extra: &Extra,
        slots: &'data [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let dict: &PyDict = obj.downcast()?;

        let ok = |output: PyObject| {
            dict.set_item(field_name, output)?;
            Ok(dict.to_object(py))
        };

        let prepare_result = |result: ValResult<'data, PyObject>| match result {
            Ok(output) => ok(output),
            Err(ValError::LineErrors(line_errors)) => {
                let errors = line_errors
                    .into_iter()
                    .map(|e| e.with_outer_location(field_name.to_string().into()))
                    .collect();
                Err(ValError::LineErrors(errors))
            }
            Err(err) => Err(err),
        };

        // by using dict but removing the field in question, we match V1 behaviour
        let data_dict = dict.copy()?;
        if let Err(err) = data_dict.del_item(field_name) {
            // KeyError is fine here as the field might not be in the dict
            if !err.get_type(py).is(PyType::new::<PyKeyError>(py)) {
                return Err(err.into());
            }
        }

        let extra = Extra {
            data: Some(data_dict),
            field_name: Some(field_name),
            ..*extra
        };

        let new_data = if let Some(field) = self.fields.iter().find(|f| f.name == field_name) {
            if field.frozen {
                Err(ValError::new_with_loc(
                    ErrorType::FrozenField,
                    field_value,
                    field.name.to_string(),
                ))
            } else {
                prepare_result(
                    field
                        .validator
                        .validate(py, field_value, &extra, slots, recursion_guard),
                )
            }
        } else {
            // Handle extra (unknown) field
            // We partially use the extra_behavior for initialization / validation
            // to determine how to handle assignment
            // For models / typed dicts we forbid assigning extra attributes
            // unless the user explicitly set extra_behavior to 'allow'
            match self.extra_behavior {
                ExtraBehavior::Allow => match self.extra_validator {
                    Some(ref validator) => {
                        prepare_result(validator.validate(py, field_value, &extra, slots, recursion_guard))
                    }
                    None => ok(field_value.to_object(py)),
                },
                ExtraBehavior::Forbid | ExtraBehavior::Ignore => {
                    return Err(ValError::new_with_loc(
                        ErrorType::NoSuchAttribute {
                            attribute: field_name.to_string(),
                        },
                        field_value,
                        field_name.to_string(),
                    ))
                }
            }
        }?;
        if self.return_fields_set {
            let fields_set: &PySet = PySet::new(py, &[field_name.to_string()])?;
            Ok(PyTuple::new(py, [new_data, fields_set.to_object(py)]).to_object(py))
        } else {
            Ok(new_data)
        }
    }

    fn different_strict_behavior(
        &self,
        build_context: Option<&BuildContext<CombinedValidator>>,
        ultra_strict: bool,
    ) -> bool {
        self.fields
            .iter()
            .any(|f| f.validator.different_strict_behavior(build_context, ultra_strict))
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }

    fn complete(&mut self, build_context: &BuildContext<CombinedValidator>) -> PyResult<()> {
        self.fields
            .iter_mut()
            .try_for_each(|f| f.validator.complete(build_context))?;
        match &mut self.extra_validator {
            Some(v) => v.complete(build_context),
            None => Ok(()),
        }
    }
}
