use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::SchemaDict;
use crate::errors::ValResult;
use crate::input::Input;
use crate::questions::Question;
use crate::recursion_guard::RecursionGuard;

use super::{build_validator, BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct JsonValidator {
    validator: Option<Box<CombinedValidator>>,
    name: String,
}

impl BuildValidator for JsonValidator {
    const EXPECTED_TYPE: &'static str = "json";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let validator = match schema.get_as(intern!(schema.py(), "schema"))? {
            Some(schema) => {
                let validator = build_validator(schema, config, build_context)?;
                match validator {
                    CombinedValidator::Any(_) => None,
                    _ => Some(Box::new(validator)),
                }
            }
            None => None,
        };
        let name = format!(
            "{}[{}]",
            Self::EXPECTED_TYPE,
            validator.as_ref().map(|v| v.get_name()).unwrap_or("any")
        );
        Ok(Self { validator, name }.into())
    }
}

impl Validator for JsonValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let json_value = input.parse_json()?;
        match self.validator {
            Some(ref validator) => match validator.validate(py, &json_value, extra, slots, recursion_guard) {
                Ok(v) => Ok(v),
                Err(err) => Err(err.duplicate(py)),
            },
            None => Ok(json_value.to_object(py)),
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn ask(&self, question: &Question) -> bool {
        self.validator.as_ref().map(|v| v.ask(question)).unwrap_or(false)
    }

    fn complete(&mut self, build_context: &BuildContext<CombinedValidator>) -> PyResult<()> {
        match self.validator {
            Some(ref mut v) => v.complete(build_context),
            None => Ok(()),
        }
    }
}
