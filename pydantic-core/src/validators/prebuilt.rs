use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::common::prebuilt::get_prebuilt;
use crate::errors::ValResult;
use crate::input::Input;

use super::ValidationState;
use super::{CombinedValidator, SchemaValidator, Validator};
use crate::py_gc::PyGcTraverse;

#[derive(Debug, PyGcTraverse)]
pub struct PrebuiltValidator {
    schema_validator: Py<SchemaValidator>,
}

impl PrebuiltValidator {
    pub fn try_get_from_schema(type_: &str, schema: &Bound<'_, PyDict>) -> PyResult<Option<CombinedValidator>> {
        get_prebuilt(type_, schema, "__pydantic_validator__", |py_any| {
            let schema_validator: Py<SchemaValidator> = match py_any.extract() {
                Ok(schema_validator) => schema_validator,
                // `__pydantic_validator__` may be a `PluggableSchemaValidator` instance (from `pydantic.plugin`),
                // which exposes the underlying `SchemaValidator` through this property:
                Err(_) => match py_any.getattr(intern!(py_any.py(), "__pydantic_schema_validator__")) {
                    Ok(inner) => match inner.extract() {
                        Ok(schema_validator) => schema_validator,
                        Err(_) => return Ok(None),
                    },
                    Err(_) => return Ok(None),
                },
            };
            if matches!(
                schema_validator.get().validator.as_ref(),
                CombinedValidator::FunctionWrap(_) | CombinedValidator::FunctionAfter(_)
            ) {
                return Ok(None);
            }
            Ok(Some(Self { schema_validator }.into()))
        })
    }
}

impl Validator for PrebuiltValidator {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Py<PyAny>> {
        self.schema_validator.get().validator.validate(py, input, state)
    }

    fn get_name(&self) -> &str {
        self.schema_validator.get().validator.get_name()
    }
}
