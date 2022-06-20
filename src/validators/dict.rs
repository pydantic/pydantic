use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::{is_strict, SchemaDict};
use crate::errors::{as_internal, context, err_val_error, ErrorKind, ValError, ValLineError, ValResult};
use crate::input::{GenericMapping, Input, JsonObject, ToLocItem};

use super::any::AnyValidator;
use super::{build_validator, BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct DictValidator {
    strict: bool,
    key_validator: Box<CombinedValidator>,
    value_validator: Box<CombinedValidator>,
    min_items: Option<usize>,
    max_items: Option<usize>,
    try_instance_as_dict: bool,
}

impl BuildValidator for DictValidator {
    const EXPECTED_TYPE: &'static str = "dict";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext,
    ) -> PyResult<CombinedValidator> {
        Ok(Self {
            strict: is_strict(schema, config)?,
            key_validator: match schema.get_item("keys") {
                Some(schema) => Box::new(build_validator(schema, config, build_context)?.0),
                None => Box::new(AnyValidator::build(schema, config, build_context)?),
            },
            value_validator: match schema.get_item("values") {
                Some(d) => Box::new(build_validator(d, config, build_context)?.0),
                None => Box::new(AnyValidator::build(schema, config, build_context)?),
            },
            min_items: schema.get_as("min_items")?,
            max_items: schema.get_as("max_items")?,
            try_instance_as_dict: schema.get_as("try_instance_as_dict")?.unwrap_or(false),
        }
        .into())
    }
}

impl Validator for DictValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        let dict = match self.strict {
            true => input.strict_dict()?,
            false => input.lax_dict(self.try_instance_as_dict)?,
        };
        self._validation_logic(py, input, dict, extra, slots)
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        self._validation_logic(py, input, input.strict_dict()?, extra, slots)
    }

    fn get_name(&self, _py: Python) -> String {
        Self::EXPECTED_TYPE.to_string()
    }
}

macro_rules! build_validate {
    ($name:ident, $dict_type:ty) => {
        fn $name<'s, 'data>(
            &'s self,
            py: Python<'data>,
            input: &'data impl Input<'data>,
            dict: &'data $dict_type,
            extra: &Extra,
            slots: &'data [CombinedValidator],
        ) -> ValResult<'data, PyObject> {
            if let Some(min_length) = self.min_items {
                if dict.len() < min_length {
                    return err_val_error!(
                        input_value = input.as_error_value(),
                        kind = ErrorKind::TooShort,
                        context = context!("type" => "Dict", "min_length" => min_length)
                    );
                }
            }
            if let Some(max_length) = self.max_items {
                if dict.len() > max_length {
                    return err_val_error!(
                        input_value = input.as_error_value(),
                        kind = ErrorKind::TooLong,
                        context = context!("type" => "Dict", "max_length" => max_length)
                    );
                }
            }
            let output = PyDict::new(py);
            let mut errors: Vec<ValLineError> = Vec::new();

            let key_validator = self.key_validator.as_ref();
            let value_validator = self.value_validator.as_ref();

            for (key, value) in dict.iter() {
                let output_key = match key_validator.validate(py, key, extra, slots) {
                    Ok(value) => Some(value),
                    Err(ValError::LineErrors(line_errors)) => {
                        let loc = vec![key.to_loc(), "[key]".to_loc()];
                        for err in line_errors {
                            errors.push(err.with_prefix_location(&loc));
                        }
                        None
                    }
                    Err(err) => return Err(err),
                };
                let output_value = match value_validator.validate(py, value, extra, slots) {
                    Ok(value) => Some(value),
                    Err(ValError::LineErrors(line_errors)) => {
                        let loc = vec![key.to_loc()];
                        for err in line_errors {
                            errors.push(err.with_prefix_location(&loc));
                        }
                        None
                    }
                    Err(err) => return Err(err),
                };
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
    };
}

impl DictValidator {
    build_validate!(validate_dict, PyDict);
    build_validate!(validate_json_object, JsonObject);

    fn _validation_logic<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        dict: GenericMapping<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        match dict {
            GenericMapping::PyDict(py_dict) => self.validate_dict(py, input, py_dict, extra, slots),
            GenericMapping::JsonObject(json_object) => self.validate_json_object(py, input, json_object, extra, slots),
        }
    }
}
