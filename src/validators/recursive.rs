use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::SchemaDict;
use crate::errors::{ErrorKind, ValError, ValResult};
use crate::input::Input;
use crate::recursion_guard::RecursionGuard;

use super::{BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct RecursiveContainerValidator {
    validator_id: usize,
    inner_name: String,
}

impl RecursiveContainerValidator {
    pub fn create(validator_id: usize, inner_name: String) -> CombinedValidator {
        Self {
            validator_id,
            inner_name,
        }
        .into()
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
        guard_validate(self.validator_id, py, input, extra, slots, recursion_guard)
    }

    fn get_name(&self) -> &str {
        // we just return the inner validator to make the recursive-container invisible in output messages
        &self.inner_name
    }

    // complete is not implemented here, instead complete_validators in mod.rs calls complete()
    // on all validators in slots
}

#[derive(Debug, Clone)]
pub struct RecursiveRefValidator {
    validator_id: usize,
    inner_name: String,
}

impl BuildValidator for RecursiveRefValidator {
    const EXPECTED_TYPE: &'static str = "recursive-ref";

    fn build(
        schema: &PyDict,
        _config: Option<&PyDict>,
        build_context: &mut BuildContext,
    ) -> PyResult<CombinedValidator> {
        let name: String = schema.get_as_req(intern!(schema.py(), "schema_ref"))?;
        let validator_id = build_context.find_slot_id(&name)?;
        Ok(Self {
            validator_id,
            inner_name: "...".to_string(),
        }
        .into())
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
        guard_validate(self.validator_id, py, input, extra, slots, recursion_guard)
    }

    fn get_name(&self) -> &str {
        &self.inner_name
    }

    /// don't need to call complete on the inner validator here, complete_validators takes care of that.
    fn complete(&mut self, build_context: &BuildContext) -> PyResult<()> {
        let validator = build_context.find_validator(self.validator_id)?;
        self.inner_name = validator.get_name().to_string();
        Ok(())
    }
}

// see #143 this is a backup in case the identity check recursion guard fails
// if a single validator "depth" (how many times it's called inside itself) exceeds the limit,
// we raise a recursion error.
const BACKUP_GUARD_LIMIT: u16 = if cfg!(PyPy) || cfg!(target_family = "wasm") {
    123
} else {
    255
};

fn guard_validate<'s, 'data>(
    validator_id: usize,
    py: Python<'data>,
    input: &'data impl Input<'data>,
    extra: &Extra,
    slots: &'data [CombinedValidator],
    recursion_guard: &'s mut RecursionGuard,
) -> ValResult<'data, PyObject> {
    if let Some(id) = input.identity() {
        if recursion_guard.contains_or_insert(id) {
            // we don't remove id here, we leave that to the validator which originally added id to `recursion_guard`
            Err(ValError::new(ErrorKind::RecursionLoop, input))
        } else {
            if recursion_guard.incr_depth() > BACKUP_GUARD_LIMIT {
                return Err(ValError::new(ErrorKind::RecursionLoop, input));
            }
            let output = validate(validator_id, py, input, extra, slots, recursion_guard);
            recursion_guard.remove(&id);
            recursion_guard.decr_depth();
            output
        }
    } else {
        validate(validator_id, py, input, extra, slots, recursion_guard)
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
    let validator = unsafe { slots.get_unchecked(validator_id) };
    validator.validate(py, input, extra, slots, recursion_guard)
}
