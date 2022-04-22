use std::os::raw::c_int;

use pyo3::conversion::AsPyPointer;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyTuple, PyType};
use pyo3::{ffi, intern, ToBorrowedObject};

use super::{build_validator, Extra, ValResult, Validator};
use crate::build_macros::{dict_get, dict_get_required, py_error};
use crate::errors::{as_internal, context, err_val_error, ErrorKind};
use crate::input::Input;

#[derive(Debug, Clone)]
pub struct ModelClassValidator {
    strict: bool,
    validator: Box<dyn Validator>,
    class: Py<PyType>,
    new_method: PyObject,
}

impl ModelClassValidator {
    pub const EXPECTED_TYPE: &'static str = "model-class";
}

impl Validator for ModelClassValidator {
    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        let class = dict_get_required!(schema, "class", &PyType)?;
        let new_method = class.getattr("__new__")?;
        // `__new__` always exists and is always callable, no point checking `is_callable` here

        let model_schema = dict_get_required!(schema, "model", &PyDict)?;
        let model_type = dict_get_required!(model_schema, "type", String)?;
        if &model_type != "model" {
            return py_error!("model-class expected a 'model' schema, got '{}'", model_type);
        }

        Ok(Box::new(Self {
            // we don't use is_strict here since we don't wan validation to be strict in this case if
            // `config.strict` is set, only if this specific field is strict
            strict: dict_get!(schema, "strict", bool).unwrap_or(false),
            validator: build_validator(model_schema, config)?,
            class: class.into(),
            new_method: new_method.into(),
        }))
    }

    fn validate(&self, py: Python, input: &dyn Input, extra: &Extra) -> ValResult<PyObject> {
        let class = self.class.as_ref(py);
        if input.strict_model_check(class)? {
            Ok(input.to_py(py))
        } else if self.strict {
            err_val_error!(
                py,
                input,
                kind = ErrorKind::ModelType,
                context = context!("class_name" => class_name(py, class)?)
            )
        } else {
            let output = self.validator.validate(py, input, extra)?;
            self.create_class(py, output).map_err(as_internal)
        }
    }

    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}

/// Get the class's `__name__`, not using `class.name()` since it uses `__qualname__` which is not what we want here
#[inline]
fn class_name(py: Python, class: &PyType) -> ValResult<String> {
    let name = class.getattr(intern!(py, "__name__")).map_err(as_internal)?;
    name.extract().map_err(as_internal)
}

impl ModelClassValidator {
    /// utility used to avoid lots of `.map_err(as_internal)` in `validate()`
    #[inline]
    fn create_class(&self, py: Python, output: PyObject) -> PyResult<PyObject> {
        let t: &PyTuple = output.extract(py)?;
        let model_dict = t.get_item(0)?;
        let fields_set = t.get_item(1)?;

        // TODO would be great if we could create `instance` without resorting to calling `__new__`,
        // if we could convert `self.class` (a `PyType`) to a `PyClass`, we could use `Py::new(...)`, but
        // I can't find a way to do that. `PyObject_New` might be our friend, but I can't find an example of its use.
        let instance = self.new_method.call(py, (&self.class,), None)?;

        force_setattr(&instance, py, intern!(py, "__dict__"), model_dict)?;
        force_setattr(&instance, py, intern!(py, "__fields_set__"), fields_set)?;

        Ok(instance)
    }
}

/// copied and modified from
/// https://github.com/PyO3/pyo3/blob/d2caa056e9aacc46374139ef491d112cb8af1a25/src/instance.rs#L587-L597
/// to use `PyObject_GenericSetAttr` thereby bypassing `__setattr__` methods on the instance,
/// see https://github.com/PyO3/pyo3/discussions/2321 for discussion
pub fn force_setattr<N, V>(obj: &PyObject, py: Python<'_>, attr_name: N, value: V) -> PyResult<()>
where
    N: ToPyObject,
    V: ToPyObject,
{
    attr_name.with_borrowed_ptr(py, move |attr_name| {
        value.with_borrowed_ptr(py, |value| unsafe {
            error_on_minusone(py, ffi::PyObject_GenericSetAttr(obj.as_ptr(), attr_name, value))
        })
    })
}

// Defined here as it's not exported by pyo3
#[inline]
fn error_on_minusone(py: Python<'_>, result: c_int) -> PyResult<()> {
    if result != -1 {
        Ok(())
    } else {
        Err(PyErr::fetch(py))
    }
}
