use pyo3::exceptions::PyKeyError;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PySet, PyString, PyType};

use ahash::AHashSet;

use crate::build_tools::py_schema_err;
use crate::build_tools::{is_strict, schema_or_config_same, ExtraBehavior};
use crate::errors::LocItem;
use crate::errors::{ErrorType, ErrorTypeDefaults, ValError, ValLineError, ValResult};
use crate::input::ConsumeIterator;
use crate::input::{BorrowInput, Input, ValidatedDict, ValidationMatch};
use crate::lookup_key::LookupKey;
use crate::tools::SchemaDict;

use super::{build_validator, BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

#[derive(Debug)]
struct Field {
    name: String,
    lookup_key: LookupKey,
    name_py: Py<PyString>,
    validator: CombinedValidator,
    frozen: bool,
}

impl_py_gc_traverse!(Field { validator });

#[derive(Debug)]
pub struct ModelFieldsValidator {
    fields: Vec<Field>,
    model_name: String,
    extra_behavior: ExtraBehavior,
    extras_validator: Option<Box<CombinedValidator>>,
    strict: bool,
    from_attributes: bool,
    loc_by_alias: bool,
}

impl BuildValidator for ModelFieldsValidator {
    const EXPECTED_TYPE: &'static str = "model-fields";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let strict = is_strict(schema, config)?;

        let from_attributes = schema_or_config_same(schema, config, intern!(py, "from_attributes"))?.unwrap_or(false);
        let populate_by_name = schema_or_config_same(schema, config, intern!(py, "populate_by_name"))?.unwrap_or(false);

        let extra_behavior = ExtraBehavior::from_schema_or_config(py, schema, config, ExtraBehavior::Ignore)?;

        let extras_validator = match (schema.get_item(intern!(py, "extras_schema"))?, &extra_behavior) {
            (Some(v), ExtraBehavior::Allow) => Some(Box::new(build_validator(&v, config, definitions)?)),
            (Some(_), _) => return py_schema_err!("extras_schema can only be used if extra_behavior=allow"),
            (_, _) => None,
        };
        let model_name: String = schema
            .get_as(intern!(py, "model_name"))?
            .unwrap_or_else(|| "Model".to_string());

        let fields_dict: Bound<'_, PyDict> = schema.get_as_req(intern!(py, "fields"))?;
        let mut fields: Vec<Field> = Vec::with_capacity(fields_dict.len());

        for (key, value) in fields_dict {
            let field_info = value.downcast::<PyDict>()?;
            let field_name_py: Bound<'_, PyString> = key.extract()?;
            let field_name = field_name_py.to_str()?;

            let schema = field_info.get_as_req(intern!(py, "schema"))?;

            let validator = match build_validator(&schema, config, definitions) {
                Ok(v) => v,
                Err(err) => return py_schema_err!("Field \"{}\":\n  {}", field_name, err),
            };

            let lookup_key = match field_info.get_item(intern!(py, "validation_alias"))? {
                Some(alias) => {
                    let alt_alias = if populate_by_name { Some(field_name) } else { None };
                    LookupKey::from_py(py, &alias, alt_alias)?
                }
                None => LookupKey::from_string(py, field_name),
            };

            fields.push(Field {
                name: field_name.to_string(),
                lookup_key,
                name_py: field_name_py.into(),
                validator,
                frozen: field_info.get_as::<bool>(intern!(py, "frozen"))?.unwrap_or(false),
            });
        }

        Ok(Self {
            fields,
            model_name,
            extra_behavior,
            extras_validator,
            strict,
            from_attributes,
            loc_by_alias: config.get_as(intern!(py, "loc_by_alias"))?.unwrap_or(true),
        }
        .into())
    }
}

impl_py_gc_traverse!(ModelFieldsValidator {
    fields,
    extras_validator
});

impl Validator for ModelFieldsValidator {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<PyObject> {
        let strict = state.strict_or(self.strict);
        let from_attributes = state.extra().from_attributes.unwrap_or(self.from_attributes);

        // we convert the DictType error to a ModelType error
        let dict = match input.validate_model_fields(strict, from_attributes) {
            Ok(d) => d,
            Err(ValError::LineErrors(errors)) => {
                let errors: Vec<ValLineError> = errors
                    .into_iter()
                    .map(|e| match e.error_type {
                        ErrorType::DictType { .. } => {
                            let mut e = e;
                            e.error_type = ErrorType::ModelType {
                                class_name: self.model_name.clone(),
                                context: None,
                            };
                            e
                        }
                        _ => e,
                    })
                    .collect();
                return Err(ValError::LineErrors(errors));
            }
            Err(err) => return Err(err),
        };

        let model_dict = PyDict::new_bound(py);
        let mut model_extra_dict_op: Option<Bound<PyDict>> = None;
        let mut errors: Vec<ValLineError> = Vec::with_capacity(self.fields.len());
        let mut fields_set_vec: Vec<Py<PyString>> = Vec::with_capacity(self.fields.len());

