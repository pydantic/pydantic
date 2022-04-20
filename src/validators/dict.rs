use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_macros::dict_get;
use crate::errors::{as_internal, context, err_val_error, ErrorKind, ValError, ValLineError, ValResult};
use crate::input::{Input, ToLocItem};

use super::{build_validator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct DictValidator {
    key_validator: Option<Box<dyn Validator>>,
    value_validator: Option<Box<dyn Validator>>,
    min_items: Option<usize>,
    max_items: Option<usize>,
}

impl DictValidator {
    pub const EXPECTED_TYPE: &'static str = "dict";
}

impl Validator for DictValidator {
    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        Ok(Box::new(Self {
            key_validator: match dict_get!(schema, "keys", &PyDict) {
                Some(d) => Some(build_validator(d, config)?),
                None => None,
            },
            value_validator: match dict_get!(schema, "values", &PyDict) {
                Some(d) => Some(build_validator(d, config)?),
                None => None,
            },
            min_items: dict_get!(schema, "min_items", usize),
            max_items: dict_get!(schema, "max_items", usize),
        }))
    }

    fn validate(&self, py: Python, input: &dyn Input, extra: &Extra) -> ValResult<PyObject> {
        let dict = input.validate_dict(py)?;
        if let Some(min_length) = self.min_items {
            if dict.input_len() < min_length {
                return err_val_error!(
                    py,
                    dict,
                    kind = ErrorKind::DictTooShort,
                    context = context!("min_length" => min_length)
                );
            }
        }
        if let Some(max_length) = self.max_items {
            if dict.input_len() > max_length {
                return err_val_error!(
                    py,
                    dict,
                    kind = ErrorKind::DictTooLong,
                    context = context!("max_length" => max_length)
                );
            }
        }
        let output = PyDict::new(py);
        let mut errors: Vec<ValLineError> = Vec::new();

        for (key, value) in dict.input_iter() {
            let output_key: Option<PyObject> =
                apply_validator(py, &self.key_validator, &mut errors, key, key, extra, true)?;
            let output_value: Option<PyObject> =
                apply_validator(py, &self.value_validator, &mut errors, value, key, extra, false)?;
            if let (Some(key), Some(value)) = (output_key, output_value) {
                output.set_item(key, value).map_err(as_internal)?;
            }
        }

        if errors.is_empty() {
            Ok(output.into())
        } else {
            Err(ValError::LineErrors(errors))
        }
    }

    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}

fn apply_validator(
    py: Python,
    validator: &Option<Box<dyn Validator>>,
    errors: &mut Vec<ValLineError>,
    input: &dyn Input,
    key: &dyn Input,
    extra: &Extra,
    key_loc: bool,
) -> ValResult<Option<PyObject>> {
    match validator {
        Some(validator) => match validator.validate(py, input, extra) {
            Ok(value) => Ok(Some(value)),
            Err(ValError::LineErrors(line_errors)) => {
                let loc = if key_loc {
                    vec![key.to_loc()?, "[key]".to_loc()?]
                } else {
                    vec![key.to_loc()?]
                };
                for err in line_errors {
                    errors.push(err.prefix_location(&loc));
                }
                Ok(None)
            }
            Err(err) => Err(err),
        },
        None => Ok(Some(input.to_py(py))),
    }
}
