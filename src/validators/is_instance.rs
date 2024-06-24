use pyo3::exceptions::PyNotImplementedError;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyType};

use crate::build_tools::py_schema_err;
use crate::errors::{ErrorType, ValError, ValResult};
use crate::input::Input;
use crate::tools::SchemaDict;

use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

#[derive(Debug, Clone)]
pub struct IsInstanceValidator {
    class: PyObject,
    class_repr: String,
    name: String,
}

impl BuildValidator for IsInstanceValidator {
    const EXPECTED_TYPE: &'static str = "is-instance";

    fn build(
        schema: &Bound<'_, PyDict>,
        _config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let cls_key = intern!(py, "cls");
        let class = schema.get_as_req(cls_key)?;

        // test that class works with isinstance to avoid errors at call time, reuse cls_key since it doesn't
        // matter what object is being checked
        if cls_key.is_instance(&class).is_err() {
            return py_schema_err!("'cls' must be valid as the first argument to 'isinstance'");
        }

        let class_repr = class_repr(schema, &class)?;
        let name = format!("{}[{class_repr}]", Self::EXPECTED_TYPE);
        Ok(Self {
            class: class.into(),
            class_repr,
            name,
        }
        .into())
    }
}

impl_py_gc_traverse!(IsInstanceValidator { class });

impl Validator for IsInstanceValidator {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        _state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<PyObject> {
        let Some(obj) = input.as_python() else {
            return Err(ValError::InternalErr(PyNotImplementedError::new_err(
                "Cannot check isinstance when validating from json, \
                            use a JsonOrPython validator instead.",
            )));
        };
        match obj.is_instance(self.class.bind(py))? {
            true => Ok(obj.clone().unbind()),
            false => Err(ValError::new(
                ErrorType::IsInstanceOf {
                    class: self.class_repr.clone(),
                    context: None,
                },
                input,
            )),
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}

pub fn class_repr(schema: &Bound<'_, PyDict>, class: &Bound<'_, PyAny>) -> PyResult<String> {
    match schema.get_as(intern!(schema.py(), "cls_repr"))? {
        Some(s) => Ok(s),
        None => match class.downcast::<PyType>() {
            Ok(t) => Ok(t.qualname()?.to_string()),
            Err(_) => Ok(class.repr()?.extract()?),
        },
    }
}
