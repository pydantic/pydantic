use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::SchemaDict;
use crate::input::Input;

use super::{build_validator, BuildValidator, Extra, ValResult, ValidateEnum, Validator, ValidatorArc};

#[derive(Debug, Clone)]
pub struct OptionalValidator {
    validator: Box<ValidateEnum>,
}

impl BuildValidator for OptionalValidator {
    const EXPECTED_TYPE: &'static str = "optional";

    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<ValidateEnum> {
        let schema: &PyAny = schema.get_as_req("schema")?;
        Ok(Self {
            validator: Box::new(build_validator(schema, config)?.0),
        }
        .into())
    }
}

impl Validator for OptionalValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        match input.is_none() {
            true => Ok(py.None()),
            false => self.validator.validate(py, input, extra),
        }
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        match input.is_none() {
            true => Ok(py.None()),
            false => self.validator.validate_strict(py, input, extra),
        }
    }

    fn set_ref(&mut self, name: &str, validator_arc: &ValidatorArc) -> PyResult<()> {
        self.validator.set_ref(name, validator_arc)
    }

    fn get_name(&self, _py: Python) -> String {
        Self::EXPECTED_TYPE.to_string()
    }
}
