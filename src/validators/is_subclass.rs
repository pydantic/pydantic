use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyType};

use crate::errors::{ErrorType, ValError, ValResult};
use crate::input::Input;
use crate::tools::SchemaDict;

use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

#[derive(Debug, Clone)]
pub struct IsSubclassValidator {
    class: Py<PyType>,
    class_repr: String,
    name: String,
}

impl BuildValidator for IsSubclassValidator {
    const EXPECTED_TYPE: &'static str = "is-subclass";

    fn build(
        schema: &Bound<'_, PyDict>,
        _config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let class = schema.get_as_req::<Bound<'_, PyType>>(intern!(py, "cls"))?;

        let class_repr = match schema.get_as(intern!(py, "cls_repr"))? {
            Some(s) => s,
            None => class.qualname()?.to_string(),
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
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        _state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<PyObject> {
        let Some(obj) = input.as_python() else {
            let method_name = "issubclass".to_string();
            return Err(ValError::new(
                ErrorType::NeedsPythonObject {
                    context: None,
                    method_name,
                },
                input,
            ));
        };
        match obj.downcast::<PyType>() {
            Ok(py_type) if py_type.is_subclass(self.class.bind(py))? => Ok(obj.clone().unbind()),
            _ => Err(ValError::new(
                ErrorType::IsSubclassOf {
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
