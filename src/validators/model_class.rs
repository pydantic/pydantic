use std::os::raw::c_int;
use std::ptr::null_mut;

use pyo3::conversion::AsPyPointer;
use pyo3::exceptions::PyTypeError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyTuple, PyType};
use pyo3::{ffi, intern};

use crate::build_tools::{py_error, SchemaDict};
use crate::errors::{as_internal, context, err_val_error, ErrorKind, InputValue, ValError, ValResult};
use crate::input::Input;

use super::{build_validator, BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct ModelClassValidator {
    strict: bool,
    validator: Box<CombinedValidator>,
    class: Py<PyType>,
}

impl BuildValidator for ModelClassValidator {
    const EXPECTED_TYPE: &'static str = "model-class";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext,
    ) -> PyResult<CombinedValidator> {
        let class: &PyType = schema.get_as_req("class_type")?;

        let model_schema_raw: &PyAny = schema.get_as_req("model")?;
        let (validator, model_schema) = build_validator(model_schema_raw, config, build_context)?;
        let model_type: String = model_schema.get_as_req("type")?;
        if &model_type != "model" {
            return py_error!("model-class expected a 'model' schema, got '{}'", model_type);
        }

        Ok(Self {
            // we don't use is_strict here since we don't wan validation to be strict in this case if
            // `config.strict` is set, only if this specific field is strict
            strict: schema.get_as("strict")?.unwrap_or(false),
            validator: Box::new(validator),
            class: class.into(),
        }
        .into())
    }
}

impl Validator for ModelClassValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
        slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        let class = self.class.as_ref(py);
        if input.strict_model_check(class)? {
            Ok(input.to_py(py))
        } else if self.strict {
            err_val_error!(
                input_value = InputValue::InputRef(input),
                kind = ErrorKind::ModelType,
                context = context!("class_name" => self.get_name(py))
            )
        } else {
            let output = self.validator.validate(py, input, extra, slots)?;
            self.create_class(py, output).map_err(as_internal)
        }
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        if input.strict_model_check(self.class.as_ref(py))? {
            Ok(input.to_py(py))
        } else {
            // errors from `validate_strict` are never used used, so we can keep this simple
            Err(ValError::LineErrors(vec![]))
        }
    }

    fn get_name(&self, py: Python) -> String {
        // Get the class's `__name__`, not using `class.name()` since it uses `__qualname__`
        // which is not what we want here
        let class = self.class.as_ref(py);
        let name_result: PyResult<&str> = match class.getattr(intern!(py, "__name__")) {
            Ok(name) => name.extract(),
            Err(e) => Err(e),
        };
        name_result.unwrap_or("ModelClass").to_string()
    }
}

impl ModelClassValidator {
    fn create_class(&self, py: Python, output: PyObject) -> PyResult<PyObject> {
        let (model_dict, fields_set): (&PyAny, &PyAny) = output.extract(py)?;

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
                None => return Err(PyTypeError::new_err("base type without tp_new")),
            }
        };

        let instance_ref = instance.as_ref(py);
        force_setattr(py, instance_ref, intern!(py, "__dict__"), model_dict)?;
        force_setattr(py, instance_ref, intern!(py, "__fields_set__"), fields_set)?;

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
        error_on_minusone(
            py,
            ffi::PyObject_GenericSetAttr(obj.as_ptr(), attr_name.as_ptr(), value.as_ptr()),
        )
    }
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