        // we only care about which keys have been used if we're iterating over the object for extra after
        // the first pass
        let mut used_keys: Option<AHashSet<&str>> =
            if self.extra_behavior == ExtraBehavior::Ignore || dict.is_py_get_attr() {
                None
            } else {
                Some(AHashSet::with_capacity(self.fields.len()))
            };

        {
            let state = &mut state.rebind_extra(|extra| extra.data = Some(model_dict.clone()));

            for field in &self.fields {
                let op_key_value = match dict.get_item(&field.lookup_key) {
                    Ok(v) => v,
                    Err(ValError::LineErrors(line_errors)) => {
                        for err in line_errors {
                            errors.push(err.with_outer_location(&field.name));
                        }
                        continue;
                    }
                    Err(err) => return Err(err),
                };
                if let Some((lookup_path, value)) = op_key_value {
                    if let Some(ref mut used_keys) = used_keys {
                        // key is "used" whether or not validation passes, since we want to skip this key in
                        // extra logic either way
                        used_keys.insert(lookup_path.first_key());
                    }
                    match field.validator.validate(py, value.borrow_input(), state) {
                        Ok(value) => {
                            model_dict.set_item(&field.name_py, value)?;
                            fields_set_vec.push(field.name_py.clone_ref(py));
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
                }

                match field.validator.default_value(py, Some(field.name.as_str()), state) {
                    Ok(Some(value)) => {
                        // Default value exists, and passed validation if required
                        model_dict.set_item(&field.name_py, value)?;
                    }
                    Ok(None) => {
                        // This means there was no default value
                        errors.push(field.lookup_key.error(
                            ErrorTypeDefaults::Missing,
                            input,
                            self.loc_by_alias,
                            &field.name,
                        ));
                    }
                    Err(ValError::Omit) => continue,
                    Err(ValError::LineErrors(line_errors)) => {
                        for err in line_errors {
                            // Note: this will always use the field name even if there is an alias
                            // However, we don't mind so much because this error can only happen if the
                            // default value fails validation, which is arguably a developer error.
                            // We could try to "fix" this in the future if desired.
                            errors.push(err);
                        }
                    }
                    Err(err) => return Err(err),
                }
            }
        }

        if let Some(used_keys) = used_keys {
            struct ValidateToModelExtra<'a, 's, 'py> {
                py: Python<'py>,
                used_keys: AHashSet<&'a str>,
                errors: &'a mut Vec<ValLineError>,
                fields_set_vec: &'a mut Vec<Py<PyString>>,
                extra_behavior: ExtraBehavior,
                extras_validator: Option<&'a CombinedValidator>,
                state: &'a mut ValidationState<'s, 'py>,
            }

            impl<'py, Key, Value> ConsumeIterator<ValResult<(Key, Value)>> for ValidateToModelExtra<'_, '_, 'py>
            where
                Key: BorrowInput<'py> + Clone + Into<LocItem>,
                Value: BorrowInput<'py>,
            {
                type Output = ValResult<Bound<'py, PyDict>>;
                fn consume_iterator(
                    self,
                    iterator: impl Iterator<Item = ValResult<(Key, Value)>>,
                ) -> ValResult<Bound<'py, PyDict>> {
                    let model_extra_dict = PyDict::new_bound(self.py);
                    for item_result in iterator {
                        let (raw_key, value) = item_result?;
                        let either_str = match raw_key
                            .borrow_input()
                            .validate_str(true, false)
                            .map(ValidationMatch::into_inner)
                        {
                            Ok(k) => k,
                            Err(ValError::LineErrors(line_errors)) => {
                                for err in line_errors {
                                    self.errors.push(
                                        err.with_outer_location(raw_key.clone())
                                            .with_type(ErrorTypeDefaults::InvalidKey),
                                    );
                                }
                                continue;
                            }
                            Err(err) => return Err(err),
                        };
                        let cow = either_str.as_cow()?;
                        if self.used_keys.contains(cow.as_ref()) {
                            continue;
                        }

                        let value = value.borrow_input();
                        // Unknown / extra field
                        match self.extra_behavior {
                            ExtraBehavior::Forbid => {
                                self.errors.push(ValLineError::new_with_loc(
                                    ErrorTypeDefaults::ExtraForbidden,
                                    value,
                                    raw_key.clone(),
                                ));
                            }
                            ExtraBehavior::Ignore => {}
                            ExtraBehavior::Allow => {
                                let py_key = either_str.as_py_string(self.py);
                                if let Some(validator) = self.extras_validator {
                                    match validator.validate(self.py, value, self.state) {
                                        Ok(value) => {
                                            model_extra_dict.set_item(&py_key, value)?;
                                            self.fields_set_vec.push(py_key.into());
                                        }
                                        Err(ValError::LineErrors(line_errors)) => {
                                            for err in line_errors {
                                                self.errors.push(err.with_outer_location(raw_key.clone()));
                                            }
                                        }
                                        Err(err) => return Err(err),
                                    }
                                } else {
                                    model_extra_dict.set_item(&py_key, value.to_object(self.py))?;
                                    self.fields_set_vec.push(py_key.into());
                                };
                            }
                        }
                    }
                    Ok(model_extra_dict)
                }
            }

            let model_extra_dict = dict.iterate(ValidateToModelExtra {
                py,
                used_keys,
                errors: &mut errors,
                fields_set_vec: &mut fields_set_vec,
                extra_behavior: self.extra_behavior,
                extras_validator: self.extras_validator.as_deref(),
                state,
            })??;

            if matches!(self.extra_behavior, ExtraBehavior::Allow) {
                model_extra_dict_op = Some(model_extra_dict);
            }
        }

