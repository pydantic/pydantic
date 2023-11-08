use pyo3::prelude::*;
use pyo3::types::{PyDict, PySet};

use crate::errors::ValResult;
use crate::input::{GenericIterable, Input};
use crate::tools::SchemaDict;
use crate::validators::Exactness;

use super::list::min_length_check;
use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

#[derive(Debug)]
pub struct SetValidator {
    strict: bool,
    item_validator: Box<CombinedValidator>,
    min_length: Option<usize>,
    max_length: Option<usize>,
    name: String,
}

macro_rules! set_build {
    () => {
        fn build(
            schema: &PyDict,
            config: Option<&PyDict>,
            definitions: &mut DefinitionsBuilder<CombinedValidator>,
        ) -> PyResult<CombinedValidator> {
            let py = schema.py();
            let item_validator = match schema.get_item(pyo3::intern!(schema.py(), "items_schema"))? {
                Some(d) => Box::new(crate::validators::build_validator(d, config, definitions)?),
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
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        let collection = input.validate_set(state.strict_or(self.strict))?;
        let exactness = match &collection {
            GenericIterable::Set(_) => Exactness::Exact,
            GenericIterable::FrozenSet(_) | GenericIterable::JsonArray(_) => Exactness::Strict,
            _ => Exactness::Lax,
        };
        state.floor_exactness(exactness);
        let set = PySet::empty(py)?;
        collection.validate_to_set(py, set, input, self.max_length, "Set", &self.item_validator, state)?;
        min_length_check!(input, "Set", self.min_length, set);
        Ok(set.into_py(py))
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}
