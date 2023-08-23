use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};

use ahash::AHashSet;

use crate::build_tools::py_schema_err;
use crate::build_tools::{is_strict, schema_or_config, schema_or_config_same, ExtraBehavior};
use crate::errors::{py_err_string, ErrorType, ErrorTypeDefaults, ValError, ValLineError, ValResult};
use crate::input::{
    AttributesGenericIterator, DictGenericIterator, GenericMapping, Input, JsonObjectGenericIterator,
    MappingGenericIterator,
};
use crate::lookup_key::LookupKey;
use crate::tools::SchemaDict;

use super::{
    build_validator, BuildValidator, CombinedValidator, DefinitionsBuilder, Extra, ValidationState, Validator,
};

use std::ops::ControlFlow;

#[derive(Debug, Clone)]
struct TypedDictField {
    name: String,
    lookup_key: LookupKey,
    name_py: Py<PyString>,
    required: bool,
    validator: CombinedValidator,
}

impl_py_gc_traverse!(TypedDictField { validator });

#[derive(Debug, Clone)]
pub struct TypedDictValidator {
    fields: Vec<TypedDictField>,
    extra_behavior: ExtraBehavior,
    extras_validator: Option<Box<CombinedValidator>>,
    strict: bool,
    loc_by_alias: bool,
}

impl BuildValidator for TypedDictValidator {
    const EXPECTED_TYPE: &'static str = "typed-dict";

    fn build(
        schema: &PyDict,
        _config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();

        // typed dicts ignore the parent config and always use the config from this TypedDict
        let config = schema.get_as(intern!(py, "config"))?;

        let strict = is_strict(schema, config)?;

        let total =
            schema_or_config(schema, config, intern!(py, "total"), intern!(py, "typed_dict_total"))?.unwrap_or(true);
        let populate_by_name = schema_or_config_same(schema, config, intern!(py, "populate_by_name"))?.unwrap_or(false);

        let extra_behavior = ExtraBehavior::from_schema_or_config(py, schema, config, ExtraBehavior::Ignore)?;

        let extras_validator = match (schema.get_item(intern!(py, "extras_schema")), &extra_behavior) {
            (Some(v), ExtraBehavior::Allow) => Some(Box::new(build_validator(v, config, definitions)?)),
            (Some(_), _) => return py_schema_err!("extras_schema can only be used if extra_behavior=allow"),
            (_, _) => None,
        };

        let fields_dict: &PyDict = schema.get_as_req(intern!(py, "fields"))?;
        let mut fields: Vec<TypedDictField> = Vec::with_capacity(fields_dict.len());

        for (key, value) in fields_dict {
            let field_info: &PyDict = value.downcast()?;
            let field_name: &str = key.extract()?;

            let schema = field_info.get_as_req(intern!(py, "schema"))?;

            let validator = match build_validator(schema, config, definitions) {
                Ok(v) => v,
                Err(err) => return py_schema_err!("Field \"{}\":\n  {}", field_name, err),
            };

            let required = match field_info.get_as::<bool>(intern!(py, "required"))? {
                Some(required) => {
                    if required {
                        if let CombinedValidator::WithDefault(ref val) = validator {
                            if val.has_default() {
                                return py_schema_err!(
                                    "Field '{}': a required field cannot have a default value",
                                    field_name
                                );
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
                        return py_schema_err!(
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
            });
        }

        Ok(Self {
            fields,
            extra_behavior,
            extras_validator,
            strict,
            loc_by_alias: config.get_as(intern!(py, "loc_by_alias"))?.unwrap_or(true),
        }
        .into())
    }
}

impl_py_gc_traverse!(TypedDictValidator {
    fields,
    extras_validator
});

impl Validator for TypedDictValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        let strict = state.strict_or(self.strict);
        let dict = input.validate_dict(strict)?;

        let output_dict = PyDict::new(py);
        let mut errors: Vec<ValLineError> = Vec::with_capacity(self.fields.len());

        // we only care about which keys have been used if we're iterating over the object for extra after
        // the first pass
        let mut used_keys: Option<AHashSet<&str>> = match (&self.extra_behavior, &dict) {
            (_, GenericMapping::PyGetAttr(_, _)) => None,
            (ExtraBehavior::Allow | ExtraBehavior::Forbid, _) => Some(AHashSet::with_capacity(self.fields.len())),
            _ => None,
        };

        macro_rules! control_flow {
            ($e: expr) => {
                match $e {
                    Ok(v) => ControlFlow::Continue(v),
                    Err(err) => ControlFlow::Break(ValError::from(err)),
                }
            };
        }

        macro_rules! process {
            ($dict:ident, $get_method:ident, $iter:ty $(,$kwargs:ident)?) => {{
                match state.with_new_extra(Extra {
                    data: Some(output_dict),
                    ..*state.extra()
                }, |state| {
                    for field in &self.fields {
                        let op_key_value = match field.lookup_key.$get_method($dict $(, $kwargs )? ) {
                            Ok(v) => v,
                            Err(err) => {
                                errors.push(ValLineError::new_with_loc(
                                    ErrorType::GetAttributeError {
                                        error: py_err_string(py, err),
                                        context: None,
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
                            match field.validator.validate(py, value, state) {
                                Ok(value) => {
                                    control_flow!(output_dict.set_item(&field.name_py, value))?;
                                }
                                Err(ValError::Omit) => continue,
                                Err(ValError::LineErrors(line_errors)) => {
                                    for err in line_errors {
                                        errors.push(lookup_path.apply_error_loc(err, self.loc_by_alias, &field.name));
                                    }
                                }
                                Err(err) => return ControlFlow::Break(err),
                            }
                            continue;
                        } else if let Some(value) = control_flow!(field.validator.default_value(py, Some(field.name.as_str()), state))? {
                            control_flow!(output_dict.set_item(&field.name_py, value))?;
                        } else if field.required {
                            errors.push(field.lookup_key.error(
                                ErrorTypeDefaults::Missing,
                                input,
                                self.loc_by_alias,
                                &field.name
                            ));
                        }
                    }
                    ControlFlow::Continue(())
                }) {
                    ControlFlow::Continue(()) => {}
                    ControlFlow::Break(err) => return Err(err),
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
                                            .with_type(ErrorTypeDefaults::InvalidKey),
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
                                    ErrorTypeDefaults::ExtraForbidden,
                                    value,
                                    raw_key.as_loc_item(),
                                ));
                            }
                            ExtraBehavior::Ignore => {}
                            ExtraBehavior::Allow => {
                            let py_key = either_str.as_py_string(py);
                                if let Some(ref validator) = self.extras_validator {
                                    match validator.validate(py, value, state) {
                                        Ok(value) => {
                                            output_dict.set_item(py_key, value)?;
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
        } else {
            Ok(output_dict.to_object(py))
        }
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
        match &mut self.extras_validator {
            Some(v) => v.complete(definitions),
            None => Ok(()),
        }
    }
}
