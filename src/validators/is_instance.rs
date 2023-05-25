use pyo3::exceptions::PyNotImplementedError;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyType};

use crate::build_tools::py_schema_err;
use crate::errors::{ErrorType, ValError, ValResult};
use crate::input::Input;
use crate::recursion_guard::RecursionGuard;
use crate::tools::SchemaDict;

use super::InputType;
use super::{BuildValidator, CombinedValidator, Definitions, DefinitionsBuilder, Extra, Validator};

#[derive(Debug, Clone)]
pub struct IsInstanceValidator {
    class: PyObject,
    class_repr: String,
    name: String,
}

impl BuildValidator for IsInstanceValidator {
    const EXPECTED_TYPE: &'static str = "is-instance";

    fn build(
        schema: &PyDict,
        _config: Option<&PyDict>,
        _definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let cls_key = intern!(py, "cls");
        let class: &PyAny = schema.get_as_req(cls_key)?;

        // test that class works with isinstance to avoid errors at call time, reuse cls_key since it doesn't
        // matter what object is being checked
        let test_value: &PyAny = cls_key.as_ref();
        if test_value.is_instance(class).is_err() {
            return py_schema_err!("'cls' must be valid as the first argument to 'isinstance'");
        }

        let class_repr = match schema.get_as(intern!(py, "cls_repr"))? {
            Some(s) => s,
            None => match class.extract::<&PyType>() {
                Ok(t) => t.name()?.to_string(),
                Err(_) => class.repr()?.extract()?,
            },
        };
        let name = format!("{}[{class_repr}]", Self::EXPECTED_TYPE);
        Ok(Self {
            class: class.into(),
            class_repr,
            name,
        }
        .into())
    }
}

impl Validator for IsInstanceValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        _definitions: &'data Definitions<CombinedValidator>,
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        match extra.mode {
            InputType::Json => Err(ValError::InternalErr(PyNotImplementedError::new_err(
                "Cannot check isinstance when validating from json,\
                            use a JsonOrPython validator instead.",
            ))),
            InputType::Python => {
                let ob = input.to_object(py);
                match ob.as_ref(py).is_instance(self.class.as_ref(py))? {
                    true => Ok(ob),
                    false => Err(ValError::new(
                        ErrorType::IsInstanceOf {
                            class: self.class_repr.clone(),
                        },
                        input,
                    )),
                }
            }
        }
    }

    fn different_strict_behavior(
        &self,
        _definitions: Option<&DefinitionsBuilder<CombinedValidator>>,
        _ultra_strict: bool,
    ) -> bool {
        false
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, _definitions: &DefinitionsBuilder<CombinedValidator>) -> PyResult<()> {
        Ok(())
    }
}
