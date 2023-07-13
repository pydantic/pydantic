use pyo3::exceptions::PyKeyError;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PySet, PyString, PyType};

use ahash::AHashSet;

use crate::build_tools::py_schema_err;
use crate::build_tools::{is_strict, schema_or_config_same, ExtraBehavior};
use crate::errors::{py_err_string, ErrorType, ValError, ValLineError, ValResult};
use crate::input::{
    AttributesGenericIterator, DictGenericIterator, GenericMapping, Input, JsonObjectGenericIterator,
    MappingGenericIterator,
};
use crate::lookup_key::LookupKey;
use crate::recursion_guard::RecursionGuard;
use crate::tools::SchemaDict;

use super::{build_validator, BuildValidator, CombinedValidator, Definitions, DefinitionsBuilder, Extra, Validator};

#[derive(Debug, Clone)]
struct Field {
    name: String,
    lookup_key: LookupKey,
    name_py: Py<PyString>,
    validator: CombinedValidator,
    frozen: bool,
}

#[derive(Debug, Clone)]
pub struct ModelFieldsValidator {
    fields: Vec<Field>,
    model_name: String,
    extra_behavior: ExtraBehavior,
    extra_validator: Option<Box<CombinedValidator>>,
    strict: bool,
    from_attributes: bool,
    loc_by_alias: bool,
}

impl BuildValidator for ModelFieldsValidator {
    const EXPECTED_TYPE: &'static str = "model-fields";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let strict = is_strict(schema, config)?;

        let from_attributes = schema_or_config_same(schema, config, intern!(py, "from_attributes"))?.unwrap_or(false);
        let populate_by_name = schema_or_config_same(schema, config, intern!(py, "populate_by_name"))?.unwrap_or(false);

        let extra_behavior = ExtraBehavior::from_schema_or_config(py, schema, config, ExtraBehavior::Ignore)?;

        let extra_validator = match (schema.get_item(intern!(py, "extra_validator")), &extra_behavior) {
            (Some(v), ExtraBehavior::Allow) => Some(Box::new(build_validator(v, config, definitions)?)),
            (Some(_), _) => return py_schema_err!("extra_validator can only be used if extra_behavior=allow"),
            (_, _) => None,
        };
        let model_name: String = schema
            .get_as(intern!(py, "model_name"))?
            .unwrap_or_else(|| "Model".to_string());

        let fields_dict: &PyDict = schema.get_as_req(intern!(py, "fields"))?;
        let mut fields: Vec<Field> = Vec::with_capacity(fields_dict.len());

        for (key, value) in fields_dict.iter() {
            let field_info: &PyDict = value.downcast()?;
            let field_name: &str = key.extract()?;

            let schema = field_info.get_as_req(intern!(py, "schema"))?;

            let validator = match build_validator(schema, config, definitions) {
                Ok(v) => v,
                Err(err) => return py_schema_err!("Field \"{}\":\n  {}", field_name, err),
            };

            let lookup_key = match field_info.get_item(intern!(py, "validation_alias")) {
                Some(alias) => {
                    let alt_alias = if populate_by_name { Some(field_name) } else { None };
                    LookupKey::from_py(py, alias, alt_alias)?
                }
                None => LookupKey::from_string(py, field_name),
            };

            fields.push(Field {
                name: field_name.to_string(),
                lookup_key,
                name_py: PyString::intern(py, field_name).into(),
                validator,
                frozen: field_info.get_as::<bool>(intern!(py, "frozen"))?.unwrap_or(false),
            });
        }

        Ok(Self {
            fields,
            model_name,
            extra_behavior,
            extra_validator,
            strict,
            from_attributes,
            loc_by_alias: config.get_as(intern!(py, "loc_by_alias"))?.unwrap_or(true),
        }
        .into())
    }
}

