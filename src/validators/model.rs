use std::cmp::Ordering;
use std::ptr::null_mut;

use pyo3::conversion::AsPyPointer;
use pyo3::exceptions::PyTypeError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString, PyTuple, PyType};
use pyo3::{ffi, intern};

use crate::build_tools::{py_err, SchemaDict};
use crate::errors::{ErrorType, ValError, ValResult};
use crate::input::{py_error_on_minusone, Input};
use crate::questions::Question;
use crate::recursion_guard::RecursionGuard;

use super::function::convert_err;
use super::{build_validator, BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct ModelValidator {
    strict: bool,
    revalidate: bool,
    validator: Box<CombinedValidator>,
    class: Py<PyType>,
    call_after_init: Option<Py<PyString>>,
    name: String,
    expect_fields_set: bool,
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

        let expect_fields_set = validator.ask(&Question::ReturnFieldsSet);

        Ok(Self {
            // we don't use is_strict here since we don't want validation to be strict in this case if
            // `config.strict` is set, only if this specific field is strict
            strict: schema.get_as(intern!(py, "strict"))?.unwrap_or(false),
            revalidate: config.get_as(intern!(py, "revalidate_models"))?.unwrap_or(false),
            validator: Box::new(validator),
            class: class.into(),
            call_after_init: schema
                .get_as::<&str>(intern!(py, "call_after_init"))?
                .map(|s| PyString::intern(py, s).into_py(py)),
            // Get the class's `__name__`, not using `class.name()` since it uses `__qualname__`
            // which is not what we want here
            name: class.getattr(intern!(py, "__name__"))?.extract()?,
            expect_fields_set,
        }
        .into())
    }
}

impl Validator for ModelValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let class = self.class.as_ref(py);
        if input.is_exact_instance(class)? {
            if self.revalidate {
                let fields_set = input.get_attr(intern!(py, "__fields_set__"));
                let output = self.validator.validate(py, input, extra, slots, recursion_guard)?;
                if self.expect_fields_set {
                    let (model_dict, validation_fields_set): (&PyAny, &PyAny) = output.extract(py)?;
                    let fields_set = fields_set.unwrap_or(validation_fields_set);
                    Ok(self.create_class(py, model_dict, Some(fields_set))?)
                } else {
                    Ok(self.create_class(py, output.as_ref(py), fields_set)?)
                }
            } else {
                Ok(input.to_object(py))
            }
        } else if extra.strict.unwrap_or(self.strict) {
            Err(ValError::new(
                ErrorType::ModelClassType {
                    class_name: self.get_name().to_string(),
                },
                input,
            ))
        } else {
            let output = self.validator.validate(py, input, extra, slots, recursion_guard)?;
            let instance = if self.expect_fields_set {
                let (model_dict, fields_set): (&PyAny, &PyAny) = output.extract(py)?;
                self.create_class(py, model_dict, Some(fields_set))?
            } else {
                self.create_class(py, output.as_ref(py), None)?
            };

            if let Some(ref call_after_init) = self.call_after_init {
                let kwargs = PyDict::new(py);
                kwargs.set_item("context", extra.context)?;
                instance
                    .call_method(py, call_after_init.as_ref(py), (), Some(kwargs))
                    .map_err(|e| convert_err(py, e, input))?;
            }
            Ok(instance)
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}

impl ModelValidator {
    fn create_class(&self, py: Python, model_dict: &PyAny, fields_set: Option<&PyAny>) -> PyResult<PyObject> {
        // based on the following but with the second argument of new_func set to an empty tuple as required
        // https://github.com/PyO3/pyo3/blob/d2caa056e9aacc46374139ef491d112cb8af1a25/src/pyclass_init.rs#L35-L77
        let args = PyTuple::empty(py);
        let raw_type = self.class.as_ref(py).as_type_ptr();
        let instance = unsafe {
            // Safety: raw_type is known to be a non-null type object pointer
            match (*raw_type).tp_new {
                // Safety: the result of new_func is guaranteed to be either an owned pointer or null on error returns.
                Some(new_func) => PyObject::from_owned_ptr_or_err(
                    py,
                    // Safety: the non-null pointers are known to be valid, and it's allowed to call tp_new with a
                    // null kwargs dict.
                    new_func(raw_type, args.as_ptr(), null_mut()),
                )?,
                None => return py_err!(PyTypeError; "base type without tp_new"),
            }
        };

        let instance_ref = instance.as_ref(py);
        force_setattr(py, instance_ref, intern!(py, "__dict__"), model_dict)?;
        if let Some(fields_set) = fields_set {
            force_setattr(py, instance_ref, intern!(py, "__fields_set__"), fields_set)?;
        }

        Ok(instance)
    }
}

pub fn force_setattr<N, V>(py: Python<'_>, obj: &PyAny, attr_name: N, value: V) -> PyResult<()>
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
