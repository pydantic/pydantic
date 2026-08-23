use std::ptr::null_mut;
use std::sync::Arc;

use pyo3::exceptions::PyTypeError;
use pyo3::pybacked::PyBackedStr;
use pyo3::types::{PyDict, PyList, PySet, PyString, PyTuple, PyType};
use pyo3::{BoundObject, IntoPyObjectExt, ffi};
use pyo3::{intern, prelude::*};

use super::function::{self, convert_err};
use super::validation_state::Exactness;
use super::{
    BuildValidator, CombinedValidator, DefinitionsBuilder, Extra, ValidationState, Validator, build_validator,
};
use crate::PydanticUndefinedType;
use crate::build_tools::py_schema_err;
use crate::build_tools::schema_or_config_same;
use crate::errors::{ErrorType, ErrorTypeDefaults, ValError, ValResult};
use crate::input::{Input, input_as_python_instance, py_error_on_minusone};
use crate::tools::{ROOT_FIELD, SchemaDict, py_err, root_field_py_str};

const DUNDER_DICT: &str = "__dict__";
const DUNDER_FIELDS_SET_KEY: &str = "__pydantic_fields_set__";
const DUNDER_MODEL_EXTRA_KEY: &str = "__pydantic_extra__";
const DUNDER_MODEL_PRIVATE_KEY: &str = "__pydantic_private__";

#[derive(Debug, Clone)]
pub(super) enum Revalidate {
    Always,
    Never,
    SubclassInstances,
}

impl Revalidate {
    pub fn from_str(s: Option<&str>) -> PyResult<Self> {
        match s {
            Some("always") => Ok(Self::Always),
            Some("never") | None => Ok(Self::Never),
            Some("subclass-instances") => Ok(Self::SubclassInstances),
            Some(s) => py_schema_err!("Invalid revalidate_instances value: {s}"),
        }
    }

    pub fn should_revalidate(&self, input: &Bound<'_, PyAny>, class: &Bound<'_, PyType>) -> bool {
        match self {
            Revalidate::Always => true,
            Revalidate::Never => false,
            Revalidate::SubclassInstances => !input.is_exact_instance(class),
        }
    }
}

/// The result of classifying `input` against a model's `class`/`generic_origin` and
/// `revalidate_instances` config. This is the single source of truth for "existing instance ->
/// already valid vs needs revalidation -> extract inner data", shared by `ModelValidator::validate`
/// and both branches of `ModelInstanceBuilder::validate` - each of which used to (or, in the case of
/// the `self_instance=None` branch, needed to but didn't) make this exact decision independently.
/// Callers remain responsible for what they do with the result (e.g. `state.floor_exactness`,
/// `existing_fields_set` scoping) - this only encapsulates the classification itself.
enum InstanceInputClassification<'py> {
    /// `input` is not an instance of `class` or `generic_origin` - treat it as raw data.
    NotAnInstance,
    /// `input` is already a valid instance that should not be revalidated - callers should return
    /// it unchanged rather than feeding it to the fields validator.
    AlreadyValid,
    /// `input` is an existing instance that needs revalidating. `inner_input` is its extracted
    /// `__dict__` (merged with `__pydantic_extra__`) or, for `RootModel`, its root field -
    /// `fields_set` is its existing `__pydantic_fields_set__`. The fields validator must never be
    /// given the raw instance directly; it only understands `inner_input`-shaped data.
    NeedsRevalidation {
        inner_input: Bound<'py, PyAny>,
        fields_set: Bound<'py, PyAny>,
    },
}

