use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::SchemaDict;
use crate::input::Input;

use super::{build_validator, Extra, ValResult, Validator, ValidatorArc};

#[derive(Debug, Clone)]
pub struct OptionalValidator {
    validator: Box<dyn Validator>,
}

impl OptionalValidator {
    pub const EXPECTED_TYPE: &'static str = "optional";
}

impl Validator for OptionalValidator {
    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        let schema: &PyAny = schema.get_as_req("schema")?;
        Ok(Box::new(Self {
            validator: build_validator(schema, config)?.0,
        }))
    }

    fn set_ref(&mut self, name: &str, validator_arc: &ValidatorArc) -> PyResult<()> {
        self.validator.set_ref(name, validator_arc)
    }

    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        match input.is_none(py) {
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
        match input.is_none(py) {
            true => Ok(py.None()),
            false => self.validator.validate_strict(py, input, extra),
        }
    }

    fn get_name(&self, _py: Python) -> String {
        Self::EXPECTED_TYPE.to_string()
    }

    #[no_coverage]
    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}
