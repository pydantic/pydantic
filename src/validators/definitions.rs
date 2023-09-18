use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use crate::errors::{ErrorTypeDefaults, ValError, ValResult};
use crate::input::Input;

use crate::tools::SchemaDict;

use super::{build_validator, BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

#[derive(Debug, Clone)]
pub struct DefinitionsValidatorBuilder;

impl BuildValidator for DefinitionsValidatorBuilder {
    const EXPECTED_TYPE: &'static str = "definitions";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();

        let schema_definitions: &PyList = schema.get_as_req(intern!(py, "definitions"))?;

        for schema_definition in schema_definitions {
            let reference = schema_definition
                .extract::<&PyDict>()?
                .get_as_req::<String>(intern!(py, "ref"))?;
            let validator = build_validator(schema_definition, config, definitions)?;
            definitions.add_definition(reference, validator)?;
        }

        let inner_schema: &PyAny = schema.get_as_req(intern!(py, "schema"))?;
        build_validator(inner_schema, config, definitions)
    }
}

#[derive(Debug, Clone)]
pub struct DefinitionRefValidator {
    validator_id: usize,
    inner_name: String,
    // we have to record the answers to `Question`s as we can't access the validator when `ask()` is called
}

impl DefinitionRefValidator {
    pub fn new(validator_id: usize) -> Self {
        Self {
            validator_id,
            inner_name: "...".to_string(),
        }
    }
}

impl BuildValidator for DefinitionRefValidator {
    const EXPECTED_TYPE: &'static str = "definition-ref";

    fn build(
        schema: &PyDict,
        _config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let schema_ref: String = schema.get_as_req(intern!(schema.py(), "schema_ref"))?;

        let validator_id = definitions.get_reference_id(&schema_ref);

        Ok(Self {
            validator_id,
            inner_name: "...".to_string(),
        }
        .into())
    }
}

impl_py_gc_traverse!(DefinitionRefValidator {});

impl Validator for DefinitionRefValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        if let Some(id) = input.identity() {
            if state.recursion_guard.contains_or_insert(id, self.validator_id) {
                // we don't remove id here, we leave that to the validator which originally added id to `recursion_guard`
                Err(ValError::new(ErrorTypeDefaults::RecursionLoop, input))
            } else {
                if state.recursion_guard.incr_depth() {
                    return Err(ValError::new(ErrorTypeDefaults::RecursionLoop, input));
                }
                let output = validate(self.validator_id, py, input, state);
                state.recursion_guard.remove(id, self.validator_id);
                state.recursion_guard.decr_depth();
                output
            }
        } else {
            validate(self.validator_id, py, input, state)
        }
    }

    fn validate_assignment<'data>(
        &self,
        py: Python<'data>,
        obj: &'data PyAny,
        field_name: &'data str,
        field_value: &'data PyAny,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        if let Some(id) = obj.identity() {
            if state.recursion_guard.contains_or_insert(id, self.validator_id) {
                // we don't remove id here, we leave that to the validator which originally added id to `recursion_guard`
                Err(ValError::new(ErrorTypeDefaults::RecursionLoop, obj))
            } else {
                if state.recursion_guard.incr_depth() {
                    return Err(ValError::new(ErrorTypeDefaults::RecursionLoop, obj));
                }
                let output = validate_assignment(self.validator_id, py, obj, field_name, field_value, state);
                state.recursion_guard.remove(id, self.validator_id);
                state.recursion_guard.decr_depth();
                output
            }
        } else {
            validate_assignment(self.validator_id, py, obj, field_name, field_value, state)
        }
    }

    fn different_strict_behavior(
        &self,
        definitions: Option<&DefinitionsBuilder<CombinedValidator>>,
        ultra_strict: bool,
    ) -> bool {
        if let Some(definitions) = definitions {
            // have to unwrap here, because we can't return an error from this function, should be okay
            let validator = definitions.get_definition(self.validator_id).unwrap();
            validator.different_strict_behavior(None, ultra_strict)
        } else {
            false
        }
    }

    fn get_name(&self) -> &str {
        &self.inner_name
    }

    /// don't need to call complete on the inner validator here, complete_validators takes care of that.
    fn complete(&mut self, definitions: &DefinitionsBuilder<CombinedValidator>) -> PyResult<()> {
        let validator = definitions.get_definition(self.validator_id)?;
        self.inner_name = validator.get_name().to_string();
        Ok(())
    }
}

fn validate<'data>(
    validator_id: usize,
    py: Python<'data>,
    input: &'data impl Input<'data>,
    state: &mut ValidationState,
) -> ValResult<'data, PyObject> {
    let validator = state.definitions.get(validator_id).unwrap();
    validator.validate(py, input, state)
}

#[allow(clippy::too_many_arguments)]
fn validate_assignment<'data>(
    validator_id: usize,
    py: Python<'data>,
    obj: &'data PyAny,
    field_name: &'data str,
    field_value: &'data PyAny,
    state: &mut ValidationState,
) -> ValResult<'data, PyObject> {
    let validator = state.definitions.get(validator_id).unwrap();
    validator.validate_assignment(py, obj, field_name, field_value, state)
}
