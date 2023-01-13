use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use crate::build_tools::{py_err, SchemaDict};
use crate::errors::ValResult;
use crate::input::Input;
use crate::questions::Question;
use crate::recursion_guard::RecursionGuard;

use super::{build_validator, BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

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
        build_context: &mut BuildContext<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let steps: Vec<CombinedValidator> = schema
            .get_as_req::<&PyList>(intern!(schema.py(), "steps"))?
            .iter()
            .map(|step| build_validator_steps(step, config, build_context))
            .collect::<PyResult<Vec<Vec<CombinedValidator>>>>()?
            .into_iter()
            .flatten()
            .collect::<Vec<CombinedValidator>>();

        match steps.len() {
            0 => py_err!("One or more steps are required for a chain validator"),
            1 => {
                let step = steps.into_iter().next().unwrap();
                Ok(step)
            }
            _ => {
                let descr = steps.iter().map(|v| v.get_name()).collect::<Vec<_>>().join(",");

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
    build_context: &mut BuildContext<CombinedValidator>,
) -> PyResult<Vec<CombinedValidator>> {
    let validator = build_validator(step, config, build_context)?;
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
        slots: &'data [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let mut steps_iter = self.steps.iter();
        let first_step = steps_iter.next().unwrap();
        let value = first_step.validate(py, input, extra, slots, recursion_guard)?;

        steps_iter.try_fold(value, |v, step| {
            step.validate(py, v.into_ref(py), extra, slots, recursion_guard)
        })
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn ask(&self, question: &Question) -> bool {
        // any makes more sense since at the moment we only use ask for "return_fields_set", might need
        // more complex logic in future
        self.steps.iter().any(|v| v.ask(question))
    }

    fn complete(&mut self, build_context: &BuildContext<CombinedValidator>) -> PyResult<()> {
        self.steps.iter_mut().try_for_each(|v| v.complete(build_context))
    }
}
