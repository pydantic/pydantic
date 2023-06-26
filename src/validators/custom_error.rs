use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::py_schema_err;
use crate::errors::{ErrorType, PydanticCustomError, PydanticKnownError, ValError, ValResult};
use crate::input::Input;
use crate::recursion_guard::RecursionGuard;
use crate::tools::SchemaDict;

use super::{build_validator, BuildValidator, CombinedValidator, Definitions, DefinitionsBuilder, Extra, Validator};

#[derive(Debug, Clone)]
pub enum CustomError {
    Custom(PydanticCustomError),
    KnownError(PydanticKnownError),
}

impl CustomError {
    pub fn build(
        schema: &PyDict,
        _config: Option<&PyDict>,
        _definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<Option<Self>> {
        let py = schema.py();
        let error_type: String = match schema.get_as(intern!(py, "custom_error_type"))? {
            Some(error_type) => error_type,
            None => return Ok(None),
        };
        let context: Option<&PyDict> = schema.get_as(intern!(py, "custom_error_context"))?;

        if ErrorType::valid_type(py, &error_type) {
            if schema.contains(intern!(py, "custom_error_message"))? {
                py_schema_err!(
                    "custom_error_message should not be provided if 'custom_error_type' matches a known error"
                )
            } else {
                let error = PydanticKnownError::py_new(py, &error_type, context)?;
                Ok(Some(Self::KnownError(error)))
            }
        } else {
            let error = PydanticCustomError::py_new(
                py,
                error_type,
                schema.get_as_req::<String>(intern!(py, "custom_error_message"))?,
                context,
            );
            Ok(Some(Self::Custom(error)))
        }
    }

    pub fn as_val_error<'a>(&self, input: &'a impl Input<'a>) -> ValError<'a> {
        match self {
            CustomError::KnownError(ref known_error) => known_error.clone().into_val_error(input),
            CustomError::Custom(ref custom_error) => custom_error.clone().into_val_error(input),
        }
    }
}

#[derive(Debug, Clone)]
pub struct CustomErrorValidator {
    validator: Box<CombinedValidator>,
    custom_error: CustomError,
    name: String,
}

impl BuildValidator for CustomErrorValidator {
    const EXPECTED_TYPE: &'static str = "custom-error";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let custom_error = CustomError::build(schema, config, definitions)?.unwrap();
        let schema: &PyAny = schema.get_as_req(intern!(schema.py(), "schema"))?;
        let validator = Box::new(build_validator(schema, config, definitions)?);
        let name = format!("{}[{}]", Self::EXPECTED_TYPE, validator.get_name());
        Ok(Self {
            validator,
            custom_error,
            name,
        }
        .into())
    }
}

impl Validator for CustomErrorValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        definitions: &'data Definitions<CombinedValidator>,
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        self.validator
            .validate(py, input, extra, definitions, recursion_guard)
            .map_err(|_| self.custom_error.as_val_error(input))
    }

    fn different_strict_behavior(
        &self,
        definitions: Option<&DefinitionsBuilder<CombinedValidator>>,
        ultra_strict: bool,
    ) -> bool {
        self.validator.different_strict_behavior(definitions, ultra_strict)
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, definitions: &DefinitionsBuilder<CombinedValidator>) -> PyResult<()> {
        self.validator.complete(definitions)
    }
}
