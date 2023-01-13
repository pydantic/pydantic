use pyo3::prelude::*;
use pyo3::types::{PyDict, PySet};

use crate::build_tools::SchemaDict;
use crate::errors::ValResult;
use crate::input::{GenericCollection, Input};
use crate::recursion_guard::RecursionGuard;

use super::list::{get_items_schema, length_check};
use super::{BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct SetValidator {
    strict: bool,
    item_validator: Option<Box<CombinedValidator>>,
    min_length: Option<usize>,
    max_length: Option<usize>,
    generator_max_length: Option<usize>,
    name: String,
}
pub static MAX_LENGTH_GEN_MULTIPLE: usize = 10;

macro_rules! set_build {
    () => {
        fn build(
            schema: &PyDict,
            config: Option<&PyDict>,
            build_context: &mut BuildContext<CombinedValidator>,
        ) -> PyResult<CombinedValidator> {
            let py = schema.py();
            let item_validator = get_items_schema(schema, config, build_context)?;
            let inner_name = item_validator.as_ref().map(|v| v.get_name()).unwrap_or("any");
            let max_length = schema.get_as(pyo3::intern!(py, "max_length"))?;
            let generator_max_length = match schema.get_as(pyo3::intern!(py, "generator_max_length"))? {
                Some(v) => Some(v),
                None => max_length.map(|v| v * super::set::MAX_LENGTH_GEN_MULTIPLE),
            };
            let name = format!("{}[{}]", Self::EXPECTED_TYPE, inner_name);
            Ok(Self {
                strict: crate::build_tools::is_strict(schema, config)?,
                item_validator,
                min_length: schema.get_as(pyo3::intern!(py, "min_length"))?,
                max_length,
                generator_max_length,
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

impl Validator for SetValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let seq = input.validate_set(extra.strict.unwrap_or(self.strict))?;

        let set = match self.item_validator {
            Some(ref v) => PySet::new(
                py,
                &seq.validate_to_vec(
                    py,
                    input,
                    self.max_length,
                    "Set",
                    self.generator_max_length,
                    v,
                    extra,
                    slots,
                    recursion_guard,
                )?,
            )?,
            None => match seq {
                GenericCollection::Set(set) => set,
                _ => PySet::new(py, &seq.to_vec(py, input, "Set", self.generator_max_length)?)?,
            },
        };
        length_check!(input, "Set", self.min_length, self.max_length, set);
        Ok(set.into_py(py))
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
