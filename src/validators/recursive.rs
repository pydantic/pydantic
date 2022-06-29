use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::SchemaDict;
use crate::errors::{err_val_error, ErrorKind, ValResult};
use crate::input::Input;
use crate::recursion_guard::RecursionGuard;

use super::{BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct RecursiveContainerValidator {
    validator_id: usize,
}

impl RecursiveContainerValidator {
    pub fn create(validator_id: usize) -> CombinedValidator {
        Self { validator_id }.into()
    }
}

impl Validator for RecursiveContainerValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        validate(self.validator_id, py, input, extra, slots, recursion_guard)
    }

    fn get_name(&self, _py: Python) -> String {
        "recursive-container".to_string()
    }
}

#[derive(Debug, Clone)]
pub struct RecursiveRefValidator {
    validator_id: usize,
}

impl BuildValidator for RecursiveRefValidator {
    const EXPECTED_TYPE: &'static str = "recursive-ref";

    fn build(
        schema: &PyDict,
        _config: Option<&PyDict>,
        build_context: &mut BuildContext,
    ) -> PyResult<CombinedValidator> {
        let name: String = schema.get_as_req("schema_ref")?;
        let validator_id = build_context.find_slot_id(&name)?;
        Ok(Self { validator_id }.into())
    }
}

impl Validator for RecursiveRefValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        validate(self.validator_id, py, input, extra, slots, recursion_guard)
    }

    fn get_name(&self, _py: Python) -> String {
        Self::EXPECTED_TYPE.to_string()
    }
}

fn validate<'s, 'data>(
    validator_id: usize,
    py: Python<'data>,
    input: &'data impl Input<'data>,
    extra: &Extra,
    slots: &'data [CombinedValidator],
    recursion_guard: &'s mut RecursionGuard,
) -> ValResult<'data, PyObject> {
    if let Some(id) = input.identity() {
        if recursion_guard.contains_or_insert(id) {
            // remove ID in case we use recursion_guard again
            recursion_guard.remove(&id);
            return err_val_error!(kind = ErrorKind::RecursionLoop, input_value = input.as_error_value());
        }
        let validator = unsafe { slots.get_unchecked(validator_id) };
        let output = validator.validate(py, input, extra, slots, recursion_guard);
        recursion_guard.remove(&id);
        output
    } else {
        let validator = unsafe { slots.get_unchecked(validator_id) };
        validator.validate(py, input, extra, slots, recursion_guard)
    }
}
