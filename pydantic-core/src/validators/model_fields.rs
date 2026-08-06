use std::sync::Arc;

use ahash::AHashSet;
use ahash::RandomState;
use indexmap::IndexMap;
use jiter::JsonObject;
use jiter::JsonValue;
use pyo3::IntoPyObjectExt;
use pyo3::exceptions::PyKeyError;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::pybacked::PyBackedStr;
use pyo3::types::{PyDict, PySet, PyType};

use crate::build_tools::py_schema_err;
use crate::build_tools::{ExtraBehavior, is_strict, schema_or_config_same};
use crate::errors::LocItem;
use crate::errors::{ErrorType, ErrorTypeDefaults, ValError, ValLineError, ValResult};
use crate::input::ConsumeIterator;
use crate::input::{BorrowInput, Input, ValidatedDict};
use crate::lookup_key::LookupPath;
use crate::lookup_key::LookupPathCollection;
use crate::lookup_key::LookupType;
use crate::tools::SchemaDict;
use crate::tools::new_py_string;
use crate::validators::shared::lookup_tree::LookupFieldInfo;
use crate::validators::shared::lookup_tree::LookupTree;

use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator, build_validator};

#[derive(Debug)]
struct Field {
    name: PyBackedStr,
    lookup_path_collection: LookupPathCollection,
    validator: Arc<CombinedValidator>,
    frozen: bool,
}

impl_py_gc_traverse!(Field { validator });

#[derive(Debug)]
pub struct ModelFieldsValidator {
    fields: Vec<Field>,
    model_name: String,
    extra_behavior: ExtraBehavior,
    extras_validator: Option<Arc<CombinedValidator>>,
    extras_keys_validator: Option<Arc<CombinedValidator>>,
    strict: bool,
    from_attributes: bool,
    loc_by_alias: bool,
    lookup: LookupTree,
    validate_by_alias: Option<bool>,
    validate_by_name: Option<bool>,
}