fn classify_instance_input<'py>(
    py: Python<'py>,
    input: &(impl Input<'py> + ?Sized),
    class: &Bound<'py, PyType>,
    generic_origin: Option<&Bound<'py, PyType>>,
    revalidate: &Revalidate,
    root_model: bool,
) -> PyResult<InstanceInputClassification<'py>> {
    // if the input is an instance of the class, we "revalidate" it - e.g. we extract and reuse
    // `__pydantic_fields_set__` but use from attributes to create a new instance of the model
    // field type. If the model has a generic origin, we allow input data to be instances of the
    // generic origin rather than the class, as cases like isinstance(SomeModel[Int],
    // SomeModel[Any]) fail the isinstance check, but are valid - we just have to enforce that the
    // data is revalidated, hence `force_revalidate`.
    let (py_instance_input, force_revalidate): (Option<&Bound<'py, PyAny>>, bool) =
        match input_as_python_instance(input, class) {
            Some(x) => (Some(x), false),
            None => match generic_origin {
                Some(generic_origin) => match input_as_python_instance(input, generic_origin) {
                    Some(x) => (Some(x), true),
                    None => (None, false),
                },
                None => (None, false),
            },
        };

    let Some(py_input) = py_instance_input else {
        return Ok(InstanceInputClassification::NotAnInstance);
    };

    if !(revalidate.should_revalidate(py_input, class) || force_revalidate) {
        return Ok(InstanceInputClassification::AlreadyValid);
    }

    let fields_set = py_input.getattr(intern!(py, DUNDER_FIELDS_SET_KEY))?;
    let inner_input = if root_model {
        py_input.getattr(root_field_py_str(py))?
    } else {
        // get dict here so from_attributes logic doesn't apply
        let dict = py_input.getattr(intern!(py, DUNDER_DICT))?;
        let model_extra = py_input.getattr(intern!(py, DUNDER_MODEL_EXTRA_KEY))?;
        if PyAnyMethods::is_none(&model_extra) {
            dict
        } else {
            let full_model_dict = dict.cast::<PyDict>()?.copy()?;
            full_model_dict.update(model_extra.cast()?)?;
            full_model_dict.into_any()
        }
    };
    Ok(InstanceInputClassification::NeedsRevalidation {
        inner_input,
        fields_set,
    })
}

#[derive(Debug)]
pub struct ModelValidator {
    revalidate: Revalidate,
    class: Py<PyType>,
    generic_origin: Option<Py<PyType>>,
    frozen: bool,
    custom_init: bool,
    root_model: bool,
    name: String,
    /// The model's own inner validator (fields + `mode="before"` model validators), plus any
    /// `mode="after"`/`mode="wrap"` model validators wrapped around it, built once here instead
    /// of as external wrapping schema nodes (see `ModelValidator::build`). Keeping the outer
    /// validators *inside* `ModelValidator` lets them be gated on `state.self_instance` the same
    /// way `ModelValidator` itself already is, so they run exactly once even when `custom_init`
    /// bounces validation through `BaseModel.__init__` (see `validate`/`validate_construct` below,
    /// and GH-13471 for the bug this fixes).
    outer_validator: Arc<CombinedValidator>,
}

impl BuildValidator for ModelValidator {
    const EXPECTED_TYPE: &'static str = "model";

    fn build(
        schema: &Bound<'_, PyDict>,
        _config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedValidator>>,
    ) -> PyResult<Arc<CombinedValidator>> {
        let py = schema.py();
        // models ignore the parent config and always use the config from this model
        let config: Option<Bound<'_, PyDict>> = schema.get_as(intern!(py, "config"))?;

        let class: Bound<'_, PyType> = schema.get_as_req(intern!(py, "cls"))?;
        let generic_origin: Option<Bound<'_, PyType>> = schema.get_as(intern!(py, "generic_origin"))?;
        let sub_schema = schema.get_as_req(intern!(py, "schema"))?;
        let validator = build_validator(&sub_schema, config.as_ref(), definitions)?;
        let name: String = class.getattr(intern!(py, "__name__"))?.extract()?;
        let post_init: Option<Py<PyString>> = schema.get_as(intern!(py, "post_init"))?;
        let root_model: bool = schema.get_as(intern!(py, "root_model"))?.unwrap_or(false);
        let undefined = PydanticUndefinedType::get(py).clone_ref(py).into_any();
        let revalidate = Revalidate::from_str(
            schema_or_config_same::<Bound<'_, PyString>>(schema, config.as_ref(), intern!(py, "revalidate_instances"))?
                .as_ref()
                .map(|s| s.to_str())
                .transpose()?,
        )?;

        let config_py: Py<PyAny> = match &config {
            Some(c) => c.clone().into(),
            None => py.None(),
        };

        let mut outer_validator: Arc<CombinedValidator> =
            Arc::new(CombinedValidator::ModelInstanceBuilder(ModelInstanceBuilder {
                validator,
                class: class.clone().unbind(),
                generic_origin: generic_origin.clone().map(std::convert::Into::into),
                revalidate: revalidate.clone(),
                post_init,
                root_model,
                undefined,
                name: name.clone(),
            }));

        // `mode="after"`/`mode="wrap"` model validators, applied in declaration order - the first
        // declared is the innermost (applied first), matching `apply_model_validators('outer', ...)`
        // in `_generate_schema.py`.
        if let Some(model_validators) = schema.get_as::<Bound<'_, PyList>>(intern!(py, "model_validators"))? {
            for validator_schema in model_validators.iter() {
                let validator_dict = validator_schema.cast::<PyDict>()?;
                let type_: Bound<'_, PyString> = validator_dict.get_as_req(intern!(py, "type"))?;
                let func_info = function::destructure_function_schema(validator_dict)?;
                outer_validator = match type_.to_str()? {
                    "after" => Arc::new(CombinedValidator::FunctionAfter(
                        function::FunctionAfterValidator::new_for_model(
                            py,
                            outer_validator,
                            func_info,
                            config_py.clone_ref(py),
                        )?,
                    )),
                    "wrap" => {
                        let hide_input_in_errors: bool = config
                            .as_ref()
                            .get_as(intern!(py, "hide_input_in_errors"))?
                            .unwrap_or(false);
                        let validation_error_cause: bool = config
                            .as_ref()
                            .get_as(intern!(py, "validation_error_cause"))?
                            .unwrap_or(false);
                        Arc::new(CombinedValidator::FunctionWrap(
                            function::FunctionWrapValidator::new_for_model(
                                py,
                                outer_validator,
                                func_info,
                                config_py.clone_ref(py),
                                hide_input_in_errors,
                                validation_error_cause,
                            )?,
                        ))
                    }
                    other => return py_schema_err!("Invalid model_validators entry type: {other}"),
                };
            }
        }

