use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use crate::build_tools::py_schema_err;
use crate::errors::ValResult;
use crate::input::Input;
use crate::tools::SchemaDict;

use super::validation_state::ValidationState;
use super::{build_validator, BuildValidator, CombinedValidator, DefinitionsBuilder, Validator};

#[derive(Debug)]
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

impl_py_gc_traverse!(ChainValidator { steps });

impl Validator for ChainValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<PyObject> {
        let mut steps_iter = self.steps.iter();
        let first_step = steps_iter.next().unwrap();
        let value = first_step.validate(py, input, state)?;

        steps_iter.try_fold(value, |v, step| step.validate(py, v.into_ref(py), state))
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}
