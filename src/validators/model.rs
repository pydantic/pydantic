use std::ptr::null_mut;

use pyo3::conversion::AsPyPointer;
use pyo3::exceptions::PyTypeError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PySet, PyString, PyTuple, PyType};
use pyo3::{ffi, intern};

use super::function::convert_err;
use super::{build_validator, BuildValidator, CombinedValidator, Definitions, DefinitionsBuilder, Extra, Validator};
use crate::build_tools::py_schema_err;
use crate::build_tools::schema_or_config_same;
use crate::errors::{ErrorType, ValError, ValResult};
use crate::input::{py_error_on_minusone, Input};
use crate::recursion_guard::RecursionGuard;
use crate::tools::{py_err, SchemaDict};
use crate::PydanticUndefinedType;

const ROOT_FIELD: &str = "root";
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
            None => Ok(Self::Never),
            Some("always") => Ok(Self::Always),
            Some("never") => Ok(Self::Never),
            Some("subclass-instances") => Ok(Self::SubclassInstances),
            Some(s) => py_schema_err!("Invalid revalidate_instances value: {}", s),
        }
    }

    pub fn should_revalidate(&self, input: &PyAny, class: &PyType) -> bool {
        match self {
            Revalidate::Always => true,
            Revalidate::Never => false,
            Revalidate::SubclassInstances => !input.get_type().is(class),
        }
    }
}

#[derive(Debug, Clone)]
pub struct ModelValidator {
    revalidate: Revalidate,
    validator: Box<CombinedValidator>,
    class: Py<PyType>,
    post_init: Option<Py<PyString>>,
    frozen: bool,
    custom_init: bool,
    root_model: bool,
    name: String,
}

impl BuildValidator for ModelValidator {
    const EXPECTED_TYPE: &'static str = "model";

    fn build(
        schema: &PyDict,
        _config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        // models ignore the parent config and always use the config from this model
        let config = schema.get_as(intern!(py, "config"))?;

        let class: &PyType = schema.get_as_req(intern!(py, "cls"))?;
        let sub_schema: &PyAny = schema.get_as_req(intern!(py, "schema"))?;
        let validator = build_validator(sub_schema, config, definitions)?;

        Ok(Self {
            revalidate: Revalidate::from_str(schema_or_config_same(
                schema,
                config,
                intern!(py, "revalidate_instances"),
            )?)?,
            validator: Box::new(validator),
            class: class.into(),
            post_init: schema
                .get_as::<&str>(intern!(py, "post_init"))?
                .map(|s| PyString::intern(py, s).into_py(py)),
            frozen: schema.get_as(intern!(py, "frozen"))?.unwrap_or(false),
            custom_init: schema.get_as(intern!(py, "custom_init"))?.unwrap_or(false),
            root_model: schema.get_as(intern!(py, "root_model"))?.unwrap_or(false),
            // Get the class's `__name__`, not using `class.name()` since it uses `__qualname__`
            // which is not what we want here
            name: class.getattr(intern!(py, "__name__"))?.extract()?,
        }
        .into())
    }
}

impl Validator for ModelValidator {
    fn py_gc_traverse(&self, visit: &pyo3::PyVisit<'_>) -> Result<(), pyo3::PyTraverseError> {
        visit.call(&self.class)?;
        self.validator.py_gc_traverse(visit)?;
        Ok(())
    }

    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        definitions: &'data Definitions<CombinedValidator>,
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        if let Some(self_instance) = extra.self_instance {
            // in the case that self_instance is Some, we're calling validation from within `BaseModel.__init__`
            return self.validate_init(py, self_instance, input, extra, definitions, recursion_guard);
        }