        Ok(CombinedValidator::Model(Self {
            revalidate,
            class: class.into(),
            generic_origin: generic_origin.map(std::convert::Into::into),
            frozen: schema.get_as(intern!(py, "frozen"))?.unwrap_or(false),
            custom_init: schema.get_as(intern!(py, "custom_init"))?.unwrap_or(false),
            root_model,
            // Get the class's `__name__`, not using `class.qualname()`
            name,
            outer_validator,
        })
        .into())
    }
}

impl_py_gc_traverse!(ModelValidator {
    class,
    generic_origin,
    outer_validator
});

impl Validator for ModelValidator {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Py<PyAny>> {
        if state.self_instance.is_some() {
            // in the case that self_instance is Some, we're calling validation from within
            // `BaseModel.__init__` - either directly, or as the resumed pass following a
            // `custom_init` bounce through it (see `validate_construct` below). Either way, this
            // is the single pass that actually builds the instance, so it's the only place outer
            // (after/wrap) model validators should run - delegate straight to them.
            return self.outer_validator.validate(py, input, state);
        }

        let class = self.class.bind(py);
        let generic_origin_class = self.generic_origin.as_ref().map(|go| go.bind(py));

        // if we're in strict mode, we require an exact instance of the class (from python, with JSON an object is ok)
        // if we're not in strict mode, instances subclasses are okay, as well as dicts, mappings, from attributes etc.
        match classify_instance_input(
            py,
            input,
            class,
            generic_origin_class,
            &self.revalidate,
            self.root_model,
        )? {
            InstanceInputClassification::NeedsRevalidation {
                inner_input,
                fields_set,
            } => self.validate_construct(py, &inner_input, Some(fields_set), state),
            InstanceInputClassification::AlreadyValid => {
                // Already a valid instance we don't need to revalidate - still give outer
                // (after/wrap) model validators a chance to see/transform it, exactly like the old
                // external wrapping nodes always did regardless of whether the inner schema itself
                // does any work. `ModelInstanceBuilder` (the chain's terminal node) makes this same
                // "already an instance, don't touch it" check itself, since a `mode="wrap"`
                // validator may hand its `handler` a *different* value than `input` here.
                self.outer_validator.validate(py, input, state)
            }
            InstanceInputClassification::NotAnInstance => {
                // Having to construct a new model is not an exact match
                state.floor_exactness(Exactness::Strict);
                self.validate_construct(py, input, None, state)
            }
        }
    }

