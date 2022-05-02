use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use crate::build_tools::SchemaDict;
use crate::errors::{LocItem, ValError, ValLineError};
use crate::input::Input;

use super::{build_validator, BuildValidator, Extra, ValResult, ValidateEnum, Validator, ValidatorArc};

#[derive(Debug, Clone)]
pub struct UnionValidator {
    choices: Vec<ValidateEnum>,
}

impl BuildValidator for UnionValidator {
    const EXPECTED_TYPE: &'static str = "union";

    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<ValidateEnum> {
        let choices: Vec<ValidateEnum> = schema
            .get_as_req::<&PyList>("choices")?
            .iter()
            .map(|choice| build_validator(choice, config).map(|result| result.0))
            .collect::<PyResult<Vec<ValidateEnum>>>()?;
        Ok(Self { choices }.into())
    }
}

impl Validator for UnionValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        // 1st pass: check if the value is an exact instance of one of the Union types
        if let Some(res) = self
            .choices
            .iter()
            .map(|validator| validator.validate_strict(py, input, extra))
            .find(ValResult::is_ok)
        {
            return res;
        }

        let mut errors: Vec<ValLineError> = Vec::with_capacity(self.choices.len());

        // 3rd pass: check if the value can be coerced into one of the Union types
        for validator in &self.choices {
            let line_errors = match validator.validate(py, input, extra) {
                Err(ValError::LineErrors(line_errors)) => line_errors,
                otherwise => return otherwise,
            };

            let loc = vec![LocItem::S(validator.get_name(py))];
            errors.extend(line_errors.into_iter().map(|err| err.with_prefix_location(&loc)));
        }

        Err(ValError::LineErrors(errors))
    }

    fn set_ref(&mut self, name: &str, validator_arc: &ValidatorArc) -> PyResult<()> {
        self.choices
            .iter_mut()
            .try_for_each(|validator| validator.set_ref(name, validator_arc))
    }

    fn get_name(&self, _py: Python) -> String {
        Self::EXPECTED_TYPE.to_string()
    }
}