        // if we're in strict mode, we require an exact instance of the class (from python, with JSON an object is ok)
        // if we're not in strict mode, instances subclasses are okay, as well as dicts, mappings, from attributes etc.
        // if the input is an instance of the class, we "revalidate" it - e.g. we extract and reuse `__pydantic_fields_set__`
        // but use from attributes to create a new instance of the model field type
        let class = self.class.as_ref(py);
        if let Some(py_input) = input.input_is_instance(class) {
            if self.revalidate.should_revalidate(py_input, class) {
                let fields_set = py_input.getattr(intern!(py, DUNDER_FIELDS_SET_KEY))?;
                if self.root_model {
                    let inner_input = py_input.getattr(intern!(py, ROOT_FIELD))?;
                    self.validate_construct(py, inner_input, Some(fields_set), extra, definitions, recursion_guard)
                } else {
                    // get dict here so from_attributes logic doesn't apply
                    let dict = py_input.getattr(intern!(py, DUNDER_DICT))?;
                    let model_extra = py_input.getattr(intern!(py, DUNDER_MODEL_EXTRA_KEY))?;

                    let inner_input: &PyAny = if model_extra.is_none() {
                        dict
                    } else {
                        let full_model_dict = dict.downcast::<PyDict>()?.copy()?;
                        full_model_dict.update(model_extra.downcast()?)?;
                        full_model_dict
                    };
                    self.validate_construct(py, inner_input, Some(fields_set), extra, definitions, recursion_guard)
                }
            } else {
                Ok(input.to_object(py))
            }
        } else {
            self.validate_construct(py, input, None, extra, definitions, recursion_guard)
        }
    }

    fn validate_assignment<'s, 'data: 's>(
        &'s self,
        py: Python<'data>,
        model: &'data PyAny,
        field_name: &'data str,
        field_value: &'data PyAny,
        extra: &Extra,
        definitions: &'data Definitions<CombinedValidator>,
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        if self.frozen {
            return Err(ValError::new(ErrorType::FrozenInstance, field_value));
        } else if self.root_model {
            return if field_name != ROOT_FIELD {
                Err(ValError::new_with_loc(
                    ErrorType::NoSuchAttribute {
                        attribute: field_name.to_string(),
                    },
                    field_value,
                    field_name.to_string(),
                ))
            } else {
                let field_extra = Extra { ..*extra };
                let output = self
                    .validator
                    .validate(py, field_value, &field_extra, definitions, recursion_guard)?;

                force_setattr(py, model, intern!(py, ROOT_FIELD), output)?;
                Ok(model.into_py(py))
            };
        }
        let old_dict: &PyDict = model.getattr(intern!(py, DUNDER_DICT))?.downcast()?;

        let input_dict = old_dict.copy()?;
        let old_extra: Option<&PyDict> = model.getattr(intern!(py, DUNDER_MODEL_EXTRA_KEY))?.downcast().ok();
        if let Some(old_extra) = old_extra {
            input_dict.update(old_extra.as_mapping())?;
        }
        input_dict.set_item(field_name, field_value)?;

        let output = self.validator.validate_assignment(
            py,
            input_dict,
            field_name,
            field_value,
            extra,
            definitions,
            recursion_guard,
        )?;

        let (validated_dict, validated_extra, validated_fields_set): (&PyDict, &PyAny, &PySet) = output.extract(py)?;

        if let Ok(fields_set) = model.getattr(intern!(py, DUNDER_FIELDS_SET_KEY)) {
            let fields_set: &PySet = fields_set.downcast()?;
            for field_name in validated_fields_set {
                fields_set.add(field_name)?;
            }
        }

        force_setattr(py, model, intern!(py, DUNDER_DICT), validated_dict.to_object(py))?;
        force_setattr(
            py,
            model,
            intern!(py, DUNDER_MODEL_EXTRA_KEY),
            validated_extra.to_object(py),
        )?;
        Ok(model.into_py(py))
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

impl ModelValidator {
    /// here we just call the inner validator, then set attributes on `self_instance`
    fn validate_init<'s, 'data>(
        &'s self,
        py: Python<'data>,
        self_instance: &'s PyAny,
        input: &'data impl Input<'data>,
        extra: &Extra,
        definitions: &'data Definitions<CombinedValidator>,
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        // we need to set `self_instance` to None for nested validators as we don't want to operate on self_instance
        // anymore
        let new_extra = Extra {
            self_instance: None,
            ..*extra
        };

        let output = self
            .validator
            .validate(py, input, &new_extra, definitions, recursion_guard)?;

        if self.root_model {
            let fields_set = if input.to_object(py).is(&PydanticUndefinedType::py_undefined()) {
                PySet::empty(py)?
            } else {
                PySet::new(py, [&String::from(ROOT_FIELD)])?
            };
            force_setattr(py, self_instance, intern!(py, DUNDER_FIELDS_SET_KEY), fields_set)?;
            force_setattr(py, self_instance, intern!(py, ROOT_FIELD), output.as_ref(py))?;
        } else {
            let (model_dict, model_extra, fields_set): (&PyAny, &PyAny, &PyAny) = output.extract(py)?;
            set_model_attrs(self_instance, model_dict, model_extra, fields_set)?;
        }
        self.call_post_init(py, self_instance.into_py(py), input, extra)
    }

