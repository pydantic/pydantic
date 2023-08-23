use pyo3::exceptions::PyKeyError;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyString, PyTuple, PyType};

use ahash::AHashSet;

use crate::build_tools::py_schema_err;
use crate::build_tools::{is_strict, schema_or_config_same, ExtraBehavior};
use crate::errors::{ErrorType, ErrorTypeDefaults, ValError, ValLineError, ValResult};
use crate::input::{GenericArguments, Input};
use crate::lookup_key::LookupKey;
use crate::tools::SchemaDict;
use crate::validators::function::convert_err;

use super::arguments::{json_get, json_slice, py_get, py_slice};
use super::model::{create_class, force_setattr, Revalidate};
use super::{
    build_validator, BuildValidator, CombinedValidator, DefinitionsBuilder, Extra, ValidationState, Validator,
};

#[derive(Debug, Clone)]
struct Field {
    kw_only: bool,
    name: String,
    py_name: Py<PyString>,
    init_only: bool,
    lookup_key: LookupKey,
    validator: CombinedValidator,
    frozen: bool,
}

#[derive(Debug, Clone)]
pub struct DataclassArgsValidator {
    fields: Vec<Field>,
    positional_count: usize,
    init_only_count: Option<usize>,
    dataclass_name: String,
    validator_name: String,
    extra_behavior: ExtraBehavior,
    extras_validator: Option<Box<CombinedValidator>>,
    loc_by_alias: bool,
}

impl BuildValidator for DataclassArgsValidator {
    const EXPECTED_TYPE: &'static str = "dataclass-args";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();

        let populate_by_name = schema_or_config_same(schema, config, intern!(py, "populate_by_name"))?.unwrap_or(false);

        let extra_behavior = ExtraBehavior::from_schema_or_config(py, schema, config, ExtraBehavior::Ignore)?;

        let extras_validator = match (schema.get_item(intern!(py, "extras_schema")), &extra_behavior) {
            (Some(v), ExtraBehavior::Allow) => Some(Box::new(build_validator(v, config, definitions)?)),
            (Some(_), _) => return py_schema_err!("extras_schema can only be used if extra_behavior=allow"),
            (_, _) => None,
        };

        let fields_schema: &PyList = schema.get_as_req(intern!(py, "fields"))?;
        let mut fields: Vec<Field> = Vec::with_capacity(fields_schema.len());

        let mut positional_count = 0;

        for field in fields_schema {
            let field: &PyDict = field.downcast()?;

            let py_name: &PyString = field.get_as_req(intern!(py, "name"))?;
            let name: String = py_name.extract()?;

            let lookup_key = match field.get_item(intern!(py, "validation_alias")) {
                Some(alias) => {
                    let alt_alias = if populate_by_name { Some(name.as_str()) } else { None };
                    LookupKey::from_py(py, alias, alt_alias)?
                }
                None => LookupKey::from_string(py, &name),
            };

            let schema: &PyAny = field.get_as_req(intern!(py, "schema"))?;

            let validator = match build_validator(schema, config, definitions) {
                Ok(v) => v,
                Err(err) => return py_schema_err!("Field '{}':\n  {}", name, err),
            };

            if let CombinedValidator::WithDefault(ref v) = validator {
                if v.omit_on_error() {
                    return py_schema_err!("Field `{}`: omit_on_error cannot be used with arguments", name);
                }
            }

            let kw_only = field.get_as(intern!(py, "kw_only"))?.unwrap_or(true);
            if !kw_only {
                positional_count += 1;
            }

            fields.push(Field {
                kw_only,
                name,
                py_name: py_name.into(),
                lookup_key,
                validator,
                init_only: field.get_as(intern!(py, "init_only"))?.unwrap_or(false),
                frozen: field.get_as::<bool>(intern!(py, "frozen"))?.unwrap_or(false),
            });
        }

        let init_only_count = if schema.get_as(intern!(py, "collect_init_only"))?.unwrap_or(false) {
            Some(fields.iter().filter(|f| f.init_only).count())
        } else {
            None
        };
        let dataclass_name: String = schema.get_as_req(intern!(py, "dataclass_name"))?;
        let validator_name = format!("dataclass-args[{dataclass_name}]");