    fn validate_assignment<'py>(
        &self,
        py: Python<'py>,
        model: &Bound<'py, PyAny>,
        field_name: &PyBackedStr,
        field_value: &Bound<'py, PyAny>,
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Py<PyAny>> {
        if self.frozen {
            return Err(ValError::new(ErrorTypeDefaults::FrozenInstance, field_value));
        }
        // outer (after/wrap) model validators, if any, apply on assignment too - delegate to them
        // the same way the (now-removed) external wrapping nodes used to.
        self.outer_validator
            .validate_assignment(py, model, field_name, field_value, state)
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}

impl ModelValidator {
    fn validate_construct<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        existing_fields_set: Option<Bound<'py, PyAny>>,
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Py<PyAny>> {
        if self.custom_init {
            // If we wanted, we could introspect the __init__ signature, and store the
            // keyword arguments and types, and create a validator for them.
            // Perhaps something similar to `validate_call`? Could probably make
            // this work with from_attributes, and would essentially allow you to
            // handle init vars by adding them to the __init__ signature.
            //
            // We deliberately do NOT go through `self.outer_validator` here: the user's `__init__`
            // is expected to call `super().__init__(**kwargs)`, which re-enters `validate` above
            // with `state.self_instance` set - that resumed call is the one that applies the outer
            // (after/wrap) model validators exactly once. Applying them here too (before we even
            // know whether `__init__` will call `super().__init__()` at all) would run them twice.
            if let Some(kwargs) = input.as_kwargs(py) {
                return self
                    .class
                    .call(py, (), Some(&kwargs))
                    .map_err(|e| convert_err(py, e, input));
            }
        }

        let state = &mut state.scoped_set_existing_fields_set(existing_fields_set);
        self.outer_validator.validate(py, input, state)
    }
}

/// The terminal step of building a model instance: sets attributes on `state.self_instance` when
/// one is active (the single resumed pass through `BaseModel.__init__`), or creates a fresh
/// instance otherwise. Any outer (`mode="after"`/`mode="wrap"`) model validators are compiled as
/// `FunctionAfter`/`FunctionWrap` nodes wrapping this validator (see `ModelValidator::build`), so
/// from their point of view this is just "the rest of validation" - the same role a model's own
/// `model_fields_schema` node plays for a field-level `after`/`wrap` validator.
#[derive(Debug)]
pub struct ModelInstanceBuilder {
    validator: Arc<CombinedValidator>,
    class: Py<PyType>,
    generic_origin: Option<Py<PyType>>,
    revalidate: Revalidate,
    post_init: Option<Py<PyString>>,
    root_model: bool,
    undefined: Py<PyAny>,
    name: String,
}

impl_py_gc_traverse!(ModelInstanceBuilder {
    validator,
    class,
    generic_origin,
    post_init,
    undefined
});

impl Validator for ModelInstanceBuilder {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Py<PyAny>> {
        if let Some(self_instance) = state.self_instance {
            // `input` here may itself be an existing instance requiring revalidation rather than
            // raw field data - e.g. a `mode="wrap"` model validator's `handler` can be called with
            // a different, already-existing instance (this is the only branch such a call can
            // reach, since outer model validators only ever run during this resumed pass).
            let class = self.class.bind(py);
            let generic_origin_class = self.generic_origin.as_ref().map(|go| go.bind(py));

            match classify_instance_input(
                py,
                input,
                class,
                generic_origin_class,
                &self.revalidate,
                self.root_model,
            )? {
                InstanceInputClassification::NeedsRevalidation {
                    inner_input,
                    fields_set: _,
                } => {
                    // Unlike `ModelValidator::validate_construct`, the freshly-extracted
                    // `fields_set` is intentionally discarded here: when populating `self_instance`
                    // directly, the fields validator's own output has always been the source of
                    // truth for `__pydantic_fields_set__` in this code path (it never accepted an
                    // `existing_fields_set` override, even before this struct existed).
                    self.set_self_instance_attrs(py, &inner_input, self_instance, state)
                }
                InstanceInputClassification::AlreadyValid | InstanceInputClassification::NotAnInstance => {
                    self.set_self_instance_attrs(py, input, self_instance, state)
                }
            }
        } else {
            // `input` here may not be the model's original top-level input at all - a
            // `mode="wrap"` model validator can hand its `handler` any value it likes - so this
            // check is independent of whatever `ModelValidator::validate` already decided about
            // its own `input`.
            let class = self.class.bind(py);
            let generic_origin_class = self.generic_origin.as_ref().map(|go| go.bind(py));

            match classify_instance_input(
                py,
                input,
                class,
                generic_origin_class,
                &self.revalidate,
                self.root_model,
            )? {
                InstanceInputClassification::AlreadyValid => Ok(input.to_object(py)?.unbind()),
                InstanceInputClassification::NotAnInstance => {
                    let existing_fields_set = state.existing_fields_set.clone();
                    self.construct_fresh(py, input, existing_fields_set, state)
                }
                InstanceInputClassification::NeedsRevalidation {
                    inner_input,
                    fields_set,
                } => self.construct_fresh(py, &inner_input, Some(fields_set), state),
            }
        }
    }

