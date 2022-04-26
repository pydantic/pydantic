use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::{is_strict, SchemaDict};
use crate::errors::{context, err_val_error, ErrorKind, InputValue, LocItem, ValError, ValLineError};
use crate::input::{Input, ListInput};

use super::{build_validator, Extra, ValResult, Validator, ValidatorArc};

#[derive(Debug, Clone)]
pub struct ListValidator {
    strict: bool,
    item_validator: Option<Box<dyn Validator>>,
    min_items: Option<usize>,
    max_items: Option<usize>,
}

impl ListValidator {
    pub const EXPECTED_TYPE: &'static str = "list";
}

impl Validator for ListValidator {
    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        Ok(Box::new(Self {
            strict: is_strict(schema, config)?,
            item_validator: match schema.get_item("items") {
                Some(d) => Some(build_validator(d, config)?.0),
                None => None,
            },
            min_items: schema.get_as("min_items")?,
            max_items: schema.get_as("max_items")?,
        }))
    }

    fn set_ref(&mut self, name: &str, validator_arc: &ValidatorArc) -> PyResult<()> {
        match self.item_validator {
            Some(ref mut item_validator) => item_validator.set_ref(name, validator_arc),
            None => Ok(()),
        }
    }

    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        let list = match self.strict {
            true => input.strict_list(py)?,
            false => input.lax_list(py)?,
        };
        self._validation_logic(py, input, list, extra)
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        self._validation_logic(py, input, input.strict_list(py)?, extra)
    }

    fn get_name(&self, py: Python) -> String {
        match &self.item_validator {
            Some(v) => format!("{}-{}", Self::EXPECTED_TYPE, v.get_name(py)),
            None => Self::EXPECTED_TYPE.to_string(),
        }
    }

    #[no_coverage]
    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}

impl ListValidator {
    fn _validation_logic<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        list: Box<dyn ListInput<'data> + 'data>,
        extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        let length = list.input_len();
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
        let mut output: Vec<PyObject> = Vec::with_capacity(length);
        let mut errors: Vec<ValLineError> = Vec::new();
        for (index, item) in list.input_iter().enumerate() {
            match self.item_validator {
                Some(ref validator) => match validator.validate(py, item, extra) {
                    Ok(item) => output.push(item),
                    Err(ValError::LineErrors(line_errors)) => {
                        let loc = vec![LocItem::I(index)];
                        for err in line_errors {
                            errors.push(err.with_prefix_location(&loc));
                        }
                    }
                    Err(err) => return Err(err),
                },
                None => output.push(item.to_py(py)),
            }
        }

        if errors.is_empty() {
            Ok(output.into_py(py))
        } else {
            Err(ValError::LineErrors(errors))
        }
    }
}