    fn validate_construct<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        existing_fields_set: Option<&'data PyAny>,
        extra: &Extra,
        definitions: &'data Definitions<CombinedValidator>,
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        if self.custom_init {
            // If we wanted, we could introspect the __init__ signature, and store the
            // keyword arguments and types, and create a validator for them.
            // Perhaps something similar to `validate_call`? Could probably make
            // this work with from_attributes, and would essentially allow you to
            // handle init vars by adding them to the __init__ signature.
            if let Some(kwargs) = input.as_kwargs(py) {
                return Ok(self.class.call(py, (), Some(kwargs))?);
            }
        }

        let output = if self.root_model {
            let field_extra = Extra { ..*extra };
            self.validator
                .validate(py, input, &field_extra, definitions, recursion_guard)?
        } else {
            self.validator
                .validate(py, input, extra, definitions, recursion_guard)?
        };

        let instance = create_class(self.class.as_ref(py))?;
        let instance_ref = instance.as_ref(py);

        if self.root_model {
            let fields_set = if input.to_object(py).is(&PydanticUndefinedType::py_undefined()) {
                PySet::empty(py)?
            } else {
                PySet::new(py, [&String::from(ROOT_FIELD)])?
            };
            force_setattr(py, instance_ref, intern!(py, DUNDER_FIELDS_SET_KEY), fields_set)?;
            force_setattr(py, instance_ref, intern!(py, ROOT_FIELD), output)?;
        } else {
            let (model_dict, model_extra, val_fields_set): (&PyAny, &PyAny, &PyAny) = output.extract(py)?;
            let fields_set = existing_fields_set.unwrap_or(val_fields_set);
            set_model_attrs(instance_ref, model_dict, model_extra, fields_set)?;
        }
        self.call_post_init(py, instance, input, extra)
    }

    fn call_post_init<'s, 'data>(
        &'s self,
        py: Python<'data>,
        instance: PyObject,
        input: &'data impl Input<'data>,
        extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        if let Some(ref post_init) = self.post_init {
            instance
                .call_method1(py, post_init.as_ref(py), (extra.context,))
                .map_err(|e| convert_err(py, e, input))?;
        }
        Ok(instance)
    }
}

/// based on the following but with the second argument of new_func set to an empty tuple as required
/// https://github.com/PyO3/pyo3/blob/d2caa056e9aacc46374139ef491d112cb8af1a25/src/pyclass_init.rs#L35-L77
pub(super) fn create_class(class: &PyType) -> PyResult<PyObject> {
    let py = class.py();
    let args = PyTuple::empty(py);
    let raw_type = class.as_type_ptr();
    unsafe {
        // Safety: raw_type is known to be a non-null type object pointer
        match (*raw_type).tp_new {
            // Safety: the result of new_func is guaranteed to be either an owned pointer or null on error returns.
            Some(new_func) => PyObject::from_owned_ptr_or_err(
                py,
                // Safety: the non-null pointers are known to be valid, and it's allowed to call tp_new with a
                // null kwargs dict.
                new_func(raw_type, args.as_ptr(), null_mut()),
            ),
            None => py_err!(PyTypeError; "base type without tp_new"),
        }
    }
}

fn set_model_attrs(instance: &PyAny, model_dict: &PyAny, model_extra: &PyAny, fields_set: &PyAny) -> PyResult<()> {
    let py = instance.py();
    force_setattr(py, instance, intern!(py, DUNDER_DICT), model_dict)?;
    force_setattr(py, instance, intern!(py, DUNDER_MODEL_EXTRA_KEY), model_extra)?;
    force_setattr(py, instance, intern!(py, DUNDER_MODEL_PRIVATE_KEY), py.None())?;
    force_setattr(py, instance, intern!(py, DUNDER_FIELDS_SET_KEY), fields_set)?;
    Ok(())
}

pub(super) fn force_setattr<N, V>(py: Python<'_>, obj: &PyAny, attr_name: N, value: V) -> PyResult<()>
where
    N: ToPyObject,
    V: ToPyObject,
{
    let attr_name = attr_name.to_object(py);
    let value = value.to_object(py);
    unsafe {
        py_error_on_minusone(
            py,
            ffi::PyObject_GenericSetAttr(obj.as_ptr(), attr_name.as_ptr(), value.as_ptr()),
        )
    }
}
