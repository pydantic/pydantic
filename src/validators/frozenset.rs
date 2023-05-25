use pyo3::prelude::*;
use pyo3::types::{PyDict, PyFrozenSet};

use crate::errors::ValResult;
use crate::input::Input;
use crate::recursion_guard::RecursionGuard;
use crate::tools::SchemaDict;

use super::list::min_length_check;
use super::set::set_build;
use super::{BuildValidator, CombinedValidator, Definitions, DefinitionsBuilder, Extra, Validator};

#[derive(Debug, Clone)]
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

impl Validator for FrozenSetValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        definitions: &'data Definitions<CombinedValidator>,
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let collection = input.validate_frozenset(extra.strict.unwrap_or(self.strict))?;
        let f_set = PyFrozenSet::empty(py)?;
        collection.validate_to_set(
            py,
            f_set,
            input,
            self.max_length,
            "Frozenset",
            &self.item_validator,
            extra,
            definitions,
            recursion_guard,
        )?;
        min_length_check!(input, "Frozenset", self.min_length, f_set);
        Ok(f_set.into_py(py))
    }

    fn different_strict_behavior(
        &self,
        definitions: Option<&DefinitionsBuilder<CombinedValidator>>,
        ultra_strict: bool,
    ) -> bool {
        if ultra_strict {
            self.item_validator.different_strict_behavior(definitions, true)
        } else {
            true
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, definitions: &DefinitionsBuilder<CombinedValidator>) -> PyResult<()> {
        self.item_validator.complete(definitions)
    }
}
