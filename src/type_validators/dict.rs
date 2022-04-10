use pyo3::prelude::*;
use pyo3::types::PyDict;

use super::{SchemaValidator, TypeValidator};
use crate::errors::{err_val_error, ok_or_internal, ErrorKind, LocItem, ValError, ValLineError, ValResult};
use crate::standalone_validators::validate_dict;
use crate::utils::{dict_create, dict_get};

#[derive(Debug, Clone)]
pub struct DictValidator {
    key_validator: Option<Box<SchemaValidator>>,
    value_validator: Option<Box<SchemaValidator>>,
    min_items: Option<usize>,
    max_items: Option<usize>,
}

impl TypeValidator for DictValidator {
    fn is_match(type_: &str, _dict: &PyDict) -> bool {
        type_ == "dict"
    }

    fn build(dict: &PyDict) -> PyResult<Self> {
        Ok(Self {
            key_validator: match dict_get!(dict, "keys", &PyDict) {
                Some(d) => Some(Box::new(SchemaValidator::build(d)?)),
                None => None,
            },
            value_validator: match dict_get!(dict, "values", &PyDict) {
                Some(d) => Some(Box::new(SchemaValidator::build(d)?)),
                None => None,
            },
            min_items: dict_get!(dict, "min_items", usize),
            max_items: dict_get!(dict, "max_items", usize),
        })
    }

    fn validate(&self, py: Python, obj: &PyAny) -> ValResult<PyObject> {
        let dict: &PyDict = validate_dict(py, obj)?;
        if let Some(min_length) = self.min_items {
            if dict.len() < min_length {
                return err_val_error!(
                    py,
                    dict,
                    kind = ErrorKind::DictTooShort,
                    context = Some(dict_create!(py, "min_length" => min_length))
                );
            }
        }
        if let Some(max_length) = self.max_items {
            if dict.len() > max_length {
                return err_val_error!(
                    py,
                    dict,
                    kind = ErrorKind::DictTooLong,
                    context = Some(dict_create!(py, "max_length" => max_length))
                );
            }
        }
        let output = PyDict::new(py);
        let mut errors: Vec<ValLineError> = Vec::new();

        for (key, value) in dict.iter() {
            let output_key: Option<PyObject> = apply_validator(py, &self.key_validator, &mut errors, key, key, true)?;
            let output_value: Option<PyObject> =
                apply_validator(py, &self.value_validator, &mut errors, value, key, false)?;
            if let (Some(key), Some(value)) = (output_key, output_value) {
                ok_or_internal!(output.set_item(key, value))?;
            }
        }

        if errors.is_empty() {
            Ok(output.into())
        } else {
            Err(ValError::LineErrors(errors))
        }
    }

    fn clone_dyn(&self) -> Box<dyn TypeValidator> {
        Box::new(self.clone())
    }
}

fn apply_validator(
    py: Python,
    validator: &Option<Box<SchemaValidator>>,
    errors: &mut Vec<ValLineError>,
    val_value: &PyAny,
    key: &PyAny,
    key_loc: bool,
) -> ValResult<Option<PyObject>> {
    match validator {
        Some(validator) => match validator.validate(py, val_value) {
            Ok(value) => Ok(Some(value)),
            Err(ValError::LineErrors(line_errors)) => {
                let loc = if key_loc {
                    vec![get_loc(key)?, LocItem::S("[key]".to_string())]
                } else {
                    vec![get_loc(key)?]
                };
                for err in line_errors {
                    errors.push(err.with_location(&loc));
                }
                Ok(None)
            }
            Err(err) => Err(err),
        },
        None => Ok(Some(val_value.to_object(py))),
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
    let repr_result = ok_or_internal!(key.repr())?;
    let repr: String = ok_or_internal!(repr_result.extract())?;
    Ok(LocItem::S(repr))
}
