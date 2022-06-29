use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::{is_strict, SchemaDict};
use crate::errors::{context, err_val_error, ErrorKind};
use crate::input::{GenericSequence, Input};
use crate::recursion_guard::RecursionGuard;

use super::any::AnyValidator;
use super::{build_validator, BuildContext, BuildValidator, CombinedValidator, Extra, ValResult, Validator};

#[derive(Debug, Clone)]
pub struct ListValidator {
    strict: bool,
    item_validator: Box<CombinedValidator>,
    min_items: Option<usize>,
    max_items: Option<usize>,
}

macro_rules! sequence_build_function {
    () => {
        fn build(
            schema: &PyDict,
            config: Option<&PyDict>,
            build_context: &mut BuildContext,
        ) -> PyResult<CombinedValidator> {
            Ok(Self {
                strict: is_strict(schema, config)?,
                item_validator: match schema.get_item("items_schema") {
                    Some(d) => Box::new(build_validator(d, config, build_context)?.0),
                    None => Box::new(AnyValidator::build(schema, config, build_context)?),
                },
                min_items: schema.get_as("min_items")?,
                max_items: schema.get_as("max_items")?,
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
        let list = match self.strict {
            true => input.strict_list()?,
            false => input.lax_list()?,
        };
        self._validation_logic(py, input, list, extra, slots, recursion_guard)
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        self._validation_logic(py, input, input.strict_list()?, extra, slots, recursion_guard)
    }

    fn get_name(&self, py: Python) -> String {
        format!("{}[{}]", Self::EXPECTED_TYPE, self.item_validator.get_name(py))
    }
}

impl ListValidator {
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
                return err_val_error!(
                    input_value = input.as_error_value(),
                    kind = ErrorKind::TooShort,
                    context = context!("type" => "List", "min_length" => min_length)
                );
            }
        }
        if let Some(max_length) = self.max_items {
            if length > max_length {
                return err_val_error!(
                    input_value = input.as_error_value(),
                    kind = ErrorKind::TooLong,
                    context = context!("type" => "List", "max_length" => max_length)
                );
            }
        }

        let output = list.validate_to_vec(py, length, &self.item_validator, extra, slots, recursion_guard)?;
        Ok(output.into_py(py))
    }
}