        Ok(Self {
            fields,
            positional_count,
            init_only_count,
            dataclass_name,
            validator_name,
            extra_behavior,
            extras_validator,
            loc_by_alias: config.get_as(intern!(py, "loc_by_alias"))?.unwrap_or(true),
        }
        .into())
    }
}

impl_py_gc_traverse!(Field { validator });

impl_py_gc_traverse!(DataclassArgsValidator { fields });

impl Validator for DataclassArgsValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        let args = input.validate_dataclass_args(&self.dataclass_name)?;

        let output_dict = PyDict::new(py);
        let mut init_only_args = self.init_only_count.map(Vec::with_capacity);

        let mut errors: Vec<ValLineError> = Vec::new();
        let mut used_keys: AHashSet<&str> = AHashSet::with_capacity(self.fields.len());

        state.with_new_extra(
            Extra {
                data: Some(output_dict),
                ..*state.extra()
            },
            |state| {
                macro_rules! set_item {
                    ($field:ident, $value:expr) => {{
                        let py_name = $field.py_name.as_ref(py);
                        if $field.init_only {
                            if let Some(ref mut init_only_args) = init_only_args {
                                init_only_args.push($value);
                            }
                        } else {
                            output_dict.set_item(py_name, $value)?;
                        }
                    }};
                }

                macro_rules! process {
                    ($args:ident, $get_method:ident, $get_macro:ident, $slice_macro:ident) => {{
                        // go through fields getting the value from args or kwargs and validating it
                        for (index, field) in self.fields.iter().enumerate() {
                            let mut pos_value = None;
                            if let Some(args) = $args.args {
                                if !field.kw_only {
                                    pos_value = $get_macro!(args, index);
                                }
                            }

                            let mut kw_value = None;
                            if let Some(kwargs) = $args.kwargs {
                                if let Some((lookup_path, value)) = field.lookup_key.$get_method(kwargs)? {
                                    used_keys.insert(lookup_path.first_key());
                                    kw_value = Some((lookup_path, value));
                                }
                            }

                            match (pos_value, kw_value) {
                                // found both positional and keyword arguments, error
                                (Some(_), Some((_, kw_value))) => {
                                    errors.push(ValLineError::new_with_loc(
                                        ErrorTypeDefaults::MultipleArgumentValues,
                                        kw_value,
                                        field.name.clone(),
                                    ));
                                }
                                // found a positional argument, validate it
                                (Some(pos_value), None) => match field.validator.validate(py, pos_value, state) {
                                    Ok(value) => set_item!(field, value),
                                    Err(ValError::LineErrors(line_errors)) => {
                                        errors.extend(
                                            line_errors
                                                .into_iter()
                                                .map(|err| err.with_outer_location(index.into())),
                                        );
                                    }
                                    Err(err) => return Err(err),
                                },
                                // found a keyword argument, validate it
                                (None, Some((lookup_path, kw_value))) => {
                                    match field.validator.validate(py, kw_value, state) {
                                        Ok(value) => set_item!(field, value),
                                        Err(ValError::LineErrors(line_errors)) => {
                                            errors.extend(line_errors.into_iter().map(|err| {
                                                lookup_path.apply_error_loc(err, self.loc_by_alias, &field.name)
                                            }));
                                        }
                                        Err(err) => return Err(err),
                                    }
                                }
                                // found neither, check if there is a default value, otherwise error
                                (None, None) => {
                                    if let Some(value) =
                                        field
                                            .validator
                                            .default_value(py, Some(field.name.as_str()), state)?
                                    {
                                        set_item!(field, value);
                                    } else {
                                        errors.push(field.lookup_key.error(
                                            ErrorTypeDefaults::Missing,
                                            input,
                                            self.loc_by_alias,
                                            &field.name,
                                        ));
                                    }
                                }
                            }
                        }
                        // if there are more args than positional_count, add an error for each one
                        if let Some(args) = $args.args {
                            let len = args.len();
                            if len > self.positional_count {
                                for (index, item) in $slice_macro!(args, self.positional_count, len)
                                    .iter()
                                    .enumerate()
                                {
                                    errors.push(ValLineError::new_with_loc(
                                        ErrorTypeDefaults::UnexpectedPositionalArgument,
                                        item,
                                        index + self.positional_count,
                                    ));
                                }
                            }
                        }
                        // if there are kwargs check any that haven't been processed yet
                        if let Some(kwargs) = $args.kwargs {
                            if kwargs.len() != used_keys.len() {
                                for (raw_key, value) in kwargs.iter() {
                                    match raw_key.strict_str() {
                                        Ok(either_str) => {
                                            if !used_keys.contains(either_str.as_cow()?.as_ref()) {
                                                // Unknown / extra field
                                                match self.extra_behavior {
                                                    ExtraBehavior::Forbid => {
                                                        errors.push(ValLineError::new_with_loc(
                                                            ErrorTypeDefaults::UnexpectedKeywordArgument,
                                                            value,
                                                            raw_key.as_loc_item(),
                                                        ));
                                                    }
                                                    ExtraBehavior::Ignore => {}
                                                    ExtraBehavior::Allow => {
                                                        if let Some(ref validator) = self.extras_validator {
                                                            match validator.validate(py, value, state) {
                                                                Ok(value) => output_dict
                                                                    .set_item(either_str.as_py_string(py), value)?,
                                                                Err(ValError::LineErrors(line_errors)) => {
                                                                    for err in line_errors {
                                                                        errors.push(err.with_outer_location(
                                                                            raw_key.as_loc_item(),
                                                                        ));
                                                                    }
                                                                }
                                                                Err(err) => return Err(err),
                                                            }
                                                        } else {
                                                            output_dict.set_item(either_str.as_py_string(py), value)?
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                        Err(ValError::LineErrors(line_errors)) => {
                                            for err in line_errors {
                                                errors.push(
                                                    err.with_outer_location(raw_key.as_loc_item())
                                                        .with_type(ErrorTypeDefaults::InvalidKey),
                                                );
                                            }
                                        }
                                        Err(err) => return Err(err),
                                    }
                                }
                            }
                        }
                    }};
                }
                match args {
                    GenericArguments::Py(a) => process!(a, py_get_dict_item, py_get, py_slice),
                    GenericArguments::Json(a) => process!(a, json_get, json_get, json_slice),
                }
                Ok(())
            },
        )?;
        if errors.is_empty() {
            if let Some(init_only_args) = init_only_args {
                Ok((output_dict, PyTuple::new(py, init_only_args)).to_object(py))
            } else {
                Ok((output_dict, py.None()).to_object(py))
            }
        } else {
            Err(ValError::LineErrors(errors))
        }
    }

    fn validate_assignment<'data>(
        &self,
        py: Python<'data>,
        obj: &'data PyAny,
        field_name: &'data str,
        field_value: &'data PyAny,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        let dict: &PyDict = obj.downcast()?;

        let ok = |output: PyObject| {
            dict.set_item(field_name, output)?;
            // The second return value represents `init_only_args`
            // which doesn't make much sense in this context but we need to put something there
            // so that function validators that sit between DataclassValidator and DataclassArgsValidator
            // always get called the same shape of data.
            Ok(PyTuple::new(py, vec![dict.to_object(py), py.None()]).into_py(py))
        };

        if let Some(field) = self.fields.iter().find(|f| f.name == field_name) {
            if field.frozen {
                return Err(ValError::new_with_loc(
                    ErrorTypeDefaults::FrozenField,
                    field_value,
                    field.name.to_string(),
                ));
            }
            // by using dict but removing the field in question, we match V1 behaviour
            let data_dict = dict.copy()?;
            if let Err(err) = data_dict.del_item(field_name) {
                // KeyError is fine here as the field might not be in the dict
                if !err.get_type(py).is(PyType::new::<PyKeyError>(py)) {
                    return Err(err.into());
                }
            }
            match state.with_new_extra(
                Extra {
                    data: Some(data_dict),
                    ..*state.extra()
                },
                |state| field.validator.validate(py, field_value, state),
            ) {
                Ok(output) => ok(output),
                Err(ValError::LineErrors(line_errors)) => {
                    let errors = line_errors
                        .into_iter()
                        .map(|e| e.with_outer_location(field_name.into()))
                        .collect();
                    Err(ValError::LineErrors(errors))
                }
                Err(err) => Err(err),
            }
        } else {
            // Handle extra (unknown) field
            // We partially use the extra_behavior for initialization / validation
            // to determine how to handle assignment
            match self.extra_behavior {
                // For dataclasses we allow assigning unknown fields
                // to match stdlib dataclass behavior
                ExtraBehavior::Allow => ok(field_value.to_object(py)),
                _ => Err(ValError::new_with_loc(
                    ErrorType::NoSuchAttribute {
                        attribute: field_name.to_string(),
                        context: None,
                    },
                    field_value,
                    field_name.to_string(),
                )),
            }
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
        &self.validator_name
    }

    fn complete(&mut self, definitions: &DefinitionsBuilder<CombinedValidator>) -> PyResult<()> {
        self.fields
            .iter_mut()
            .try_for_each(|field| field.validator.complete(definitions))
    }
}

#[derive(Debug, Clone)]
pub struct DataclassValidator {
    strict: bool,
    validator: Box<CombinedValidator>,
    class: Py<PyType>,
    fields: Vec<Py<PyString>>,
    post_init: Option<Py<PyString>>,
    revalidate: Revalidate,
    name: String,
    frozen: bool,
    slots: bool,
}

impl BuildValidator for DataclassValidator {
    const EXPECTED_TYPE: &'static str = "dataclass";

    fn build(
        schema: &PyDict,
        _config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();

        // dataclasses ignore the parent config and always use the config from this dataclasses
        let config = schema.get_as(intern!(py, "config"))?;

        let class: &PyType = schema.get_as_req(intern!(py, "cls"))?;
        let name = match schema.get_as_req::<String>(intern!(py, "cls_name")) {
            Ok(name) => name,
            Err(_) => class.getattr(intern!(py, "__name__"))?.extract()?,
        };
        let sub_schema: &PyAny = schema.get_as_req(intern!(py, "schema"))?;
        let validator = build_validator(sub_schema, config, definitions)?;

        let post_init = if schema.get_as::<bool>(intern!(py, "post_init"))?.unwrap_or(false) {
            Some(PyString::intern(py, "__post_init__").into_py(py))
        } else {
            None
        };

        let fields = schema
            .get_as_req::<&PyList>(intern!(py, "fields"))?
            .iter()
            .map(|s| Ok(s.downcast::<PyString>()?.into_py(py)))
            .collect::<PyResult<Vec<_>>>()?;

        Ok(Self {
            strict: is_strict(schema, config)?,
            validator: Box::new(validator),
            class: class.into(),
            fields,
            post_init,
            revalidate: Revalidate::from_str(schema_or_config_same(
                schema,
                config,
                intern!(py, "revalidate_instances"),
            )?)?,
            name,
            frozen: schema.get_as(intern!(py, "frozen"))?.unwrap_or(false),
            slots: schema.get_as(intern!(py, "slots"))?.unwrap_or(false),
        }
        .into())
    }
}

impl_py_gc_traverse!(DataclassValidator { class, validator });

impl Validator for DataclassValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        if let Some(self_instance) = state.extra().self_instance {
            // in the case that self_instance is Some, we're calling validation from within `BaseModel.__init__`
            return self.validate_init(py, self_instance, input, state);
        }

        // same logic as on models
        let class = self.class.as_ref(py);
        if let Some(py_input) = input.input_is_instance(class) {
            if self.revalidate.should_revalidate(py_input, class) {
                let input_dict: &PyAny = self.dataclass_to_dict(py, py_input)?;
                let val_output = self.validator.validate(py, input_dict, state)?;
                let dc = create_class(self.class.as_ref(py))?;
                self.set_dict_call(py, dc.as_ref(py), val_output, input)?;
                Ok(dc)
            } else {
                Ok(input.to_object(py))
            }
        } else if state.strict_or(self.strict) && input.is_python() {
            Err(ValError::new(
                ErrorType::DataclassExactType {
                    class_name: self.get_name().to_string(),
                    context: None,
                },
                input,
            ))
        } else {
            let val_output = self.validator.validate(py, input, state)?;
            let dc = create_class(self.class.as_ref(py))?;
            self.set_dict_call(py, dc.as_ref(py), val_output, input)?;
            Ok(dc)
        }
    }

    fn validate_assignment<'data>(
        &self,
        py: Python<'data>,
        obj: &'data PyAny,
        field_name: &'data str,
        field_value: &'data PyAny,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        if self.frozen {
            return Err(ValError::new(ErrorTypeDefaults::FrozenInstance, field_value));
        }

        let new_dict = self.dataclass_to_dict(py, obj)?;

        new_dict.set_item(field_name, field_value)?;

        let val_assignment_result = self
            .validator
            .validate_assignment(py, new_dict, field_name, field_value, state)?;

        let (dc_dict, _): (&PyDict, PyObject) = val_assignment_result.extract(py)?;

        if self.slots {
            let value = dc_dict
                .get_item(field_name)
                .ok_or_else(|| PyKeyError::new_err(field_name.to_string()))?;
            force_setattr(py, obj, field_name, value)?;
        } else {
            force_setattr(py, obj, intern!(py, "__dict__"), dc_dict)?;
        }

        Ok(obj.to_object(py))
    }

    fn different_strict_behavior(
        &self,
        definitions: Option<&DefinitionsBuilder<CombinedValidator>>,
        ultra_strict: bool,
    ) -> bool {
        if ultra_strict {
            self.validator.different_strict_behavior(definitions, ultra_strict)
        } else {
            true
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, definitions: &DefinitionsBuilder<CombinedValidator>) -> PyResult<()> {
        self.validator.complete(definitions)
    }
}

