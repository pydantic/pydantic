use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use crate::build_tools::{is_strict, SchemaDict};
use crate::errors::{ValError, ValLineError, ValResult};
use crate::input::Input;
use crate::recursion_guard::RecursionGuard;

use super::{build_validator, BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct UnionValidator {
    choices: Vec<CombinedValidator>,
    strict: bool,
    name: String,
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

        let descr = choices.iter().map(|v| v.get_name()).collect::<Vec<_>>().join(",");

        Ok(Self {
            choices,
            strict,
            name: format!("{}[{}]", Self::EXPECTED_TYPE, descr),
        }
        .into())
    }
}

impl Validator for UnionValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        if extra.strict.unwrap_or(self.strict) {
            let mut errors: Vec<ValLineError> = Vec::with_capacity(self.choices.len());
            let strict_strict = extra.as_strict();

            for validator in &self.choices {
                let line_errors = match validator.validate(py, input, &strict_strict, slots, recursion_guard) {
                    Err(ValError::LineErrors(line_errors)) => line_errors,
                    otherwise => return otherwise,
                };

                errors.extend(
                    line_errors
                        .into_iter()
                        .map(|err| err.with_outer_location(validator.get_name().into())),
                );
            }

            Err(ValError::LineErrors(errors))
        } else {
            // 1st pass: check if the value is an exact instance of one of the Union types,
            // e.g. use validate in strict mode
            let strict_strict = extra.as_strict();
            if let Some(res) = self
                .choices
                .iter()
                .map(|validator| validator.validate(py, input, &strict_strict, slots, recursion_guard))
                .find(ValResult::is_ok)
            {
                return res;
            }

            let mut errors: Vec<ValLineError> = Vec::with_capacity(self.choices.len());

            // 2nd pass: check if the value can be coerced into one of the Union types, e.g. use validate
            for validator in &self.choices {
                let line_errors = match validator.validate(py, input, extra, slots, recursion_guard) {
                    Err(ValError::LineErrors(line_errors)) => line_errors,
                    success => return success,
                };

                errors.extend(
                    line_errors
                        .into_iter()
                        .map(|err| err.with_outer_location(validator.get_name().into())),
                );
            }

            Err(ValError::LineErrors(errors))
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, build_context: &BuildContext) -> PyResult<()> {
        self.choices.iter_mut().try_for_each(|v| v.complete(build_context))
    }
}
