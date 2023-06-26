use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use crate::build_tools::py_schema_err;
use crate::errors::ValResult;
use crate::input::Input;
use crate::recursion_guard::RecursionGuard;
use crate::tools::SchemaDict;

use super::{build_validator, BuildValidator, CombinedValidator, Definitions, DefinitionsBuilder, Extra, Validator};

#[derive(Debug, Clone)]
pub struct ChainValidator {
    steps: Vec<CombinedValidator>,
    name: String,
}

impl BuildValidator for ChainValidator {
    const EXPECTED_TYPE: &'static str = "chain";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let steps: Vec<CombinedValidator> = schema
            .get_as_req::<&PyList>(intern!(schema.py(), "steps"))?
            .iter()
            .map(|step| build_validator_steps(step, config, definitions))
            .collect::<PyResult<Vec<Vec<CombinedValidator>>>>()?
            .into_iter()
            .flatten()
            .collect::<Vec<CombinedValidator>>();

        match steps.len() {
            0 => py_schema_err!("One or more steps are required for a chain validator"),
            1 => {
                let step = steps.into_iter().next().unwrap();
                Ok(step)
            }
            _ => {
                let descr = steps.iter().map(Validator::get_name).collect::<Vec<_>>().join(",");

                Ok(Self {
                    steps,
                    name: format!("{}[{descr}]", Self::EXPECTED_TYPE),
                }
                .into())
            }
        }
    }
}

// either a vec of the steps from a nested `ChainValidator`, or a length-1 vec containing the validator
// to be flattened into `steps` above
fn build_validator_steps<'a>(
    step: &'a PyAny,
    config: Option<&'a PyDict>,
    definitions: &mut DefinitionsBuilder<CombinedValidator>,
) -> PyResult<Vec<CombinedValidator>> {
    let validator = build_validator(step, config, definitions)?;
    if let CombinedValidator::Chain(chain_validator) = validator {
        Ok(chain_validator.steps)
    } else {
        Ok(vec![validator])
    }
}

impl Validator for ChainValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        definitions: &'data Definitions<CombinedValidator>,
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let mut steps_iter = self.steps.iter();
        let first_step = steps_iter.next().unwrap();
        let value = first_step.validate(py, input, extra, definitions, recursion_guard)?;

        steps_iter.try_fold(value, |v, step| {
            step.validate(py, v.into_ref(py), extra, definitions, recursion_guard)
        })
    }

    fn different_strict_behavior(
        &self,
        definitions: Option<&DefinitionsBuilder<CombinedValidator>>,
        ultra_strict: bool,
    ) -> bool {
        self.steps
            .iter()
            .any(|v| v.different_strict_behavior(definitions, ultra_strict))
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, definitions: &DefinitionsBuilder<CombinedValidator>) -> PyResult<()> {
        self.steps.iter_mut().try_for_each(|v| v.complete(definitions))
    }
}
