use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyString;
use pyo3::types::{PyDict, PyList};

use crate::definitions::DefinitionRef;
use crate::errors::{ErrorTypeDefaults, ValError, ValResult};
use crate::input::Input;

use crate::recursion_guard::RecursionGuard;
use crate::tools::SchemaDict;

use super::{build_validator, BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

#[derive(Debug, Clone)]
pub struct DefinitionsValidatorBuilder;

impl BuildValidator for DefinitionsValidatorBuilder {
    const EXPECTED_TYPE: &'static str = "definitions";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();

        let schema_definitions: Bound<'_, PyList> = schema.get_as_req(intern!(py, "definitions"))?;

        for schema_definition in schema_definitions {
            let reference = schema_definition
                .extract::<Bound<'_, PyDict>>()?
                .get_as_req::<String>(intern!(py, "ref"))?;
            let validator = build_validator(&schema_definition, config, definitions)?;
            definitions.add_definition(reference, validator)?;
        }

        let inner_schema = schema.get_as_req(intern!(py, "schema"))?;
        build_validator(&inner_schema, config, definitions)
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
        schema: &Bound<'_, PyDict>,
        _config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let schema_ref: Bound<'_, PyString> = schema.get_as_req(intern!(schema.py(), "schema_ref"))?;

        let definition = definitions.get_definition(schema_ref.to_str()?);
        Ok(Self::new(definition).into())
    }
}

impl_py_gc_traverse!(DefinitionRefValidator {});

impl Validator for DefinitionRefValidator {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<PyObject> {
        self.definition.read(|validator| {
            let validator = validator.unwrap();
            if let Some(id) = input.as_python().map(py_identity) {
                // Python objects can be cyclic, so need recursion guard
                let Ok(mut guard) = RecursionGuard::new(state, id, self.definition.id()) else {
                    return Err(ValError::new(ErrorTypeDefaults::RecursionLoop, input));
                };
                validator.validate(py, input, guard.state())
            } else {
                validator.validate(py, input, state)
            }
        })
    }

    fn validate_assignment<'py>(
        &self,
        py: Python<'py>,
        obj: &Bound<'py, PyAny>,
        field_name: &str,
        field_value: &Bound<'py, PyAny>,
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<PyObject> {
        self.definition.read(|validator| {
            let validator = validator.unwrap();
            let Ok(mut guard) = RecursionGuard::new(state, py_identity(obj), self.definition.id()) else {
                return Err(ValError::new(ErrorTypeDefaults::RecursionLoop, obj));
            };
            validator.validate_assignment(py, obj, field_name, field_value, guard.state())
        })
    }

    fn get_name(&self) -> &str {
        self.definition.get_or_init_name(|v| v.get_name().into())
    }
}

fn py_identity(obj: &Bound<'_, PyAny>) -> usize {
    obj.as_ptr() as usize
}
