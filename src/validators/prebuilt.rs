use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::common::prebuilt::get_prebuilt;
use crate::errors::ValResult;
use crate::input::Input;

use super::ValidationState;
use super::{CombinedValidator, SchemaValidator, Validator};

#[derive(Debug)]
pub struct PrebuiltValidator {
    schema_validator: Py<SchemaValidator>,
}

impl PrebuiltValidator {
    pub fn try_get_from_schema(type_: &str, schema: &Bound<'_, PyDict>) -> PyResult<Option<CombinedValidator>> {
        get_prebuilt(type_, schema, "__pydantic_validator__", |py_any| {
            let schema_validator = py_any.extract::<Py<SchemaValidator>>()?;
            if matches!(
                schema_validator.get().validator,
                CombinedValidator::FunctionWrap(_) | CombinedValidator::FunctionAfter(_)
            ) {
                return Ok(None);
            }
            Ok(Some(Self { schema_validator }.into()))
        })
    }
}

impl_py_gc_traverse!(PrebuiltValidator { schema_validator });

impl Validator for PrebuiltValidator {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<PyObject> {
        self.schema_validator.get().validator.validate(py, input, state)
    }

    fn get_name(&self) -> &str {
        self.schema_validator.get().validator.get_name()
    }
}
