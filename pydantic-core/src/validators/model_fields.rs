use std::sync::Arc;

use pyo3::IntoPyObjectExt;
use pyo3::exceptions::PyKeyError;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::pybacked::PyBackedStr;
use pyo3::types::{PyDict, PySet, PyString, PyType};

use crate::build_tools::py_schema_err;
use crate::build_tools::{ExtraBehavior, is_strict, schema_or_config_same};
use crate::errors::{ErrorType, ErrorTypeDefaults, ValError, ValLineError, ValResult};
use crate::input::{BorrowInput, Input, PreparedFieldResults, ValidatedDict, ValidationMatch};
use crate::lookup_key::FieldLookupPaths;
use crate::lookup_key::LookupType;
use crate::tools::SchemaDict;
use crate::validators::shared::lookup_tree::LookupTree;

use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator, build_validator};

#[derive(Debug)]
struct Field {
    name: PyBackedStr,
    lookup_paths: FieldLookupPaths,
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
            let lookup_paths = FieldLookupPaths::new(validation_alias, name.clone())?;

            fields.push(Field {
                name,
                lookup_paths,
                validator,
                frozen: field_info.get_as::<bool>(intern!(py, "frozen"))?.unwrap_or(false),
            });
        }

        let lookup = LookupTree::from_fields(&fields, |field| &field.lookup_paths);

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
        Ok(self.validate_fields(py, input, dict, state)?.into_py_any(py)?)
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

type ValidatedModelFields<'py> = (Bound<'py, PyDict>, Option<Bound<'py, PyDict>>, Bound<'py, PySet>);

impl ModelFieldsValidator {
    fn validate_fields<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        dict: impl ValidatedDict<'py>,
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<ValidatedModelFields<'py>> {
        let extra_behavior = state.extra_behavior_or(self.extra_behavior);
        let model_dict = PyDict::new(py);
        let mut errors: Vec<ValLineError> = Vec::with_capacity(self.fields.len());
        let mut fields_set_vec = Vec::with_capacity(self.fields.len());
        let mut fields_set_count: usize = 0;

        let validate_by_alias = state.validate_by_alias_or(self.validate_by_alias);
        let validate_by_name = state.validate_by_name_or(self.validate_by_name);
        let lookup_type = LookupType::from_bools(validate_by_alias, validate_by_name)?;

        let mut prepared = dict.prepare_fields(&self.lookup, lookup_type, extra_behavior);

        {
            let state = &mut state.scoped_set_data(Some(model_dict.clone()));
            let state = &mut state.scoped_clear_field_error();

            for (index, field) in self.fields.iter().enumerate() {
                let state = &mut state.scoped_set_field_name(Some(field.name.as_py_str().bind(py).clone()));

                if let Some(lookup_result) = prepared.lookup(index, &field.lookup_paths).transpose() {
                    let (lookup_path, value) = match lookup_result {
                        Ok(value) => value,
                        Err(ValError::LineErrors(line_errors)) => {
                            for err in line_errors {
                                errors.push(err.with_outer_location(field.name.clone()));
                            }
                            continue;
                        }
                        Err(e) => {
                            return Err(e);
                        }
                    };

                    match field.validator.validate(py, value.borrow_input(), state) {
                        Ok(value) => {
                            model_dict.set_item(&field.name, value)?;
                            fields_set_vec.push(field.name.clone());
                            fields_set_count += 1;
                        }
                        Err(e) => {
                            state.has_field_error = true;
                            match e {
                                ValError::Omit => continue,
                                ValError::LineErrors(line_errors) => {
                                    for err in line_errors {
                                        errors.push(lookup_path.apply_error_loc(err, self.loc_by_alias, &field.name));
                                    }
                                }
                                err => return Err(err),
                            }
                        }
                    }
                    continue;
                }

                match field.validator.default_value(py, Some(field.name.clone()), state) {
                    Ok(Some(value)) => {
                        // Default value exists, and passed validation if required
                        model_dict.set_item(&field.name, value)?;
                    }
                    Ok(None) => {
                        // There was no default value
                        state.has_field_error = true;
                        let error_type = ErrorTypeDefaults::Missing;
                        let error_loc = field.lookup_paths.error_loc(lookup_type, self.loc_by_alias);
                        errors.push(ValLineError::new_with_full_loc(error_type, input, error_loc));
                    }
                    Err(ValError::Omit) => {}
                    Err(ValError::LineErrors(line_errors)) => {
                        state.has_field_error = true;
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

        let model_extra_dict_op = (extra_behavior == ExtraBehavior::Allow).then(|| PyDict::new(py));
        prepared.for_each_extra(|raw_key, value| {
            let either_str = match raw_key
                .borrow_input()
                .validate_str(true, false)
                .map(ValidationMatch::into_inner)
            {
                Ok(k) => k,
                Err(ValError::LineErrors(line_errors)) => {
                    for err in line_errors {
                        errors.push(
                            err.with_outer_location(raw_key.clone())
                                .with_type(ErrorTypeDefaults::InvalidKey),
                        );
                    }
                    return Ok(());
                }
                Err(err) => return Err(err),
            };
            let value = value.borrow_input();
            // Unknown / extra field
            match extra_behavior {
                ExtraBehavior::Forbid => {
                    errors.push(ValLineError::new_with_loc(
                        ErrorTypeDefaults::ExtraForbidden,
                        value,
                        raw_key.clone(),
                    ));
                }
                ExtraBehavior::Ignore => {}
                ExtraBehavior::Allow => {
                    let model_extra_dict = model_extra_dict_op.as_ref().unwrap();
                    let py_key = match &self.extras_keys_validator {
                        Some(validator) => match validator.validate(py, raw_key.borrow_input(), state) {
                            Ok(value) => value.cast_bound::<PyString>(py)?.clone(),
                            Err(ValError::LineErrors(line_errors)) => {
                                for err in line_errors {
                                    errors.push(err.with_outer_location(raw_key.clone()));
                                }
                                return Ok(());
                            }
                            Err(err) => return Err(err),
                        },
                        None => either_str.as_py_string(py, state.cache_str()),
                    };

                    if let Some(validator) = &self.extras_validator {
                        match validator.validate(py, value, state) {
                            Ok(value) => {
                                model_extra_dict.set_item(&py_key, value)?;
                                fields_set_vec.push(py_key.try_into()?);
                            }
                            Err(ValError::LineErrors(line_errors)) => {
                                for err in line_errors {
                                    errors.push(err.with_outer_location(raw_key.clone()));
                                }
                            }
                            Err(err) => return Err(err),
                        }
                    } else {
                        model_extra_dict.set_item(&py_key, value.to_object(py)?)?;
                        fields_set_vec.push(py_key.try_into()?);
                    }
                }
            }
            Ok(())
        })?;

        if !errors.is_empty() {
            Err(ValError::LineErrors(errors))
        } else {
            let fields_set = PySet::new(py, &fields_set_vec)?;
            state.add_fields_set(fields_set_count);

            Ok((model_dict, model_extra_dict_op, fields_set))
        }
    }
}
