use pyo3::prelude::*;
use pyo3::types::{PyDict, PyFrozenSet};

use crate::build_tools::{is_strict, SchemaDict};
use crate::errors::{as_internal, ErrorKind, ValError, ValResult};
use crate::input::{GenericSequence, Input};
use crate::recursion_guard::RecursionGuard;

use super::any::AnyValidator;
use super::list::sequence_build_function;
use super::{build_validator, BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct FrozenSetValidator {
    strict: bool,
    item_validator: Box<CombinedValidator>,
    min_items: Option<usize>,
    max_items: Option<usize>,
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
        let frozenset = match self.strict {
            true => input.strict_frozenset()?,
            false => input.lax_frozenset()?,
        };
        self._validation_logic(py, input, frozenset, extra, slots, recursion_guard)
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        self._validation_logic(py, input, input.strict_frozenset()?, extra, slots, recursion_guard)
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, build_context: &BuildContext) -> PyResult<()> {
        self.item_validator.complete(build_context)
    }
}

impl FrozenSetValidator {
    fn _validation_logic<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        list: GenericSequence<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let length = list.generic_len();
        if let Some(min_length) = self.min_items {
            if length < min_length {
                return Err(ValError::new(ErrorKind::TooShort { min_length }, input));
            }
        }
        if let Some(max_length) = self.max_items {
            if length > max_length {
                return Err(ValError::new(ErrorKind::TooLong { max_length }, input));
            }
        }

        let output = list.validate_to_vec(py, length, &self.item_validator, extra, slots, recursion_guard)?;
        Ok(PyFrozenSet::new(py, &output).map_err(as_internal)?.into_py(py))
    }
}