impl DataclassValidator {
    /// here we just call the inner validator, then set attributes on `self_instance`
    fn validate_init<'s, 'data>(
        &'s self,
        py: Python<'data>,
        self_instance: &'s PyAny,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        // we need to set `self_instance` to None for nested validators as we don't want to operate on the self_instance
        // instance anymore
        let state = &mut state.rebind_extra(|extra| extra.self_instance = None);
        let val_output = self.validator.validate(py, input, state)?;

        self.set_dict_call(py, self_instance, val_output, input)?;

        Ok(self_instance.into_py(py))
    }

    fn dataclass_to_dict<'py>(&self, py: Python<'py>, dc: &'py PyAny) -> PyResult<&'py PyDict> {
        let dict = PyDict::new(py);

        for field_name in &self.fields {
            let field_name = field_name.as_ref(py);
            dict.set_item(field_name, dc.getattr(field_name)?)?;
        }
        Ok(dict)
    }

    fn set_dict_call<'s, 'data>(
        &'s self,
        py: Python<'data>,
        dc: &PyAny,
        val_output: PyObject,
        input: &'data impl Input<'data>,
    ) -> ValResult<'data, ()> {
        let (dc_dict, post_init_kwargs): (&PyAny, &PyAny) = val_output.extract(py)?;
        if self.slots {
            let dc_dict: &PyDict = dc_dict.downcast()?;
            for (key, value) in dc_dict {
                force_setattr(py, dc, key, value)?;
            }
        } else {
            force_setattr(py, dc, intern!(py, "__dict__"), dc_dict)?;
        }

        if let Some(ref post_init) = self.post_init {
            let post_init = post_init.as_ref(py);
            let r = if post_init_kwargs.is_none() {
                dc.call_method0(post_init)
            } else {
                let args = post_init_kwargs.downcast::<PyTuple>()?;
                dc.call_method1(post_init, args)
            };
            r.map_err(|e| convert_err(py, e, input))?;
        }
        Ok(())
    }
}
