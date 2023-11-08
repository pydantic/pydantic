use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use crate::definitions::DefinitionRef;
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
    definition: DefinitionRef<CombinedValidator>,
}

impl DefinitionRefValidator {
    pub fn new(definition: DefinitionRef<CombinedValidator>) -> Self {
        Self { definition }
    }
}

impl BuildValidator for DefinitionRefValidator {
    const EXPECTED_TYPE: &'static str = "definition-ref";

    fn build(
        schema: &PyDict,
        _config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let schema_ref = schema.get_as_req(intern!(schema.py(), "schema_ref"))?;

        let definition = definitions.get_definition(schema_ref);
        Ok(Self::new(definition).into())
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
        let validator = self.definition.get().unwrap();
        if let Some(id) = input.identity() {
            if state.recursion_guard.contains_or_insert(id, self.definition.id()) {
                // we don't remove id here, we leave that to the validator which originally added id to `recursion_guard`
                Err(ValError::new(ErrorTypeDefaults::RecursionLoop, input))
            } else {
                if state.recursion_guard.incr_depth() {
                    return Err(ValError::new(ErrorTypeDefaults::RecursionLoop, input));
                }
                let output = validator.validate(py, input, state);
                state.recursion_guard.remove(id, self.definition.id());
                state.recursion_guard.decr_depth();
                output
            }
        } else {
            validator.validate(py, input, state)
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
        let validator = self.definition.get().unwrap();
        if let Some(id) = obj.identity() {
            if state.recursion_guard.contains_or_insert(id, self.definition.id()) {
                // we don't remove id here, we leave that to the validator which originally added id to `recursion_guard`
                Err(ValError::new(ErrorTypeDefaults::RecursionLoop, obj))
            } else {
                if state.recursion_guard.incr_depth() {
                    return Err(ValError::new(ErrorTypeDefaults::RecursionLoop, obj));
                }
                let output = validator.validate_assignment(py, obj, field_name, field_value, state);
                state.recursion_guard.remove(id, self.definition.id());
                state.recursion_guard.decr_depth();
                output
            }
        } else {
            validator.validate_assignment(py, obj, field_name, field_value, state)
        }
    }

    fn get_name(&self) -> &str {
        self.definition.get_or_init_name(|v| v.get_name().into())
    }
}
