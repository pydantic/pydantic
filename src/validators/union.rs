use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use crate::build_tools::{is_strict, SchemaDict};
use crate::errors::{ValError, ValLineError};
use crate::input::Input;

use super::{build_validator, BuildContext, BuildValidator, CombinedValidator, Extra, ValResult, Validator};

#[derive(Debug, Clone)]
pub struct UnionValidator {
    choices: Vec<CombinedValidator>,
    strict: bool,
}

impl BuildValidator for UnionValidator {
    const EXPECTED_TYPE: &'static str = "union";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext,
    ) -> PyResult<CombinedValidator> {
        let choices: Vec<CombinedValidator> = schema
            .get_as_req::<&PyList>("choices")?
            .iter()
            .map(|choice| build_validator(choice, config, build_context).map(|result| result.0))
            .collect::<PyResult<Vec<CombinedValidator>>>()?;
        let strict = is_strict(schema, config)?;
        Ok(Self { choices, strict }.into())
    }
}

impl Validator for UnionValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        if self.strict {
            let mut errors: Vec<ValLineError> = Vec::with_capacity(self.choices.len());

            for validator in &self.choices {
                let line_errors = match validator.validate_strict(py, input, extra, slots) {
                    Err(ValError::LineErrors(line_errors)) => line_errors,
                    otherwise => return otherwise,
                };

                errors.extend(
                    line_errors
                        .into_iter()
                        .map(|err| err.with_outer_location(validator.get_name(py).into())),
                );
            }

            Err(ValError::LineErrors(errors))
        } else {
            // 1st pass: check if the value is an exact instance of one of the Union types
            if let Some(res) = self
                .choices
                .iter()
                .map(|validator| validator.validate_strict(py, input, extra, slots))
                .find(ValResult::is_ok)
            {
                return res;
            }

            let mut errors: Vec<ValLineError> = Vec::with_capacity(self.choices.len());

            // 2nd pass: check if the value can be coerced into one of the Union types
            for validator in &self.choices {
                let line_errors = match validator.validate(py, input, extra, slots) {
                    Err(ValError::LineErrors(line_errors)) => line_errors,
                    otherwise => return otherwise,
                };

                errors.extend(
                    line_errors
                        .into_iter()
                        .map(|err| err.with_outer_location(validator.get_name(py).into())),
                );
            }

            Err(ValError::LineErrors(errors))
        }
    }

    fn get_name(&self, py: Python) -> String {
        let descr = self
            .choices
            .iter()
            .map(|v| v.get_name(py))
            .collect::<Vec<_>>()
            .join(", ");
        format!("{}[{}]", Self::EXPECTED_TYPE, descr)
    }
}
