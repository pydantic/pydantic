use pyo3::prelude::*;
use pyo3::types::{PyDict, PyFrozenSet};

use crate::build_tools::SchemaDict;
use crate::errors::ValResult;
use crate::input::Input;
use crate::recursion_guard::RecursionGuard;

use super::list::sequence_build_function;
use super::{build_validator, BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct FrozenSetValidator {
    strict: bool,
    item_validator: Option<Box<CombinedValidator>>,
    size_range: Option<(Option<usize>, Option<usize>)>,
    name: String,
}

impl BuildValidator for FrozenSetValidator {
    const EXPECTED_TYPE: &'static str = "frozenset";
    sequence_build_function!();
}

impl Validator for FrozenSetValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let seq = input.validate_frozenset(extra.strict.unwrap_or(self.strict))?;

        let length = seq.check_len(self.size_range, input)?;

        let output = match self.item_validator {
            Some(ref v) => seq.validate_to_vec(py, length, v, extra, slots, recursion_guard)?,
            None => seq.to_vec(py),
        };
        Ok(PyFrozenSet::new(py, &output)?.into_py(py))
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, build_context: &BuildContext) -> PyResult<()> {
        match self.item_validator {
            Some(ref mut v) => v.complete(build_context),
            None => Ok(()),
        }
    }
}
