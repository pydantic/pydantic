use pyo3::prelude::*;
use pyo3::types::PyDict;

use super::{build_validator, ValResult, Validator};
use crate::errors::{context, err_val_error, ErrorKind, LocItem, ValError, ValLineError};
use crate::standalone_validators::validate_list;
use crate::utils::dict_get;

#[derive(Debug, Clone)]
pub struct ListValidator {
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
            item_validator: match dict_get!(schema, "items", &PyDict) {
                Some(d) => Some(build_validator(d, config)?),
                None => None,
            },
            min_items: dict_get!(schema, "min_items", usize),
            max_items: dict_get!(schema, "max_items", usize),
        }))
    }

    fn validate(&self, py: Python, input: &PyAny, data: &PyDict) -> ValResult<PyObject> {
        let list = validate_list(py, input)?;
        if let Some(min_length) = self.min_items {
            if list.len() < min_length {
                return err_val_error!(
                    py,
                    list,
                    kind = ErrorKind::ListTooShort,
                    context = context!("min_length" => min_length)
                );
            }
        }
        if let Some(max_length) = self.max_items {
            if list.len() > max_length {
                return err_val_error!(
                    py,
                    list,
                    kind = ErrorKind::ListTooLong,
                    context = context!("max_length" => max_length)
                );
            }
        }
        let mut output: Vec<PyObject> = Vec::with_capacity(list.len());
        let mut errors: Vec<ValLineError> = Vec::new();
        for (index, item) in list.iter().enumerate() {
            match self.item_validator {
                Some(ref validator) => match validator.validate(py, item, data) {
                    Ok(item) => output.push(item),
                    Err(ValError::LineErrors(line_errors)) => {
                        let loc = vec![LocItem::I(index)];
                        for err in line_errors {
                            errors.push(err.prefix_location(&loc));
                        }
                    }
                    Err(err) => return Err(err),
                },
                None => output.push(item.into_py(py)),
            }
        }

        if errors.is_empty() {
            Ok(output.into_py(py))
        } else {
            Err(ValError::LineErrors(errors))
        }
    }

    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}
