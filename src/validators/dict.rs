use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::is_strict;
use crate::errors::{ValError, ValLineError, ValResult};
use crate::input::{DictGenericIterator, GenericMapping, Input, JsonObjectGenericIterator, MappingGenericIterator};

use crate::tools::SchemaDict;

use super::any::AnyValidator;
use super::list::length_check;
use super::{build_validator, BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

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
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let key_validator = match schema.get_item(intern!(py, "keys_schema")) {
            Some(schema) => Box::new(build_validator(schema, config, definitions)?),
            None => Box::new(AnyValidator::build(schema, config, definitions)?),
        };
        let value_validator = match schema.get_item(intern!(py, "values_schema")) {
            Some(d) => Box::new(build_validator(d, config, definitions)?),
            None => Box::new(AnyValidator::build(schema, config, definitions)?),
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

impl_py_gc_traverse!(DictValidator {
    key_validator,
    value_validator
});

impl Validator for DictValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        let strict = state.strict_or(self.strict);
        let dict = input.validate_dict(strict)?;
        match dict {
            GenericMapping::PyDict(py_dict) => {
                self.validate_generic_mapping(py, input, DictGenericIterator::new(py_dict)?, state)
            }
            GenericMapping::PyMapping(mapping) => {
                self.validate_generic_mapping(py, input, MappingGenericIterator::new(mapping)?, state)
            }
            GenericMapping::PyGetAttr(_, _) => unreachable!(),
            GenericMapping::JsonObject(json_object) => {
                self.validate_generic_mapping(py, input, JsonObjectGenericIterator::new(json_object)?, state)
            }
        }
    }

    fn different_strict_behavior(
        &self,
        definitions: Option<&DefinitionsBuilder<CombinedValidator>>,
        ultra_strict: bool,
    ) -> bool {
        if ultra_strict {
            self.key_validator.different_strict_behavior(definitions, true)
                || self.value_validator.different_strict_behavior(definitions, true)
        } else {
            true
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, definitions: &DefinitionsBuilder<CombinedValidator>) -> PyResult<()> {
        self.key_validator.complete(definitions)?;
        self.value_validator.complete(definitions)
    }
}

impl DictValidator {
    fn validate_generic_mapping<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        mapping_iter: impl Iterator<
            Item = ValResult<'data, (&'data (impl Input<'data> + 'data), &'data (impl Input<'data> + 'data))>,
        >,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        let output = PyDict::new(py);
        let mut errors: Vec<ValLineError> = Vec::new();

        let key_validator = self.key_validator.as_ref();
        let value_validator = self.value_validator.as_ref();
        for item_result in mapping_iter {
            let (key, value) = item_result?;
            let output_key = match key_validator.validate(py, key, state) {
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
            let output_value = match value_validator.validate(py, value, state) {
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
}
