use std::sync::Arc;

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
    steps: Vec<Arc<CombinedValidator>>,
    name: String,
}

impl BuildValidator for ChainValidator {
    const EXPECTED_TYPE: &'static str = "chain";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedValidator>>,
    ) -> PyResult<Arc<CombinedValidator>> {
        let steps: Vec<Arc<CombinedValidator>> = schema
            .get_as_req::<Bound<'_, PyList>>(intern!(schema.py(), "steps"))?
            .iter()
            .map(|step| build_validator_steps(&step, config, definitions))
            .collect::<PyResult<Vec<Vec<Arc<CombinedValidator>>>>>()?
            .into_iter()
            .flatten()
            .collect();

        match steps.len() {
            0 => py_schema_err!("One or more steps are required for a chain validator"),
            1 => {
                let step = steps.into_iter().next().unwrap();
                Ok(step)
            }
            _ => {
                let descr = steps.iter().map(|v| v.get_name()).collect::<Vec<_>>().join(",");

                Ok(CombinedValidator::Chain(Self {
                    steps,
                    name: format!("{}[{descr}]", Self::EXPECTED_TYPE),
                })
                .into())
            }
        }
    }
}

// either a vec of the steps from a nested `ChainValidator`, or a length-1 vec containing the validator
// to be flattened into `steps` above
fn build_validator_steps(
    step: &Bound<'_, PyAny>,
    config: Option<&Bound<'_, PyDict>>,
    definitions: &mut DefinitionsBuilder<Arc<CombinedValidator>>,
) -> PyResult<Vec<Arc<CombinedValidator>>> {
    let validator = build_validator(step, config, definitions)?;
    if let CombinedValidator::Chain(chain_validator) = validator.as_ref() {
        Ok(chain_validator.steps.clone())
    } else {
        Ok(vec![validator])
    }
}

impl_py_gc_traverse!(ChainValidator { steps });

impl Validator for ChainValidator {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Py<PyAny>> {
        let mut steps_iter = self.steps.iter();
        let first_step = steps_iter.next().unwrap();
        let value = first_step.validate(py, input, state)?;

        steps_iter.try_fold(value, |v, step| step.validate(py, v.bind(py), state))
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}
