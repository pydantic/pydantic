use pyo3::prelude::*;
use pyo3::types::{PyDict, PyFrozenSet};

use crate::errors::ValResult;
use crate::input::{GenericIterable, Input};
use crate::tools::SchemaDict;
use crate::validators::Exactness;

use super::list::min_length_check;
use super::set::set_build;
use super::validation_state::ValidationState;
use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, Validator};

#[derive(Debug)]
pub struct FrozenSetValidator {
    strict: bool,
    item_validator: Box<CombinedValidator>,
    min_length: Option<usize>,
    max_length: Option<usize>,
    name: String,
}

impl BuildValidator for FrozenSetValidator {
    const EXPECTED_TYPE: &'static str = "frozenset";
    set_build!();
}

impl_py_gc_traverse!(FrozenSetValidator { item_validator });

impl Validator for FrozenSetValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<PyObject> {
        let collection = input.validate_frozenset(state.strict_or(self.strict))?;
        let exactness = match &collection {
            GenericIterable::FrozenSet(_) => Exactness::Exact,
            GenericIterable::Set(_) | GenericIterable::JsonArray(_) => Exactness::Strict,
            _ => Exactness::Lax,
        };
        state.floor_exactness(exactness);
        let f_set = PyFrozenSet::empty_bound(py)?;
        collection.validate_to_set(
            py,
            &f_set,
            input,
            self.max_length,
            "Frozenset",
            &self.item_validator,
            state,
        )?;
        min_length_check!(input, "Frozenset", self.min_length, f_set);
        Ok(f_set.into_py(py))
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}
