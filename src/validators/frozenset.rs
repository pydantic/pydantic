use pyo3::prelude::*;
use pyo3::types::{PyDict, PyFrozenSet};

use crate::errors::ValResult;
use crate::input::{validate_iter_to_set, BorrowInput, ConsumeIterator, Input, ValidatedSet};
use crate::tools::SchemaDict;

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
    fail_fast: bool,
}

impl BuildValidator for FrozenSetValidator {
    const EXPECTED_TYPE: &'static str = "frozenset";
    set_build!();
}

impl_py_gc_traverse!(FrozenSetValidator { item_validator });

impl Validator for FrozenSetValidator {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<PyObject> {
        let collection = input.validate_frozenset(state.strict_or(self.strict))?.unpack(state);
        let f_set = PyFrozenSet::empty_bound(py)?;
        collection.iterate(ValidateToFrozenSet {
            py,
            input,
            f_set: &f_set,
            max_length: self.max_length,
            item_validator: &self.item_validator,
            state,
            fail_fast: self.fail_fast,
        })??;
        min_length_check!(input, "Frozenset", self.min_length, f_set);
        Ok(f_set.into_py(py))
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}

struct ValidateToFrozenSet<'a, 's, 'py, I: Input<'py> + ?Sized> {
    py: Python<'py>,
    input: &'a I,
    f_set: &'a Bound<'py, PyFrozenSet>,
    max_length: Option<usize>,
    item_validator: &'a CombinedValidator,
    state: &'a mut ValidationState<'s, 'py>,
    fail_fast: bool,
}

impl<'py, T, I> ConsumeIterator<PyResult<T>> for ValidateToFrozenSet<'_, '_, 'py, I>
where
    T: BorrowInput<'py>,
    I: Input<'py> + ?Sized,
{
    type Output = ValResult<()>;
    fn consume_iterator(self, iterator: impl Iterator<Item = PyResult<T>>) -> ValResult<()> {
        validate_iter_to_set(
            self.py,
            self.f_set,
            iterator,
            self.input,
            "Frozenset",
            self.max_length,
            self.item_validator,
            self.state,
            self.fail_fast,
        )
    }
}