    fn validate_assignment<'py>(
        &self,
        py: Python<'py>,
        model: &Bound<'py, PyAny>,
        field_name: &PyBackedStr,
        field_value: &Bound<'py, PyAny>,
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Py<PyAny>> {
        if self.root_model {
            if field_name != ROOT_FIELD {
                return Err(ValError::new_with_loc(
                    ErrorType::NoSuchAttribute {
                        attribute: field_name.to_string(),
                        context: None,
                    },
                    field_value,
                    field_name.to_string(),
                ));
            }
            let root_field = root_field_py_str(py);
            let state = &mut state.scoped_set_field_name(Some(root_field.clone()));
            let output = self.validator.validate(py, field_value, state)?;

            force_setattr(py, model, root_field, output)?;
            return Ok(model.into_py_any(py)?);
        }
        let old_dict = model.getattr(intern!(py, DUNDER_DICT))?.cast_into::<PyDict>()?;

        let input_dict = old_dict.copy()?;
        if let Ok(old_extra) = model.getattr(intern!(py, DUNDER_MODEL_EXTRA_KEY))?.cast::<PyDict>() {
            input_dict.update(old_extra.as_mapping())?;
        }
        input_dict.set_item(field_name, field_value)?;

        let output = self
            .validator
            .validate_assignment(py, input_dict.as_any(), field_name, field_value, state)?;

        let (validated_dict, validated_extra, validated_fields_set): (
            Bound<'_, PyDict>,
            Bound<'_, PyAny>,
            Bound<'_, PySet>,
        ) = output.extract(py)?;

        if let Ok(fields_set) = model.getattr(intern!(py, DUNDER_FIELDS_SET_KEY)) {
            let fields_set = fields_set.cast::<PySet>()?;
            for field_name in validated_fields_set {
                fields_set.add(field_name)?;
            }
        }

        force_setattr(py, model, intern!(py, DUNDER_DICT), validated_dict)?;
        force_setattr(py, model, intern!(py, DUNDER_MODEL_EXTRA_KEY), validated_extra)?;
        Ok(model.into_py_any(py)?)
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}

impl ModelInstanceBuilder {
    /// Validates `input` (either the raw data passed to `__init__`, or - after extraction by the
    /// caller - the `__dict__`/root-field of an existing instance being revalidated) and sets the
    /// resulting attributes directly on `self_instance`.
    fn set_self_instance_attrs<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        self_instance: &Bound<'py, PyAny>,
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Py<PyAny>> {
        // we need to set `self_instance` to None for nested validators as we don't want to
        // operate on self_instance anymore, and clear `existing_fields_set` for the same
        // reason - both are specific to *this* model's construction, not any nested one.
        let state = &mut state.scoped_clear_self_instance();
        let state = &mut state.scoped_set_existing_fields_set(None);

        if self.root_model {
            let root_field = root_field_py_str(py);
            let state = &mut state.scoped_set_field_name(Some(root_field.clone()));
            let output = self.validator.validate(py, input, state)?;

            let fields_set = if input.as_python().is_some_and(|py_input| py_input.is(&self.undefined)) {
                PySet::empty(py)?
            } else {
                PySet::new(py, [root_field])?
            };
            force_setattr(py, self_instance, intern!(py, DUNDER_FIELDS_SET_KEY), &fields_set)?;
            force_setattr(py, self_instance, root_field, &output)?;
        } else {
            let output = self.validator.validate(py, input, state)?;

            let (model_dict, model_extra, fields_set): (Bound<PyAny>, Bound<PyAny>, Bound<PyAny>) =
                output.extract(py)?;
            set_model_attrs(self_instance, &model_dict, &model_extra, &fields_set)?;
        }
        self.call_post_init(py, self_instance.clone(), input, state.extra())
    }