        if !errors.is_empty() {
            Err(ValError::LineErrors(errors))
        } else {
            let fields_set = PySet::new_bound(py, &fields_set_vec)?;

            // if we have extra=allow, but we didn't create a dict because we were validating
            // from attributes, set it now so __pydantic_extra__ is always a dict if extra=allow
            if matches!(self.extra_behavior, ExtraBehavior::Allow) && model_extra_dict_op.is_none() {
                model_extra_dict_op = Some(PyDict::new_bound(py));
            };

            Ok((model_dict, model_extra_dict_op, fields_set).to_object(py))
        }
    }

    fn validate_assignment<'py>(
        &self,
        py: Python<'py>,
        obj: &Bound<'py, PyAny>,
        field_name: &str,
        field_value: &Bound<'py, PyAny>,
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<PyObject> {
        let dict = obj.downcast::<PyDict>()?;

        let get_updated_dict = |output: PyObject| {
            dict.set_item(field_name, output)?;
            Ok(dict)
        };

        let prepare_result = |result: ValResult<PyObject>| match result {
            Ok(output) => get_updated_dict(output),
            Err(ValError::LineErrors(line_errors)) => {
                let errors = line_errors
                    .into_iter()
                    .map(|e| e.with_outer_location(field_name))
                    .collect();
                Err(ValError::LineErrors(errors))
            }
            Err(err) => Err(err),
        };

        // by using dict but removing the field in question, we match V1 behaviour
        let data_dict = dict.copy()?;
        if let Err(err) = data_dict.del_item(field_name) {
            // KeyError is fine here as the field might not be in the dict
            if !err.get_type_bound(py).is(&PyType::new_bound::<PyKeyError>(py)) {
                return Err(err.into());
            }
        }

        let new_data = {
            let state = &mut state.rebind_extra(move |extra| extra.data = Some(data_dict));

            if let Some(field) = self.fields.iter().find(|f| f.name == field_name) {
                if field.frozen {
                    return Err(ValError::new_with_loc(
                        ErrorTypeDefaults::FrozenField,
                        field_value,
                        field.name.to_string(),
                    ));
                }

                prepare_result(field.validator.validate(py, field_value, state))?
            } else {
                // Handle extra (unknown) field
                // We partially use the extra_behavior for initialization / validation
                // to determine how to handle assignment
                // For models / typed dicts we forbid assigning extra attributes
                // unless the user explicitly set extra_behavior to 'allow'
                match self.extra_behavior {
                    ExtraBehavior::Allow => match self.extras_validator {
                        Some(ref validator) => prepare_result(validator.validate(py, field_value, state))?,
                        None => get_updated_dict(field_value.to_object(py))?,
                    },
                    ExtraBehavior::Forbid | ExtraBehavior::Ignore => {
                        return Err(ValError::new_with_loc(
                            ErrorType::NoSuchAttribute {
                                attribute: field_name.to_string(),
                                context: None,
                            },
                            field_value,
                            field_name.to_string(),
                        ))
                    }
                }
            }
        };

        let new_extra = match &self.extra_behavior {
            ExtraBehavior::Allow => {
                let non_extra_data = PyDict::new_bound(py);
                self.fields.iter().for_each(|f| {
                    let popped_value = PyAnyMethods::get_item(&**new_data, &f.name).unwrap();
                    new_data.del_item(&f.name).unwrap();
                    non_extra_data.set_item(&f.name, popped_value).unwrap();
                });
                let new_extra = new_data.copy()?;
                new_data.clear();
                new_data.update(non_extra_data.as_mapping())?;
                new_extra.to_object(py)
            }
            _ => py.None(),
        };

        let fields_set = PySet::new_bound(py, &[field_name.to_string()])?;
        Ok((new_data.to_object(py), new_extra, fields_set.to_object(py)).to_object(py))
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}
