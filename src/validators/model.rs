use std::cmp::Ordering;
use std::ptr::null_mut;

use pyo3::conversion::AsPyPointer;
use pyo3::exceptions::PyTypeError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PySet, PyString, PyTuple, PyType};
use pyo3::{ffi, intern};

use crate::build_tools::{py_err, schema_or_config_same, SchemaDict};
use crate::errors::{ErrorType, ValError, ValResult};
use crate::input::{py_error_on_minusone, Input};
use crate::recursion_guard::RecursionGuard;

use super::function::convert_err;
use super::{build_validator, BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

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
            Some(s) => py_err!("Invalid revalidate_instances value: {}", s),
        }
    }

    pub fn should_revalidate<'d>(&self, input: &impl Input<'d>, class: &PyType) -> bool {
        match self {
            Revalidate::Always => true,
            Revalidate::Never => false,
            Revalidate::SubclassInstances => !input.is_exact_instance(class),
        }
    }
}

#[derive(Debug, Clone)]
pub struct ModelValidator {
    strict: bool,
    revalidate: Revalidate,
    validator: Box<CombinedValidator>,
    class: Py<PyType>,
    post_init: Option<Py<PyString>>,
    name: String,
    frozen: bool,
}

impl BuildValidator for ModelValidator {
    const EXPECTED_TYPE: &'static str = "model";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        // models ignore the parent config and always use the config from this model
        let config = build_config(py, schema, config)?;

        let class: &PyType = schema.get_as_req(intern!(py, "cls"))?;
        let sub_schema: &PyAny = schema.get_as_req(intern!(py, "schema"))?;
        let validator = build_validator(sub_schema, config, build_context)?;

        Ok(Self {
            // we don't use is_strict here since we don't want validation to be strict in this case if
            // `config.strict` is set, only if this specific field is strict
            strict: schema.get_as(intern!(py, "strict"))?.unwrap_or(false),
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
            // Get the class's `__name__`, not using `class.name()` since it uses `__qualname__`
            // which is not what we want here
            name: class.getattr(intern!(py, "__name__"))?.extract()?,
            frozen: schema.get_as(intern!(py, "frozen"))?.unwrap_or(false),
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
        slots: &'data [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        if let Some(self_instance) = extra.self_instance {
            // in the case that self_instance is Some, we're calling validation from within `BaseModel.__init__`
            return self.validate_init(py, self_instance, input, extra, slots, recursion_guard);
        }

        // if we're in strict mode, we require an exact instance of the class (from python, with JSON an object is ok)
        // if we're not in strict mode, instances subclasses are okay, as well as dicts, mappings, from attributes etc.
        // if the input is an instance of the class, we "revalidate" it - e.g. we extract and reuse `__pydantic_fields_set__`
        // but use from attributes to create a new instance of the model field type
        let class = self.class.as_ref(py);
        // mask 0 so JSON is input is never true here
        if input.input_is_instance(class, 0)? {
            if self.revalidate.should_revalidate(input, class) {
                let fields_set = match input.input_get_attr(intern!(py, "__pydantic_fields_set__")) {
                    Some(fields_set) => fields_set.ok(),
                    None => None,
                };
                // get dict here so from_attributes logic doesn't apply
                let dict = input.input_get_attr(intern!(py, "__dict__")).unwrap()?;
                let output = self.validator.validate(py, dict, extra, slots, recursion_guard)?;

                let (model_dict, validation_fields_set): (&PyAny, &PyAny) = output.extract(py)?;
                let fields_set = fields_set.unwrap_or(validation_fields_set);
                let instance = self.create_class(model_dict, fields_set)?;

                self.call_post_init(py, instance, input, extra)
            } else {
                Ok(input.to_object(py))
            }
        } else if extra.strict.unwrap_or(self.strict) && input.is_python() {
            Err(ValError::new(
                ErrorType::ModelClassType {
                    class_name: self.get_name().to_string(),
                },
                input,
            ))
        } else {
            let output = self.validator.validate(py, input, extra, slots, recursion_guard)?;
            let (model_dict, fields_set): (&PyAny, &PyAny) = output.extract(py)?;
            let instance = self.create_class(model_dict, fields_set)?;
            self.call_post_init(py, instance, input, extra)
        }
    }

