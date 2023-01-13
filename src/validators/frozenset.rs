use pyo3::prelude::*;
use pyo3::types::{PyDict, PyFrozenSet};

use crate::build_tools::SchemaDict;
use crate::errors::ValResult;
use crate::input::{GenericCollection, Input};
use crate::recursion_guard::RecursionGuard;

use super::list::{get_items_schema, length_check};
use super::set::set_build;
use super::{BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct FrozenSetValidator {
    strict: bool,
    item_validator: Option<Box<CombinedValidator>>,
    min_length: Option<usize>,
    max_length: Option<usize>,
    generator_max_length: Option<usize>,
    name: String,
}

impl BuildValidator for FrozenSetValidator {
    const EXPECTED_TYPE: &'static str = "frozenset";
    set_build!();
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

        let f_set = match self.item_validator {
            Some(ref v) => PyFrozenSet::new(
                py,
                &seq.validate_to_vec(
                    py,
                    input,
                    self.max_length,
                    "Frozenset",
                    self.generator_max_length,
                    v,
                    extra,
                    slots,
                    recursion_guard,
                )?,
            )?,
            None => match seq {
                GenericCollection::FrozenSet(f_set) => f_set,
                _ => PyFrozenSet::new(py, &seq.to_vec(py, input, "Frozenset", self.generator_max_length)?)?,
            },
        };
        length_check!(input, "Frozenset", self.min_length, self.max_length, f_set);
        Ok(f_set.into_py(py))
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, build_context: &BuildContext<CombinedValidator>) -> PyResult<()> {
        match self.item_validator {
            Some(ref mut v) => v.complete(build_context),
            None => Ok(()),
        }
    }
}