    /// Validates `input` (raw data, or - after extraction by the caller - the `__dict__`/root-field
    /// of an existing instance being revalidated) and constructs a fresh instance from the result,
    /// preferring `existing_fields_set` over the freshly-validated fields set when present.
    fn construct_fresh<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        existing_fields_set: Option<Bound<'py, PyAny>>,
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Py<PyAny>> {
        let state = &mut state.scoped_set_existing_fields_set(None);

        let instance;

        if self.root_model {
            let root_field = root_field_py_str(py);
            let state = &mut state.scoped_set_field_name(Some(root_field.clone()));
            let output = self.validator.validate(py, input, state)?;
            instance = create_class(self.class.bind(py))?;

            let fields_set = if input.as_python().is_some_and(|py_input| py_input.is(&self.undefined)) {
                PySet::empty(py)?
            } else {
                PySet::new(py, [root_field])?
            };
            force_setattr(py, &instance, intern!(py, DUNDER_FIELDS_SET_KEY), &fields_set)?;
            force_setattr(py, &instance, root_field, output)?;
        } else {
            let output = self.validator.validate(py, input, state)?;
            instance = create_class(self.class.bind(py))?;

            let (model_dict, model_extra, val_fields_set): (Bound<PyAny>, Bound<PyAny>, Bound<PyAny>) =
                output.extract(py)?;
            let fields_set = existing_fields_set.as_ref().unwrap_or(&val_fields_set);
            set_model_attrs(&instance, &model_dict, &model_extra, fields_set)?;
        }
        self.call_post_init(py, instance, input, state.extra())
    }

    fn call_post_init<'py>(
        &self,
        py: Python<'py>,
        instance: Bound<'_, PyAny>,
        input: &(impl Input<'py> + ?Sized),
        extra: &Extra<'_, 'py>,
    ) -> ValResult<Py<PyAny>> {
        if let Some(ref post_init) = self.post_init {
            instance
                .call_method1(post_init.bind(py), (extra.context,))
                .map_err(|e| convert_err(py, e, input))?;
        }
        Ok(instance.into())
    }
}

/// based on the following but with the second argument of new_func set to an empty tuple as required
/// https://github.com/PyO3/pyo3/blob/d2caa056e9aacc46374139ef491d112cb8af1a25/src/pyclass_init.rs#L35-L77
pub(super) fn create_class<'py>(class: &Bound<'py, PyType>) -> PyResult<Bound<'py, PyAny>> {
    let py = class.py();
    let args = PyTuple::empty(py);
    let raw_type = class.as_type_ptr();
    unsafe {
        // Safety: raw_type is known to be a non-null type object pointer
        match (*raw_type).tp_new {
            // Safety: the result of new_func is guaranteed to be either an owned pointer or null on error returns.
            Some(new_func) => Bound::from_owned_ptr_or_err(
                py,
                // Safety: the non-null pointers are known to be valid, and it's allowed to call tp_new with a
                // null kwargs dict.
                new_func(raw_type, args.as_ptr(), null_mut()),
            ),
            None => py_err!(PyTypeError; "base type without tp_new"),
        }
    }
}

fn set_model_attrs(
    instance: &Bound<'_, PyAny>,
    model_dict: &Bound<'_, PyAny>,
    model_extra: &Bound<'_, PyAny>,
    fields_set: &Bound<'_, PyAny>,
) -> PyResult<()> {
    let py = instance.py();
    force_setattr(py, instance, intern!(py, DUNDER_DICT), model_dict)?;
    force_setattr(py, instance, intern!(py, DUNDER_MODEL_EXTRA_KEY), model_extra)?;
    force_setattr(py, instance, intern!(py, DUNDER_MODEL_PRIVATE_KEY), py.None())?;
    force_setattr(py, instance, intern!(py, DUNDER_FIELDS_SET_KEY), fields_set)?;
    Ok(())
}

pub(super) fn force_setattr<'py, N, V>(py: Python<'py>, obj: &Bound<'py, PyAny>, attr_name: N, value: V) -> PyResult<()>
where
    N: IntoPyObject<'py>,
    V: IntoPyObject<'py>,
{
    let attr_name = attr_name.into_pyobject_or_pyerr(py)?;
    let value = value.into_pyobject_or_pyerr(py)?;
    unsafe {
        py_error_on_minusone(
            py,
            ffi::PyObject_GenericSetAttr(obj.as_ptr(), attr_name.as_ptr(), value.as_ptr()),
        )
    }
}
