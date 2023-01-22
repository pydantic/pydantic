use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyMapping};

use crate::build_tools::{is_strict, SchemaDict};
use crate::errors::{ValError, ValLineError, ValResult};
use crate::input::{
    DictGenericIterator, GenericMapping, Input, JsonObject, JsonObjectGenericIterator, MappingGenericIterator,
};
use crate::recursion_guard::RecursionGuard;

use super::any::AnyValidator;
use super::list::length_check;
use super::{build_validator, BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct DictValidator {
    strict: bool,
    key_validator: Box<CombinedValidator>,
    value_validator: Box<CombinedValidator>,
    min_length: Option<usize>,
    max_length: Option<usize>,
    name: String,
}

impl BuildValidator for DictValidator {
    const EXPECTED_TYPE: &'static str = "dict";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let key_validator = match schema.get_item(intern!(py, "keys_schema")) {
            Some(schema) => Box::new(build_validator(schema, config, build_context)?),
            None => Box::new(AnyValidator::build(schema, config, build_context)?),
        };
        let value_validator = match schema.get_item(intern!(py, "values_schema")) {
            Some(d) => Box::new(build_validator(d, config, build_context)?),
            None => Box::new(AnyValidator::build(schema, config, build_context)?),
        };
        let name = format!(
            "{}[{},{}]",
            Self::EXPECTED_TYPE,
            key_validator.get_name(),
            value_validator.get_name()
        );
        Ok(Self {
            strict: is_strict(schema, config)?,
            key_validator,
            value_validator,
            min_length: schema.get_as(intern!(py, "min_length"))?,
            max_length: schema.get_as(intern!(py, "max_length"))?,
            name,
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
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let dict = input.validate_dict(extra.strict.unwrap_or(self.strict))?;
        match dict {
            GenericMapping::PyDict(py_dict) => self.validate_dict(py, input, py_dict, extra, slots, recursion_guard),
            GenericMapping::PyMapping(mapping) => {
                self.validate_mapping(py, input, mapping, extra, slots, recursion_guard)
            }
            GenericMapping::PyGetAttr(_, _) => unreachable!(),
            GenericMapping::JsonObject(json_object) => {
                self.validate_json_object(py, input, json_object, extra, slots, recursion_guard)
            }
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, build_context: &BuildContext<CombinedValidator>) -> PyResult<()> {
        self.key_validator.complete(build_context)?;
        self.value_validator.complete(build_context)
    }
}

macro_rules! build_validate {
    ($name:ident, $dict_type:ty, $iter:ty) => {
        fn $name<'s, 'data>(
            &'s self,
            py: Python<'data>,
            input: &'data impl Input<'data>,
            dict: &'data $dict_type,
            extra: &Extra,
            slots: &'data [CombinedValidator],
            recursion_guard: &'s mut RecursionGuard,
        ) -> ValResult<'data, PyObject> {
            let output = PyDict::new(py);
            let mut errors: Vec<ValLineError> = Vec::new();

            let key_validator = self.key_validator.as_ref();
            let value_validator = self.value_validator.as_ref();
            for item_result in <$iter>::new(dict)? {
                let (key, value) = item_result?;
                let output_key = match key_validator.validate(py, key, extra, slots, recursion_guard) {
                    Ok(value) => Some(value),
                    Err(ValError::LineErrors(line_errors)) => {
                        for err in line_errors {
                            // these are added in reverse order so [key] is shunted along by the second call
                            errors.push(
                                err.with_outer_location("[key]".into())
                                    .with_outer_location(key.as_loc_item()),
                            );
                        }
                        None
                    }
                    Err(ValError::Omit) => continue,
                    Err(err) => return Err(err),
                };
                let output_value = match value_validator.validate(py, value, extra, slots, recursion_guard) {
                    Ok(value) => Some(value),
                    Err(ValError::LineErrors(line_errors)) => {
                        for err in line_errors {
                            errors.push(err.with_outer_location(key.as_loc_item()));
                        }
                        None
                    }
                    Err(ValError::Omit) => continue,
                    Err(err) => return Err(err),
                };
                if let (Some(key), Some(value)) = (output_key, output_value) {
                    output.set_item(key, value)?;
                }
            }

            if errors.is_empty() {
                length_check!(input, "Dictionary", self.min_length, self.max_length, output);
                Ok(output.into())
            } else {
                Err(ValError::LineErrors(errors))
            }
        }
    };
}

impl DictValidator {
    build_validate!(validate_dict, PyDict, DictGenericIterator);
    build_validate!(validate_mapping, PyMapping, MappingGenericIterator);
    build_validate!(validate_json_object, JsonObject, JsonObjectGenericIterator);
}
