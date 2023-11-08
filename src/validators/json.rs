use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::errors::ValResult;
use crate::input::Input;
use crate::tools::SchemaDict;

use super::{build_validator, BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

#[derive(Debug)]
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

impl_py_gc_traverse!(JsonValidator { validator });

impl Validator for JsonValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        let json_value = input.parse_json()?;
        match self.validator {
            Some(ref validator) => match validator.validate(py, &json_value, state) {
                Ok(v) => Ok(v),
                Err(err) => Err(err.into_owned(py)),
            },
            None => Ok(json_value.to_object(py)),
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}
