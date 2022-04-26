use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use crate::build_tools::SchemaDict;
use crate::errors::{LocItem, ValError, ValLineError};
use crate::input::Input;

use super::{build_validator, Extra, ValResult, Validator, ValidatorArc};

#[derive(Debug, Clone)]
pub struct UnionValidator {
    choices: Vec<Box<dyn Validator>>,
}

impl UnionValidator {
    pub const EXPECTED_TYPE: &'static str = "union";
}

impl Validator for UnionValidator {
    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        let mut choices: Vec<Box<dyn Validator>> = vec![];
        let choice_schemas: &PyList = schema.get_as_req("choices")?;
        for choice in choice_schemas.iter() {
            choices.push(build_validator(choice, config)?.0);
        }

        Ok(Box::new(Self { choices }))
    }

    fn set_ref(&mut self, name: &str, validator_arc: &ValidatorArc) -> PyResult<()> {
        for validator in self.choices.iter_mut() {
            validator.set_ref(name, validator_arc)?;
        }
        Ok(())
    }

    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        // 1st pass: check if the value is an exact instance of one of the Union types
        for validator in &self.choices {
            if let Ok(output) = validator.validate_strict(py, input, extra) {
                return Ok(output);
            }
        }
        let mut errors: Vec<ValLineError> = Vec::with_capacity(self.choices.len());

        // 3rd pass: check if the value can be coerced into one of the Union types
        for validator in &self.choices {
            let line_errors = match validator.validate(py, input, extra) {
                Ok(item) => return Ok(item),
                Err(ValError::LineErrors(line_errors)) => line_errors,
                Err(err) => return Err(err),
            };

            let loc = vec![LocItem::S(validator.get_name(py))];
            for err in line_errors {
                errors.push(err.with_prefix_location(&loc));
            }
        }
        Err(ValError::LineErrors(errors))
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        self.validate(py, input, extra)
    }

    fn get_name(&self, _py: Python) -> String {
        Self::EXPECTED_TYPE.to_string()
    }

    #[no_coverage]
    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}