impl BuildValidator for ModelFieldsValidator {
    const EXPECTED_TYPE: &'static str = "model-fields";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedValidator>>,
    ) -> PyResult<Arc<CombinedValidator>> {
        let py = schema.py();

        let strict = is_strict(schema, config)?;

        let from_attributes = schema_or_config_same(schema, config, intern!(py, "from_attributes"))?.unwrap_or(false);

        let extra_behavior = ExtraBehavior::from_schema_or_config(py, schema, config, ExtraBehavior::Ignore)?;

        let extras_validator = match (schema.get_item(intern!(py, "extras_schema"))?, &extra_behavior) {
            (Some(v), ExtraBehavior::Allow) => Some(build_validator(&v, config, definitions)?),
            (Some(_), _) => return py_schema_err!("extras_schema can only be used if extra_behavior=allow"),
            (_, _) => None,
        };
        let extras_keys_validator = match (schema.get_item(intern!(py, "extras_keys_schema"))?, &extra_behavior) {
            (Some(v), ExtraBehavior::Allow) => Some(build_validator(&v, config, definitions)?),
            (Some(_), _) => return py_schema_err!("extras_keys_schema can only be used if extra_behavior=allow"),
            (_, _) => None,
        };
        let model_name: String = schema
            .get_as(intern!(py, "model_name"))?
            .unwrap_or_else(|| "Model".to_string());

        let fields_dict: Bound<'_, PyDict> = schema.get_as_req(intern!(py, "fields"))?;
        let mut fields: Vec<Field> = Vec::with_capacity(fields_dict.len());

        for (key, value) in fields_dict {
            let field_info = value.cast::<PyDict>()?;
            let name: PyBackedStr = key.extract()?;

            let schema = field_info.get_as_req(intern!(py, "schema"))?;

            let validator = match build_validator(&schema, config, definitions) {
                Ok(v) => v,
                Err(err) => return py_schema_err!("Field \"{name}\":\n  {err}"),
            };

            let validation_alias = field_info.get_as(intern!(py, "validation_alias"))?;
            let lookup_path_collection = LookupPathCollection::new(validation_alias, name.clone())?;

            fields.push(Field {
                name,
                lookup_path_collection,
                validator,
                frozen: field_info.get_as::<bool>(intern!(py, "frozen"))?.unwrap_or(false),
            });
        }

        let lookup = LookupTree::from_fields(&fields, |field| &field.lookup_path_collection);

        Ok(CombinedValidator::ModelFields(Self {
            fields,
            model_name,
            extra_behavior,
            extras_validator,
            extras_keys_validator,
            strict,
            from_attributes,
            loc_by_alias: config.get_as(intern!(py, "loc_by_alias"))?.unwrap_or(true),
            lookup,
            validate_by_alias: config.get_as(intern!(py, "validate_by_alias"))?,
            validate_by_name: config.get_as(intern!(py, "validate_by_name"))?,
        })
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
    ) -> ValResult<Py<PyAny>> {
        // this validator does not yet support partial validation, disable it to avoid incorrect results
        state.allow_partial = false.into();

        let strict = state.strict_or(self.strict);
        let from_attributes = state.extra().from_attributes.unwrap_or(self.from_attributes);

        let extra_behavior = state.extra_behavior_or(self.extra_behavior);
        let validate_by_alias = state.validate_by_alias_or(self.validate_by_alias);
        let validate_by_name = state.validate_by_name_or(self.validate_by_name);
        let lookup_type = LookupType::from_bools(validate_by_alias, validate_by_name)?;

        let model_dict = PyDict::new(py);
        let extra_validator = match extra_behavior {
            ExtraBehavior::Forbid => ModelExtraValidator::Forbid,
            ExtraBehavior::Ignore => ModelExtraValidator::Ignore,
            ExtraBehavior::Allow => ModelExtraValidator::Allow {
                extra_dict: PyDict::new(py),
                keys_validator: self.extras_keys_validator.as_deref(),
                values_validator: self.extras_validator.as_deref(),
            },
        };

        let state = &mut state.scoped_set_data(Some(model_dict.clone()));
        let state = &mut state.scoped_clear_field_error();

        let mut state = ModelFieldsValidationState {
            lookup_type,
            model_dict,
            extra_validator,
            fields_set: PySet::empty(py)?,
            fields_set_count: 0,
            state,
            errors: Vec::new(),
            loc_by_alias: self.loc_by_alias,
        };

        if let Some(json_input) = input.as_json() {
            let JsonValue::Object(json_object) = json_input else {
                return Err(ValError::new(
                    ErrorType::ModelType {
                        context: None,
                        class_name: self.model_name.clone(),
                    },
                    input,
                ));
            };
            self.validate_json_by_iteration(py, json_input, json_object, &mut state)?;
        } else {
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
            self.validate_by_get_item(py, input, dict, &mut state)?;
        }

        if !state.errors.is_empty() {
            return Err(ValError::LineErrors(state.errors));
        }

        state.state.add_fields_set(state.fields_set_count);
        let extra_dict = match state.extra_validator {
            ModelExtraValidator::Allow { extra_dict, .. } => Some(extra_dict),
            _ => None,
        };

        Ok((state.model_dict, extra_dict, state.fields_set).into_py_any(py)?)
    }

    fn validate_assignment<'py>(
        &self,
        py: Python<'py>,
        obj: &Bound<'py, PyAny>,
        field_name: &PyBackedStr,
        field_value: &Bound<'py, PyAny>,
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Py<PyAny>> {
        let dict = obj.cast::<PyDict>()?;
        let extra_behavior = state.extra_behavior_or(self.extra_behavior);

        let get_updated_dict = |output: &Bound<'py, PyAny>| {
            dict.set_item(field_name, output)?;
            Ok(dict)
        };

        let prepare_result = |result: ValResult<Py<PyAny>>| match result {
            Ok(output) => get_updated_dict(&output.into_bound(py)),
            Err(ValError::LineErrors(line_errors)) => {
                let errors = line_errors
                    .into_iter()
                    .map(|e| e.with_outer_location(field_name.clone()))
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

        let new_data = {
            let state = &mut state.scoped_set_data(Some(data_dict));

            if let Some(field) = self.fields.iter().find(|f| &*f.name == field_name) {
                if field.frozen {
                    return Err(ValError::new_with_loc(
                        ErrorTypeDefaults::FrozenField,
                        field_value,
                        &*field.name,
                    ));
                }

                let state = &mut state.scoped_set_field_name(Some(field.name.as_py_str().bind(py).clone()));

                prepare_result(field.validator.validate(py, field_value, state))?
            } else {
                // Handle extra (unknown) field
                // We partially use the extra_behavior for initialization / validation
                // to determine how to handle assignment
                // For models / typed dicts we forbid assigning extra attributes
                // unless the user explicitly set extra_behavior to 'allow'
                match extra_behavior {
                    ExtraBehavior::Allow => match self.extras_validator {
                        Some(ref validator) => prepare_result(validator.validate(py, field_value, state))?,
                        None => get_updated_dict(field_value)?,
                    },
                    ExtraBehavior::Forbid | ExtraBehavior::Ignore => {
                        return Err(ValError::new_with_loc(
                            ErrorType::NoSuchAttribute {
                                attribute: field_name.to_string(),
                                context: None,
                            },
                            field_value,
                            field_name.to_string(),
                        ));
                    }
                }
            }
        };

        let new_extra = match &extra_behavior {
            ExtraBehavior::Allow => {
                let non_extra_data = PyDict::new(py);
                self.fields.iter().try_for_each(|f| -> PyResult<()> {
                    let Some(popped_value) = new_data.get_item(&f.name)? else {
                        // field not present in __dict__ for some reason; let the rest of the
                        // validation pipeline handle it later
                        return Ok(());
                    };
                    new_data.del_item(&f.name)?;
                    non_extra_data.set_item(&f.name, popped_value)?;
                    Ok(())
                })?;
                let new_extra = new_data.copy()?;
                new_data.clear();
                new_data.update(non_extra_data.as_mapping())?;
                new_extra.into()
            }
            _ => py.None(),
        };

        let fields_set = PySet::new(py, &[field_name.to_string()])?;
        Ok((new_data, new_extra, fields_set).into_py_any(py)?)
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}

impl ModelFieldsValidator {
    fn validate_by_get_item<'a, 'py>(
        &'a self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        dict: impl ValidatedDict<'py>,
        state: &mut ModelFieldsValidationState<'a, '_, 'py>,
    ) -> ValResult<()> {
        // we only care about which keys have been used if we're iterating over the object for extra after
        // the first pass
        let mut used_keys: Option<AHashSet<&str>> =
            if matches!(&state.extra_validator, ModelExtraValidator::Ignore) || dict.is_py_get_attr() {
                None
            } else {
                Some(AHashSet::with_capacity(self.fields.len()))
            };

        for field in &self.fields {
            let field_input = match field
                .lookup_path_collection
                .lookup_paths(state.lookup_type)
                .find_map(|path| {
                    let value = dict.get_item(path).transpose()?;
                    if let Some(used_keys) = used_keys.as_mut() {
                        // key is "used" whether or not validation passes, since we want to skip this key in
                        // extra logic either way
                        used_keys.insert(path.first_key());
                    }
                    Some(value.map(|v| (path, v)))
                })
                .transpose()
            {
                Ok(field_input) => field_input,
                Err(ValError::LineErrors(line_errors)) => {
                    for err in line_errors {
                        state.errors.push(err.with_outer_location(field.name.clone()));
                    }
                    continue;
                }
                Err(e) => return Err(e),
            };

            state.validate_field(py, input, field, field_input)?;
        }

        if let Some(used_keys) = used_keys {
            struct ValidateToModelExtra<'m, 'a, 's, 'py> {
                state: &'m mut ModelFieldsValidationState<'a, 's, 'py>,
                py: Python<'py>,
                used_keys: AHashSet<&'a str>,
            }

            impl<'py, Key, Value> ConsumeIterator<ValResult<(Key, Value)>> for ValidateToModelExtra<'_, '_, '_, 'py>
            where
                Key: BorrowInput<'py> + Clone + Into<LocItem>,
                Value: BorrowInput<'py>,
            {
                type Output = ValResult<()>;
                fn consume_iterator(self, iterator: impl Iterator<Item = ValResult<(Key, Value)>>) -> ValResult<()> {
                    for item_result in iterator {
                        let (raw_key, value) = item_result?;
                        let either_str = match raw_key.borrow_input().validate_str(true, false) {
                            Ok(k) => k.into_inner(),
                            Err(ValError::LineErrors(line_errors)) => {
                                for err in line_errors {
                                    self.state.errors.push(
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

                        // Unknown / extra field
                        self.state.validate_extra_key_value(self.py, &cow, value)?;
                    }
                    Ok(())
                }
            }

            dict.iterate(ValidateToModelExtra { state, py, used_keys })??;
        }

        Ok(())
    }

    fn validate_json_by_iteration<'py>(
        &self,
        py: Python<'py>,
        json_input: &JsonValue<'_>,
        json_object: &JsonObject<'_>,
        state: &mut ModelFieldsValidationState<'_, '_, 'py>,
    ) -> ValResult<()> {
        // expect json_input and json_object to be the same thing, just projected
        debug_assert!(matches!(&json_input, JsonValue::Object(j) if Arc::ptr_eq(j, json_object)));

        // Individual inputs for each field. There is some complicated decision making
        // around which field input to use if multiple lookup paths match:
        // - aliases are preferred over field names (if validating by alias)
        // - later inputs for *the same path* are preferred over earlier inputs
        //
        // Once the iteration is complete, the highest priority input for each field
        // is validated and the rest are propagated into extra (if necessary).
        let mut field_inputs: Vec<Option<(LookupFieldInfo, &JsonValue)>> =
            (0..self.fields.len()).map(|_| None).collect();

        // Buffer for possible extra data, `None` if ignoring extra. Extra data
        // is validated in order of appearance after all fields have been processed.
        let mut possible_extra = (!matches!(&state.extra_validator, ModelExtraValidator::Ignore))
            .then_some(IndexMap::with_hasher(RandomState::new()));

        for (key, value) in &**json_object {
            let mut might_be_extra = possible_extra.is_some();
            let key = key.as_ref();
            for (field_info, field_value) in self.lookup.iter_matches(key, value) {
                if !field_info.matches_lookup(state.lookup_type) {
                    continue;
                }

                let field_input = &mut field_inputs[field_info.field_index];

                // later inputs are preferred unless the existing input has come from a higher priority alias
                if let Some((existing_field_info, _)) = &field_input
                    && existing_field_info
                        .lookup_priority
                        .is_higher_priority_than(&field_info.lookup_priority)
                {
                    continue;
                }

                *field_input = Some((*field_info, field_value));

                if might_be_extra
                    && field_info
                        .lookup_priority
                        .is_maximum_priority_for_lookup_type(state.lookup_type)
                {
                    // this input is definitely going to consume the key, so we don't want to
                    // buffer it in possible_extra
                    might_be_extra = false;
                }
            }

            if might_be_extra {
                let possible_extra = possible_extra.as_mut().expect("must be Some if might_be_extra is true");
                match possible_extra.entry(key) {
                    indexmap::map::Entry::Vacant(entry) => {
                        // when recording in possible_extra, we also record a boolean which is used to
                        // skip extra for any keys consumed by a field input (see below)
                        entry.insert((value, false));
                    }
                    indexmap::map::Entry::Occupied(mut existing) => {
                        // if the key is already in possible_extra, we update the value to the latest one
                        existing.get_mut().0 = value;
                    }
                }
            }
        }

        // handle all inputs for fields
        for (field, field_input) in std::iter::zip(&self.fields, field_inputs) {
            let field_input_with_lookup_path = field_input.map(|(field_info, value)| {
                let lookup_path = if let Some(alias_index) = field_info.alias_index() {
                    &field.lookup_path_collection.by_alias[alias_index]
                } else {
                    &field.lookup_path_collection.by_name
                };

                // mark consumed any existing possible extra for this lookup path's first key
                if let Some(possible_extra) = possible_extra.as_mut()
                    && let Some(extra) = possible_extra.get_mut(lookup_path.first_key())
                {
                    // marking true is cheaper than removing from the index map
                    extra.1 = true;
                }

                (lookup_path, value)
            });

            state.validate_field(py, json_input, field, field_input_with_lookup_path)?;
        }

        // handle extra fields if necessary
        for (key, (value, consumed)) in possible_extra.into_iter().flatten() {
            if consumed {
                // this key was consumed by a field input, so we don't want to treat it as extra
                continue;
            }
            state.validate_extra_key_value(py, key, value)?;
        }

        Ok(())
    }
}

/// Collection of all state needed during validation of model fields
struct ModelFieldsValidationState<'a, 's, 'py> {
    lookup_type: LookupType,
    model_dict: Bound<'py, PyDict>,
    extra_validator: ModelExtraValidator<'a, 'py>,
    fields_set: Bound<'py, PySet>,
    fields_set_count: usize,
    state: &'a mut ValidationState<'s, 'py>,
    errors: Vec<ValLineError>,
    loc_by_alias: bool,
}

enum ModelExtraValidator<'a, 'py> {
    Forbid,
    Ignore,
    Allow {
        extra_dict: Bound<'py, PyDict>,
        keys_validator: Option<&'a CombinedValidator>,
        values_validator: Option<&'a CombinedValidator>,
    },
}

impl<'py> ModelFieldsValidationState<'_, '_, 'py> {
    /// Attempt to validate a single field.
    ///
    /// Error return is for unexpected errors to be propagated upward; validation
    /// errors are captured in `self.errors`.
    fn validate_field(
        &mut self,
        py: Python<'py>,
        full_input: &(impl Input<'py> + ?Sized),
        field: &Field,
        field_input: Option<(&LookupPath, impl BorrowInput<'py>)>,
    ) -> PyResult<()> {
        let state = &mut self
            .state
            .scoped_set_field_name(Some(field.name.as_py_str().bind(py).clone()));

        if let Some((lookup_path, value)) = field_input {
            match field.validator.validate(py, value.borrow_input(), state) {
                Ok(value) => {
                    self.model_dict.set_item(&field.name, value)?;
                    self.fields_set.add(&field.name)?;
                    self.fields_set_count += 1;
                    return Ok(());
                }
                // will fall through to default value logic below
                Err(ValError::UseDefault) => {}
                Err(ValError::Omit) => return Ok(()),
                Err(ValError::InternalErr(e)) => return Err(e),
                Err(ValError::LineErrors(line_errors)) => {
                    state.has_field_error = true;
                    for err in line_errors {
                        self.errors
                            .push(lookup_path.apply_error_loc(err, self.loc_by_alias, &field.name));
                    }
                    return Ok(());
                }
            }
        }

        // No value, or `UseDefault` raised, try default pathway
        match field.validator.default_value(py, Some(field.name.clone()), state) {
            Ok(Some(value)) => {
                // Default value exists, and passed validation if required
                self.model_dict.set_item(&field.name, value)?;
                Ok(())
            }
            Ok(None) | Err(ValError::UseDefault) => {
                // There was no default value available
                state.has_field_error = true;
                let error_type = ErrorTypeDefaults::Missing;
                let error_loc = field
                    .lookup_path_collection
                    .error_loc(self.lookup_type, self.loc_by_alias);
                self.errors
                    .push(ValLineError::new_with_full_loc(error_type, full_input, error_loc));
                Ok(())
            }
            Err(ValError::Omit) => Ok(()),
            Err(ValError::LineErrors(line_errors)) => {
                state.has_field_error = true;
                for err in line_errors {
                    // Note: this will always use the field name even if there is an alias
                    // However, we don't mind so much because this error can only happen if the
                    // default value fails validation, which is arguably a developer error.
                    // We could try to "fix" this in the future if desired.
                    self.errors.push(err);
                }
                Ok(())
            }
            Err(ValError::InternalErr(e)) => Err(e),
        }
    }

    fn validate_extra_key_value<Value>(&mut self, py: Python<'py>, key: &str, value: Value) -> ValResult<()>
    where
        Value: BorrowInput<'py>,
    {
        let Self {
            extra_validator,
            state,
            errors,
            fields_set,
            ..
        } = self;
        let state = &mut **state;
        match extra_validator {
            ModelExtraValidator::Forbid => {
                errors.push(ValLineError::new_with_loc(
                    ErrorTypeDefaults::ExtraForbidden,
                    value,
                    key,
                ));
                Ok(())
            }
            ModelExtraValidator::Ignore => Ok(()),
            ModelExtraValidator::Allow {
                extra_dict,
                keys_validator,
                values_validator,
            } => {
                // Buffer `validated_key` in an option to allow for validation of the value even if the
                // key is invalid.
                let validated_key = if let Some(validator) = keys_validator {
                    match validator.validate(py, key, state) {
                        Ok(value) => Some(value),
                        Err(ValError::LineErrors(line_errors)) => {
                            for err in line_errors {
                                errors.push(err.with_outer_location(key));
                            }
                            None
                        }
                        Err(err) => return Err(err),
                    }
                } else {
                    Some(new_py_string(py, key, state.cache_str()).into_any().unbind())
                };
                let validated_value = if let Some(validator) = values_validator {
                    match validator.validate(py, value.borrow_input(), state) {
                        Ok(value) => value,
                        Err(ValError::LineErrors(line_errors)) => {
                            for err in line_errors {
                                errors.push(err.with_outer_location(key));
                            }
                            return Ok(());
                        }
                        Err(err) => return Err(err),
                    }
                } else {
                    value.borrow_input().to_object(py)?.unbind()
                };
                if let Some(validated_key) = validated_key {
                    extra_dict.set_item(&validated_key, validated_value)?;
                    fields_set.add(validated_key)?;
                }
                Ok(())
            }
        }
    }
}
