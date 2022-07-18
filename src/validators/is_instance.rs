use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyType};

use crate::build_tools::SchemaDict;
use crate::errors::{ErrorKind, ValError, ValResult};
use crate::input::Input;
use crate::recursion_guard::RecursionGuard;

use super::{BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct IsInstanceValidator {
    class: Py<PyType>,
    class_repr: String,
    name: String,
}

impl BuildValidator for IsInstanceValidator {
    const EXPECTED_TYPE: &'static str = "is-instance";

    fn build(
        schema: &PyDict,
        _config: Option<&PyDict>,
        _build_context: &mut BuildContext,
    ) -> PyResult<CombinedValidator> {
        let class: &PyType = schema.get_as_req(intern!(schema.py(), "class_"))?;
        let class_repr = class.name()?.to_string();
        let name = format!("{}[{}]", Self::EXPECTED_TYPE, class_repr);
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
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        match input.is_instance(self.class.as_ref(py))? {
            true => Ok(input.to_object(py)),
            false => Err(ValError::new(
                ErrorKind::IsInstanceOf {
                    class: self.class_repr.clone(),
                },
                input,
            )),
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}
