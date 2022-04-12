use pyo3::prelude::*;
use pyo3::types::PyDict;

use super::{build_validator, Validator};
use crate::errors::{as_internal, context, err_val_error, ErrorKind, LocItem, ValError, ValLineError, ValResult};
use crate::standalone_validators::validate_dict;
use crate::utils::dict_get;

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
    fn build(dict: &PyDict, config: Option<&PyDict>) -> PyResult<Self> {
        Ok(Self {
            key_validator: match dict_get!(dict, "keys", &PyDict) {
                Some(d) => Some(build_validator(d, config)?),
                None => None,
            },
            value_validator: match dict_get!(dict, "values", &PyDict) {
                Some(d) => Some(build_validator(d, config)?),
                None => None,
            },
            min_items: dict_get!(dict, "min_items", usize),
            max_items: dict_get!(dict, "max_items", usize),
        })
    }

    fn validate(&self, py: Python, input: &PyAny, data: &PyDict) -> ValResult<PyObject> {
        let dict = validate_dict(py, input)?;
        if let Some(min_length) = self.min_items {
            if dict.len() < min_length {
                return err_val_error!(
                    py,
                    dict,
                    kind = ErrorKind::DictTooShort,
                    context = context!("min_length" => min_length)
                );
            }
        }
        if let Some(max_length) = self.max_items {
            if dict.len() > max_length {
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

        for (key, value) in dict.iter() {
            let output_key: Option<PyObject> =
                apply_validator(py, &self.key_validator, &mut errors, key, key, data, true)?;
            let output_value: Option<PyObject> =
                apply_validator(py, &self.value_validator, &mut errors, value, key, data, false)?;
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
    input: &PyAny,
    key: &PyAny,
    data: &PyDict,
    key_loc: bool,
) -> ValResult<Option<PyObject>> {
    match validator {
        Some(validator) => match validator.validate(py, input, data) {
            Ok(value) => Ok(Some(value)),
            Err(ValError::LineErrors(line_errors)) => {
                let loc = if key_loc {
                    vec![get_loc(key)?, LocItem::S("[key]".to_string())]
                } else {
                    vec![get_loc(key)?]
                };
                for err in line_errors {
                    errors.push(err.prefix_location(&loc));
                }
                Ok(None)
            }
            Err(err) => Err(err),
        },
        None => Ok(Some(input.into_py(py))),
    }
}

fn get_loc(key: &PyAny) -> ValResult<LocItem> {
    if let Ok(key_str) = key.extract::<String>() {
        return Ok(LocItem::S(key_str));
    }
    if let Ok(key_int) = key.extract::<usize>() {
        return Ok(LocItem::I(key_int));
    }
    // best effort is to use repr
    let repr_result = key.repr().map_err(as_internal)?;
    let repr: String = repr_result.extract().map_err(as_internal)?;
    Ok(LocItem::S(repr))
}