impl Validator for ModelFieldsValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        definitions: &'data Definitions<CombinedValidator>,
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let strict = extra.strict.unwrap_or(self.strict);
        let from_attributes = extra.from_attributes.unwrap_or(self.from_attributes);

        // we convert the DictType error to a ModelType error
        let dict = match input.validate_model_fields(strict, from_attributes) {
            Ok(d) => d,
            Err(ValError::LineErrors(errors)) => {
                let errors: Vec<ValLineError> = errors
                    .into_iter()
                    .map(|e| match e.error_type {
                        ErrorType::DictType => {
                            let mut e = e;
                            e.error_type = ErrorType::ModelType {
                                class_name: self.model_name.clone(),
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

        let model_dict = PyDict::new(py);
        let mut model_extra_dict_op: Option<&PyDict> = None;
        let mut errors: Vec<ValLineError> = Vec::with_capacity(self.fields.len());
        let mut fields_set_vec: Vec<Py<PyString>> = Vec::with_capacity(self.fields.len());

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
                        data: Some(model_dict),
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
                            .validate(py, value, &extra, definitions, recursion_guard)
                        {
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
                    } else if let Some(value) = field.validator.default_value(py, Some(field.name.as_str()), &extra, definitions, recursion_guard)? {
                        model_dict.set_item(&field.name_py, value)?;
                    } else {
                        errors.push(field.lookup_key.error(
                            ErrorType::Missing,
                            input,
                            self.loc_by_alias,
                            &field.name
                        ));
                    }
                }

                if let Some(ref mut used_keys) = used_keys {
                    let model_extra_dict = PyDict::new(py);
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
                                    match validator.validate(py, value, &extra, definitions, recursion_guard) {
                                        Ok(value) => {
                                            model_extra_dict.set_item(py_key, value)?;
                                            fields_set_vec.push(py_key.into_py(py));
                                        }
                                        Err(ValError::LineErrors(line_errors)) => {
                                            for err in line_errors {
                                                errors.push(err.with_outer_location(raw_key.as_loc_item()));
                                            }
                                        }
                                        Err(err) => return Err(err),
                                    }
                                } else {
                                    model_extra_dict.set_item(py_key, value.to_object(py))?;
                                    fields_set_vec.push(py_key.into_py(py));
                                };
                            }
                        }
                    }
                    if matches!(self.extra_behavior, ExtraBehavior::Allow) {
                        model_extra_dict_op = Some(model_extra_dict);
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
        } else {
            let fields_set = PySet::new(py, &fields_set_vec)?;

            // if we have extra=allow, but we didn't create a dict because we were validating
            // from attributes, set it now so __pydantic_extra__ is always a dict if extra=allow
            if matches!(self.extra_behavior, ExtraBehavior::Allow) && model_extra_dict_op.is_none() {
                model_extra_dict_op = Some(PyDict::new(py));
            };

            Ok((model_dict, model_extra_dict_op, fields_set).to_object(py))
        }
    }

    fn validate_assignment<'s, 'data: 's>(
        &'s self,
        py: Python<'data>,
        obj: &'data PyAny,
        field_name: &'data str,
        field_value: &'data PyAny,
        extra: &Extra,
        definitions: &'data Definitions<CombinedValidator>,
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let dict: &PyDict = obj.downcast()?;

        let get_updated_dict = |output: PyObject| {
            dict.set_item(field_name, output)?;
            Ok(dict)
        };

        let prepare_result = |result: ValResult<'data, PyObject>| match result {
            Ok(output) => get_updated_dict(output),
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
                        .validate(py, field_value, &extra, definitions, recursion_guard),
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
                        prepare_result(validator.validate(py, field_value, &extra, definitions, recursion_guard))
                    }
                    None => get_updated_dict(field_value.to_object(py)),
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

        let new_extra = match &self.extra_behavior {
            ExtraBehavior::Allow => {
                let non_extra_data = PyDict::new(py);
                self.fields.iter().for_each(|f| {
                    let popped_value = PyAny::get_item(new_data, &f.name).unwrap();
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

        let fields_set: &PySet = PySet::new(py, &[field_name.to_string()])?;
        Ok((new_data.to_object(py), new_extra, fields_set.to_object(py)).to_object(py))
    }

    fn different_strict_behavior(
        &self,
        definitions: Option<&DefinitionsBuilder<CombinedValidator>>,
        ultra_strict: bool,
    ) -> bool {
        self.fields
            .iter()
            .any(|f| f.validator.different_strict_behavior(definitions, ultra_strict))
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }

    fn complete(&mut self, definitions: &DefinitionsBuilder<CombinedValidator>) -> PyResult<()> {
        self.fields
            .iter_mut()
            .try_for_each(|f| f.validator.complete(definitions))?;
        match &mut self.extra_validator {
            Some(v) => v.complete(definitions),
            None => Ok(()),
        }
    }
}
