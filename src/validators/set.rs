use pyo3::prelude::*;
use pyo3::types::{PyDict, PySet};

use crate::build_tools::{is_strict, SchemaDict};
use crate::errors::{as_internal, context, err_val_error, ErrorKind, InputValue, LocItem, ValError, ValLineError};
use crate::input::{Input, ListInput};

use super::{build_validator, BuildValidator, CombinedValidator, Extra, SlotsBuilder, ValResult, Validator};

#[derive(Debug, Clone)]
pub struct SetValidator {
    strict: bool,
    item_validator: Option<Box<CombinedValidator>>,
    min_items: Option<usize>,
    max_items: Option<usize>,
}

impl BuildValidator for SetValidator {
    const EXPECTED_TYPE: &'static str = "set";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        slots_builder: &mut SlotsBuilder,
    ) -> PyResult<CombinedValidator> {
        Ok(Self {
            strict: is_strict(schema, config)?,
            item_validator: match schema.get_item("items") {
                Some(d) => Some(Box::new(build_validator(d, config, slots_builder)?.0)),
                None => None,
            },
            min_items: schema.get_as("min_items")?,
            max_items: schema.get_as("max_items")?,
        }
        .into())
    }
}

impl Validator for SetValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
        slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        let set = match self.strict {
            true => input.strict_set()?,
            false => input.lax_set()?,
        };
        self._validation_logic(py, input, set, extra, slots)
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
        slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        self._validation_logic(py, input, input.strict_set()?, extra, slots)
    }

    fn get_name(&self, py: Python) -> String {
        match &self.item_validator {
            Some(v) => format!("{}-{}", Self::EXPECTED_TYPE, v.get_name(py)),
            None => Self::EXPECTED_TYPE.to_string(),
        }
    }
}

impl SetValidator {
    fn _validation_logic<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        set: Box<dyn ListInput<'data> + 'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        let length = set.input_len();
        if let Some(min_length) = self.min_items {
            if length < min_length {
                return err_val_error!(
                    input_value = InputValue::InputRef(input),
                    kind = ErrorKind::SetTooShort,
                    context = context!("min_length" => min_length)
                );
            }
        }
        if let Some(max_length) = self.max_items {
            if length > max_length {
                return err_val_error!(
                    input_value = InputValue::InputRef(input),
                    kind = ErrorKind::SetTooLong,
                    context = context!("max_length" => max_length)
                );
            }
        }

        match self.item_validator {
            Some(ref validator) => {
                let mut errors: Vec<ValLineError> = Vec::new();
                let mut output: Vec<PyObject> = Vec::with_capacity(length);
                for (index, item) in set.input_iter().enumerate() {
                    match validator.validate(py, item, extra, slots) {
                        Ok(item) => output.push(item),
                        Err(ValError::LineErrors(line_errors)) => {
                            let loc = vec![LocItem::I(index)];
                            errors.extend(line_errors.into_iter().map(|err| err.with_prefix_location(&loc)));
                        }
                        Err(err) => return Err(err),
                    };
                }
                if errors.is_empty() {
                    Ok(PySet::new(py, &output).map_err(as_internal)?.into_py(py))
                } else {
                    Err(ValError::LineErrors(errors))
                }
            }
            None => {
                let output: Vec<PyObject> = set.input_iter().map(|item| item.to_py(py)).collect();
                Ok(PySet::new(py, &output).map_err(as_internal)?.into_py(py))
            }
        }
    }
}
