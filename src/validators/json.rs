use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::errors::ValResult;
use crate::input::Input;
use crate::recursion_guard::RecursionGuard;
use crate::tools::SchemaDict;

use super::{build_validator, BuildValidator, CombinedValidator, Definitions, DefinitionsBuilder, Extra, Validator};

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
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let validator = match schema.get_as(intern!(schema.py(), "schema"))? {
            Some(schema) => {
                let validator = build_validator(schema, config, definitions)?;
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
            validator.as_ref().map_or("any", |v| v.get_name())
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
        definitions: &'data Definitions<CombinedValidator>,
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let json_value = input.parse_json()?;
        match self.validator {
            Some(ref validator) => match validator.validate(py, &json_value, extra, definitions, recursion_guard) {
                Ok(v) => Ok(v),
                Err(err) => Err(err.duplicate(py)),
            },
            None => Ok(json_value.to_object(py)),
        }
    }

    fn different_strict_behavior(
        &self,
        definitions: Option<&DefinitionsBuilder<CombinedValidator>>,
        ultra_strict: bool,
    ) -> bool {
        if let Some(ref v) = self.validator {
            v.different_strict_behavior(definitions, ultra_strict)
        } else {
            false
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, definitions: &DefinitionsBuilder<CombinedValidator>) -> PyResult<()> {
        match self.validator {
            Some(ref mut v) => v.complete(definitions),
            None => Ok(()),
        }
    }
}
