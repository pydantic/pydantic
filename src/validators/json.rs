use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use jiter::JsonValue;

use crate::errors::{ErrorType, ErrorTypeDefaults, ValError, ValLineError, ValResult};
use crate::input::{EitherBytes, Input, InputType, ValidationMatch};
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
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let validator = match schema.get_as(intern!(schema.py(), "schema"))? {
            Some(schema) => {
                let validator = build_validator(&schema, config, definitions)?;
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
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &impl Input<'py>,
        state: &mut ValidationState,
    ) -> ValResult<PyObject> {
        let v_match = validate_json_bytes(input)?;
        let json_either_bytes = v_match.unpack(state);
        let json_bytes = json_either_bytes.as_slice();
        match self.validator {
            Some(ref validator) => {
                let json_value = JsonValue::parse(json_bytes, true).map_err(|e| map_json_err(input, e, json_bytes))?;
                let mut json_state = state.rebind_extra(|e| {
                    e.input_type = InputType::Json;
                });
                validator.validate(py, &json_value, &mut json_state)
            }
            None => {
                let obj =
                    jiter::python_parse(py, json_bytes, true, true).map_err(|e| map_json_err(input, e, json_bytes))?;
                Ok(obj.unbind())
            }
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}

pub fn validate_json_bytes<'a, 'py>(input: &'a impl Input<'py>) -> ValResult<ValidationMatch<EitherBytes<'a, 'py>>> {
    match input.validate_bytes(false) {
        Ok(v_match) => Ok(v_match),
        Err(ValError::LineErrors(e)) => Err(ValError::LineErrors(
            e.into_iter().map(map_bytes_error).collect::<Vec<_>>(),
        )),
        Err(e) => Err(e),
    }
}

fn map_bytes_error(line_error: ValLineError) -> ValLineError {
    match line_error.error_type {
        ErrorType::BytesType { .. } => {
            ValLineError::new_custom_input(ErrorTypeDefaults::JsonType, line_error.input_value)
        }
        _ => line_error,
    }
}

pub fn map_json_err<'py>(input: &impl Input<'py>, error: jiter::JsonError, json_bytes: &[u8]) -> ValError {
    ValError::new(
        ErrorType::JsonInvalid {
            error: error.description(json_bytes),
            context: None,
        },
        input,
    )
}
