use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use crate::build_tools::{is_strict, SchemaDict};
use crate::errors::{context, err_val_error, ErrorKind, InputValue, LocItem, ValError, ValLineError};
use crate::input::{GenericSequence, Input, SequenceLenIter};

use super::{build_validator, BuildContext, BuildValidator, CombinedValidator, Extra, ValResult, Validator};

#[derive(Debug, Clone)]
pub struct ListValidator {
    strict: bool,
    item_validator: Option<Box<CombinedValidator>>,
    min_items: Option<usize>,
    max_items: Option<usize>,
}

impl BuildValidator for ListValidator {
    const EXPECTED_TYPE: &'static str = "list";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext,
    ) -> PyResult<CombinedValidator> {
        Ok(Self {
            strict: is_strict(schema, config)?,
            item_validator: match schema.get_item("items") {
                Some(d) => Some(Box::new(build_validator(d, config, build_context)?.0)),
                None => None,
            },
            min_items: schema.get_as("min_items")?,
            max_items: schema.get_as("max_items")?,
        }
        .into())
    }
}

impl Validator for ListValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
        slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        let list = match self.strict {
            true => input.strict_list()?,
            false => input.lax_list()?,
        };
        self._validation_logic(py, input, list, extra, slots)
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
        slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        self._validation_logic(py, input, input.strict_list()?, extra, slots)
    }

    fn get_name(&self, py: Python) -> String {
        match &self.item_validator {
            Some(v) => format!("{}-{}", Self::EXPECTED_TYPE, v.get_name(py)),
            None => Self::EXPECTED_TYPE.to_string(),
        }
    }
}

impl ListValidator {
    fn _validation_logic<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        list: GenericSequence<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        let length = list.generic_len();
        if let Some(min_length) = self.min_items {
            if length < min_length {
                return err_val_error!(
                    input_value = InputValue::InputRef(input),
                    kind = ErrorKind::ListTooShort,
                    context = context!("min_length" => min_length)
                );
            }
        }
        if let Some(max_length) = self.max_items {
            if length > max_length {
                return err_val_error!(
                    input_value = InputValue::InputRef(input),
                    kind = ErrorKind::ListTooLong,
                    context = context!("max_length" => max_length)
                );
            }
        }

        match self.item_validator {
            Some(ref validator) => {
                let mut output: Vec<PyObject> = Vec::with_capacity(length);
                let mut errors: Vec<ValLineError> = Vec::new();
                for (index, item) in list.generic_iter() {
                    match validator.validate(py, item, extra, slots) {
                        Ok(item) => output.push(item),
                        Err(ValError::LineErrors(line_errors)) => {
                            let loc = vec![LocItem::I(index)];
                            errors.extend(line_errors.into_iter().map(|err| err.with_prefix_location(&loc)));
                        }
                        Err(err) => return Err(err),
                    }
                }
                if errors.is_empty() {
                    Ok(output.into_py(py))
                } else {
                    Err(ValError::LineErrors(errors))
                }
            }
            None => {
                let output: Vec<PyObject> = list.generic_iter().map(|(_, item)| item.to_py(py)).collect();
                Ok(PyList::new(py, &output).into_py(py))
            }
        }
    }
}
