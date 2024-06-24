use pyo3::prelude::*;
use pyo3::types::{PyDict, PySet};

use crate::errors::ValResult;
use crate::input::{validate_iter_to_set, BorrowInput, ConsumeIterator, Input, ValidatedSet};
use crate::tools::SchemaDict;

use super::list::min_length_check;
use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

#[derive(Debug)]
pub struct SetValidator {
    strict: bool,
    item_validator: Box<CombinedValidator>,
    min_length: Option<usize>,
    max_length: Option<usize>,
    name: String,
    fail_fast: bool,
}

macro_rules! set_build {
    () => {
        fn build(
            schema: &Bound<'_, PyDict>,
            config: Option<&Bound<'_, PyDict>>,
            definitions: &mut DefinitionsBuilder<CombinedValidator>,
        ) -> PyResult<CombinedValidator> {
            let py = schema.py();
            let item_validator = match schema.get_item(pyo3::intern!(schema.py(), "items_schema"))? {
                Some(d) => Box::new(crate::validators::build_validator(&d, config, definitions)?),
                None => Box::new(crate::validators::any::AnyValidator::build(
                    schema,
                    config,
                    definitions,
                )?),
            };
            let inner_name = item_validator.get_name();
            let max_length = schema.get_as(pyo3::intern!(py, "max_length"))?;
            let name = format!("{}[{}]", Self::EXPECTED_TYPE, inner_name);
            Ok(Self {
                strict: crate::build_tools::is_strict(schema, config)?,
                item_validator,
                min_length: schema.get_as(pyo3::intern!(py, "min_length"))?,
                max_length,
                name,
                fail_fast: schema.get_as(pyo3::intern!(py, "fail_fast"))?.unwrap_or(false),
            }
            .into())
        }
    };
}
pub(crate) use set_build;

impl BuildValidator for SetValidator {
    const EXPECTED_TYPE: &'static str = "set";
    set_build!();
}

impl_py_gc_traverse!(SetValidator { item_validator });

impl Validator for SetValidator {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<PyObject> {
        let collection = input.validate_set(state.strict_or(self.strict))?.unpack(state);
        let set = PySet::empty_bound(py)?;
        collection.iterate(ValidateToSet {
            py,
            input,
            set: &set,
            max_length: self.max_length,
            item_validator: &self.item_validator,
            state,
            fail_fast: self.fail_fast,
        })??;
        min_length_check!(input, "Set", self.min_length, set);
        Ok(set.into_py(py))
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}

struct ValidateToSet<'a, 's, 'py, I: Input<'py> + ?Sized> {
    py: Python<'py>,
    input: &'a I,
    set: &'a Bound<'py, PySet>,
    max_length: Option<usize>,
    item_validator: &'a CombinedValidator,
    state: &'a mut ValidationState<'s, 'py>,
    fail_fast: bool,
}

impl<'py, T, I> ConsumeIterator<PyResult<T>> for ValidateToSet<'_, '_, 'py, I>
where
    T: BorrowInput<'py>,
    I: Input<'py> + ?Sized,
{
    type Output = ValResult<()>;
    fn consume_iterator(self, iterator: impl Iterator<Item = PyResult<T>>) -> ValResult<()> {
        validate_iter_to_set(
            self.py,
            self.set,
            iterator,
            self.input,
            "Set",
            self.max_length,
            self.item_validator,
            self.state,
            self.fail_fast,
        )
    }
}
