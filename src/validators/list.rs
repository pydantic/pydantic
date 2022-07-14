use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::SchemaDict;
use crate::errors::{ErrorKind, ValError, ValResult};
use crate::input::Input;
use crate::recursion_guard::RecursionGuard;

use super::any::AnyValidator;
use super::{build_validator, BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct ListValidator {
    strict: bool,
    item_validator: Box<CombinedValidator>,
    min_items: Option<usize>,
    max_items: Option<usize>,
    name: String,
}

macro_rules! sequence_build_function {
    () => {
        fn build(
            schema: &PyDict,
            config: Option<&PyDict>,
            build_context: &mut BuildContext,
        ) -> PyResult<CombinedValidator> {
            let item_validator = match schema.get_item("items_schema") {
                Some(d) => Box::new(build_validator(d, config, build_context)?.0),
                None => Box::new(AnyValidator::build(schema, config, build_context)?),
            };
            let name = format!("{}[{}]", Self::EXPECTED_TYPE, item_validator.get_name());
            Ok(Self {
                strict: crate::build_tools::is_strict(schema, config)?,
                item_validator,
                min_items: schema.get_as("min_items")?,
                max_items: schema.get_as("max_items")?,
                name,
            }
            .into())
        }
    };
}
pub(crate) use sequence_build_function;

impl BuildValidator for ListValidator {
    const EXPECTED_TYPE: &'static str = "list";
    sequence_build_function!();
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
        let length = seq.generic_len();
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

        let output = seq.validate_to_vec(py, length, &self.item_validator, extra, slots, recursion_guard)?;
        Ok(output.into_py(py))
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, build_context: &BuildContext) -> PyResult<()> {
        self.item_validator.complete(build_context)
    }
}
