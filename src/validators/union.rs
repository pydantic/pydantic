use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use super::{build_validator, Extra, ValResult, Validator};
use crate::build_macros::dict_get_required;
use crate::errors::{LocItem, ValError, ValLineError};
use crate::input::Input;

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
        let choice_schemas: &PyList = dict_get_required!(schema, "choices", &PyList)?;
        for choice in choice_schemas.iter() {
            let choice_dict: &PyDict = choice.extract()?;
            choices.push(build_validator(choice_dict, config)?);
        }

        Ok(Box::new(Self { choices }))
    }

    fn validate(&self, py: Python, input: &dyn Input, extra: &Extra) -> ValResult<PyObject> {
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
                errors.push(err.prefix_location(&loc));
            }
        }
        Err(ValError::LineErrors(errors))
    }

    fn validate_strict(&self, py: Python, input: &dyn Input, extra: &Extra) -> ValResult<PyObject> {
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
