use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyType};

use crate::errors::{ErrorType, ValError, ValResult};
use crate::input::Input;
use crate::tools::SchemaDict;

use super::ValidationState;
use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, Validator};

#[derive(Debug, Clone)]
pub struct IsSubclassValidator {
    class: Py<PyType>,
    class_repr: String,
    name: String,
}

impl BuildValidator for IsSubclassValidator {
    const EXPECTED_TYPE: &'static str = "is-subclass";

    fn build(
        schema: &PyDict,
        _config: Option<&PyDict>,
        _definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let class: &PyType = schema.get_as_req(intern!(py, "cls"))?;

        let class_repr = match schema.get_as(intern!(py, "cls_repr"))? {
            Some(s) => s,
            None => class.name()?.to_string(),
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

impl_py_gc_traverse!(IsSubclassValidator { class });

impl Validator for IsSubclassValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        match input.input_is_subclass(self.class.as_ref(py))? {
            true => Ok(input.to_object(py)),
            false => Err(ValError::new(
                ErrorType::IsSubclassOf {
                    class: self.class_repr.clone(),
                    context: None,
                },
                input,
            )),
        }
    }

    fn different_strict_behavior(&self, _ultra_strict: bool) -> bool {
        false
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&self) -> PyResult<()> {
        Ok(())
    }
}