    fn validate_assignment<'s, 'data: 's>(
        &'s self,
        py: Python<'data>,
        model: &'data PyAny,
        field_name: &'data str,
        field_value: &'data PyAny,
        extra: &Extra,
        slots: &'data [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        if self.frozen {
            return Err(ValError::new(ErrorType::FrozenInstance, field_value));
        }
        let dict_py_str = intern!(py, "__dict__");
        let dict: &PyDict = model.getattr(dict_py_str)?.downcast()?;

        let new_dict = dict.copy()?;
        new_dict.set_item(field_name, field_value)?;

        let output =
            self.validator
                .validate_assignment(py, new_dict, field_name, field_value, extra, slots, recursion_guard)?;

        let (output, updated_fields_set): (&PyDict, &PySet) = output.extract(py)?;

        if let Ok(fields_set) = model.input_get_attr(intern!(py, "__pydantic_fields_set__")).unwrap() {
            let fields_set: &PySet = fields_set.downcast()?;
            for field_name in updated_fields_set {
                fields_set.add(field_name)?;
            }
        }
        let output = output.to_object(py);

        force_setattr(py, model, dict_py_str, output)?;
        Ok(model.into_py(py))
    }

    fn different_strict_behavior(
        &self,
        build_context: Option<&BuildContext<CombinedValidator>>,
        ultra_strict: bool,
    ) -> bool {
        if ultra_strict {
            self.validator.different_strict_behavior(build_context, ultra_strict)
        } else {
            true
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, build_context: &BuildContext<CombinedValidator>) -> PyResult<()> {
        self.validator.complete(build_context)
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
        slots: &'data [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        // we need to set `self_instance` to None for nested validators as we don't want to operate on self_instance
        // anymore
        let new_extra = Extra {
            self_instance: None,
            ..*extra
        };

        let output = self.validator.validate(py, input, &new_extra, slots, recursion_guard)?;
        let (model_dict, fields_set): (&PyAny, &PyAny) = output.extract(py)?;
        set_model_attrs(self_instance, model_dict, fields_set)?;
        self.call_post_init(py, self_instance.into_py(py), input, extra)
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

    fn create_class(&self, model_dict: &PyAny, fields_set: &PyAny) -> PyResult<PyObject> {
        let py = model_dict.py();
        let instance = create_class(self.class.as_ref(py))?;
        set_model_attrs(instance.as_ref(py), model_dict, fields_set)?;
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

fn set_model_attrs(instance: &PyAny, model_dict: &PyAny, fields_set: &PyAny) -> PyResult<()> {
    let py = instance.py();
    force_setattr(py, instance, intern!(py, "__dict__"), model_dict)?;
    force_setattr(py, instance, intern!(py, "__pydantic_fields_set__"), fields_set)?;
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

fn build_config<'a>(
    py: Python<'a>,
    schema: &'a PyDict,
    parent_config: Option<&'a PyDict>,
) -> PyResult<Option<&'a PyDict>> {
    let child_config: Option<&PyDict> = schema.get_as(intern!(py, "config"))?;
    match (parent_config, child_config) {
        (Some(parent), None) => Ok(Some(parent)),
        (None, Some(child)) => Ok(Some(child)),
        (None, None) => Ok(None),
        (Some(parent), Some(child)) => {
            let key = intern!(py, "config_choose_priority");
            let parent_choose: i32 = parent.get_as(key)?.unwrap_or_default();
            let child_choose: i32 = child.get_as(key)?.unwrap_or_default();
            match parent_choose.cmp(&child_choose) {
                Ordering::Greater => Ok(Some(parent)),
                Ordering::Less => Ok(Some(child)),
                Ordering::Equal => {
                    let key = intern!(py, "config_merge_priority");
                    let parent_merge: i32 = parent.get_as(key)?.unwrap_or_default();
                    let child_merge: i32 = child.get_as(key)?.unwrap_or_default();
                    let update = intern!(py, "update");
                    match parent_merge.cmp(&child_merge) {
                        Ordering::Greater => {
                            child.getattr(update)?.call1((parent,))?;
                            Ok(Some(child))
                        }
                        // otherwise child is the winner
                        _ => {
                            parent.getattr(update)?.call1((child,))?;
                            Ok(Some(parent))
                        }
                    }
                }
            }
        }
    }
}
