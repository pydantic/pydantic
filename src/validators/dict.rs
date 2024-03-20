use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::is_strict;
use crate::errors::{LocItem, ValError, ValLineError, ValResult};
use crate::input::BorrowInput;
use crate::input::ConsumeIterator;
use crate::input::{Input, ValidatedDict};

use crate::tools::SchemaDict;

use super::any::AnyValidator;
use super::list::length_check;
use super::{build_validator, BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

#[derive(Debug)]
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
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let key_validator = match schema.get_item(intern!(py, "keys_schema"))? {
            Some(schema) => Box::new(build_validator(&schema, config, definitions)?),
            None => Box::new(AnyValidator::build(schema, config, definitions)?),
        };
        let value_validator = match schema.get_item(intern!(py, "values_schema"))? {
            Some(d) => Box::new(build_validator(&d, config, definitions)?),
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
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<PyObject> {
        let strict = state.strict_or(self.strict);
        let dict = input.validate_dict(strict)?;
        dict.iterate(ValidateToDict {
            py,
            input,
            min_length: self.min_length,
            max_length: self.max_length,
            key_validator: &self.key_validator,
            value_validator: &self.value_validator,
            state,
        })?
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}

struct ValidateToDict<'a, 's, 'py, I: Input<'py> + ?Sized> {
    py: Python<'py>,
    input: &'a I,
    min_length: Option<usize>,
    max_length: Option<usize>,
    key_validator: &'a CombinedValidator,
    value_validator: &'a CombinedValidator,
    state: &'a mut ValidationState<'s, 'py>,
}

impl<'py, Key, Value, I: Input<'py> + ?Sized> ConsumeIterator<ValResult<(Key, Value)>>
    for ValidateToDict<'_, '_, 'py, I>
where
    Key: BorrowInput<'py> + Clone + Into<LocItem>,
    Value: BorrowInput<'py>,
{
    type Output = ValResult<PyObject>;
    fn consume_iterator(self, iterator: impl Iterator<Item = ValResult<(Key, Value)>>) -> ValResult<PyObject> {
        let output = PyDict::new_bound(self.py);
        let mut errors: Vec<ValLineError> = Vec::new();

        for item_result in iterator {
            let (key, value) = item_result?;
            let output_key = match self.key_validator.validate(self.py, key.borrow_input(), self.state) {
                Ok(value) => Some(value),
                Err(ValError::LineErrors(line_errors)) => {
                    for err in line_errors {
                        // these are added in reverse order so [key] is shunted along by the second call
                        errors.push(err.with_outer_location("[key]").with_outer_location(key.clone()));
                    }
                    None
                }
                Err(ValError::Omit) => continue,
                Err(err) => return Err(err),
            };
            let output_value = match self.value_validator.validate(self.py, value.borrow_input(), self.state) {
                Ok(value) => Some(value),
                Err(ValError::LineErrors(line_errors)) => {
                    for err in line_errors {
                        errors.push(err.with_outer_location(key.clone()));
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
            let input = self.input;
            length_check!(input, "Dictionary", self.min_length, self.max_length, output);
            Ok(output.into())
        } else {
            Err(ValError::LineErrors(errors))
        }
    }
}
