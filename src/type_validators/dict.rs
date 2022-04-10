use pyo3::prelude::*;
use pyo3::types::PyDict;

use super::{SchemaValidator, TypeValidator};
use crate::errors::{
    ok_or_internal, single_val_error, ErrorKind, LocItem, Location, ValError, ValLineError, ValResult,
};
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

    fn validate(&self, py: Python, obj: &PyAny, loc: &Location) -> ValResult<PyObject> {
        let dict: &PyDict = match obj.cast_as() {
            Ok(d) => d,
            Err(_) => {
                // need to make this a better error
                return single_val_error!(py, obj);
            }
        };
        if let Some(min_length) = self.min_items {
            if dict.len() < min_length {
                return single_val_error!(
                    py,
                    dict,
                    kind = ErrorKind::DictTooShort,
                    context = Some(dict_create!(py, "min_length" => min_length))
                );
            }
        }
        if let Some(max_length) = self.max_items {
            if dict.len() > max_length {
                return single_val_error!(
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
            let get_key_loc = || -> ValResult<LocItem> {
                if let Ok(key_str) = key.extract::<String>() {
                    return Ok(LocItem::Key(key_str));
                }
                if let Ok(key_int) = key.extract::<usize>() {
                    return Ok(LocItem::Index(key_int));
                }
                // best effort is to use repr
                let repr_result = ok_or_internal!(key.repr())?;
                let repr: String = ok_or_internal!(repr_result.extract())?;
                Ok(LocItem::Key(repr))
            };
            // just call this for now, should be lazy in future
            let key_loc = get_key_loc()?;

            let output_key: Option<PyObject> = match self.key_validator {
                Some(ref validator) => {
                    let mut field_loc = loc.clone();
                    field_loc.push(key_loc.clone());
                    field_loc.push(LocItem::Key("[key]".to_string()));

                    match validator.validate(py, key, &field_loc) {
                        Ok(key) => Some(key),
                        Err(err) => {
                            if let ValError::LineErrors(errs) = err {
                                errors.extend(errs);
                                None
                            } else {
                                return Err(err);
                            }
                        }
                    }
                }
                None => Some(key.to_object(py)),
            };
            let output_value: Option<PyObject> = match self.value_validator {
                Some(ref validator) => {
                    let mut field_loc = loc.clone();
                    field_loc.push(key_loc);
                    match validator.validate(py, value, &field_loc) {
                        Ok(value) => Some(value),
                        Err(err) => {
                            if let ValError::LineErrors(errs) = err {
                                errors.extend(errs);
                                None
                            } else {
                                return Err(err);
                            }
                        }
                    }
                }
                None => Some(value.to_object(py)),
            };
            if let (Some(key), Some(value)) = (output_key, output_value) {
                ok_or_internal!(output.set_item(key, value))?;
            }
        }

        if errors.is_empty() {
            Ok(output.to_object(py))
        } else {
            Err(ValError::LineErrors(errors))
        }
    }

    fn clone_dyn(&self) -> Box<dyn TypeValidator> {
        Box::new(self.clone())
    }
}
