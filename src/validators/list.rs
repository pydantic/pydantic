use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::SchemaDict;
use crate::errors::ValResult;
use crate::input::{GenericListLike, Input};
use crate::recursion_guard::RecursionGuard;

use super::{build_validator, BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct ListValidator {
    strict: bool,
    item_validator: Option<Box<CombinedValidator>>,
    size_range: Option<(Option<usize>, Option<usize>)>,
    name: String,
}

macro_rules! generic_list_like_build {
    () => {
        super::list::generic_list_like_build!("{}[{}]", Self::EXPECTED_TYPE);
    };
    ($name_template:literal, $name:expr) => {
        fn build(
            schema: &PyDict,
            config: Option<&PyDict>,
            build_context: &mut BuildContext,
        ) -> PyResult<CombinedValidator> {
            let py = schema.py();
            let item_validator = match schema.get_item(pyo3::intern!(py, "items_schema")) {
                Some(d) => Some(Box::new(build_validator(d, config, build_context)?)),
                None => None,
            };
            let inner_name = item_validator.as_ref().map(|v| v.get_name()).unwrap_or("any");
            let name = format!($name_template, $name, inner_name);
            let min_items = schema.get_as(pyo3::intern!(py, "min_items"))?;
            let max_items = schema.get_as(pyo3::intern!(py, "max_items"))?;
            Ok(Self {
                strict: crate::build_tools::is_strict(schema, config)?,
                item_validator,
                size_range: match min_items.is_some() || max_items.is_some() {
                    true => Some((min_items, max_items)),
                    false => None,
                },
                name,
            }
            .into())
        }
    };
}
pub(crate) use generic_list_like_build;

impl BuildValidator for ListValidator {
    const EXPECTED_TYPE: &'static str = "list";
    generic_list_like_build!();
}

impl Validator for ListValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let seq = input.validate_list(extra.strict.unwrap_or(self.strict))?;

        let length = seq.check_len(self.size_range, input)?;

        let output = match self.item_validator {
            Some(ref v) => seq.validate_to_vec(py, length, v, extra, slots, recursion_guard)?,
            None => match seq {
                GenericListLike::List(list) => return Ok(list.into_py(py)),
                _ => seq.to_vec(py),
            },
        };
        Ok(output.into_py(py))
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
