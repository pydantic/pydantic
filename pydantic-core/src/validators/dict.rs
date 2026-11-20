use std::sync::Arc;

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
use super::list::{max_length_check, min_length_check};
use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator, build_validator};

#[derive(Debug)]
pub struct DictValidator {
    strict: bool,
    key_validator: Arc<CombinedValidator>,
    value_validator: Arc<CombinedValidator>,
    min_length: Option<usize>,
    max_length: Option<usize>,
    fail_fast: bool,
    name: String,
}

impl BuildValidator for DictValidator {
    const EXPECTED_TYPE: &'static str = "dict";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedValidator>>,
    ) -> PyResult<Arc<CombinedValidator>> {
        let py = schema.py();
        let key_validator = match schema.get_item(intern!(py, "keys_schema"))? {
            Some(schema) => build_validator(&schema, config, definitions)?,
            None => AnyValidator::build(schema, config, definitions)?,
        };
        let value_validator = match schema.get_item(intern!(py, "values_schema"))? {
            Some(d) => build_validator(&d, config, definitions)?,
            None => AnyValidator::build(schema, config, definitions)?,
        };
        let name = format!(
            "{}[{},{}]",
            Self::EXPECTED_TYPE,
            key_validator.get_name(),
            value_validator.get_name()
        );
        Ok(CombinedValidator::Dict(Self {
            strict: is_strict(schema, config)?,
            key_validator,
            value_validator,
            min_length: schema.get_as(intern!(py, "min_length"))?,
            max_length: schema.get_as(intern!(py, "max_length"))?,
            fail_fast: schema.get_as(intern!(py, "fail_fast"))?.unwrap_or(false),
            name,
        })
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
    ) -> ValResult<Py<PyAny>> {
        let strict = state.strict_or(self.strict);
        let dict = input.validate_dict(strict)?;
        dict.iterate(ValidateToDict {
            py,
            input,
            min_length: self.min_length,
            max_length: self.max_length,
            fail_fast: self.fail_fast,
            key_validator: &self.key_validator,
            value_validator: &self.value_validator,
            state,
        })?
    }

    fn supports_json_cursor(&self) -> bool {
        true
    }

    fn validate_json_cursor<'py>(
        &self,
        py: Python<'py>,
        input: &mut super::JsonCursor<'_>,
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Py<PyAny>> {
        if !matches!(input.jiter.peek(), Ok(jiter::Peek::Object)) {
            return self.validate(py, &input.take_value()?, state);
        }
        input.with_complete_container(|input| {
            let output = PyDict::new(py);
            let mut errors = Vec::new();
            let object_start = input.jiter.current_index();
            let mut key_start = object_start;
            let mut key = input.jiter.known_object().map_err(super::JsonCursor::parse_error)?;
            while let Some(name) = key {
                // `str` implements the existing JSON-key Input semantics, including
                // strict numeric-key coercion. JsonValue::Str is a different input.
                let output_key = match self.key_validator.validate(py, name, state) {
                    Ok(key) => Some(key),
                    Err(ValError::LineErrors(line_errors)) => {
                        extend_dict_errors(&mut errors, line_errors, name, true);
                        None
                    }
                    Err(ValError::Omit) => {
                        input.take_value()?;
                        key_start = input.jiter.current_index();
                        key = input.jiter.next_key().map_err(super::JsonCursor::parse_error)?;
                        continue;
                    }
                    Err(ValError::UseDefault) => {
                        input.skip_value()?;
                        input.finish_object()?;
                        return Err(ValError::UseDefault);
                    }
                    Err(error) => return Err(error),
                };
                if self.fail_fast && !errors.is_empty() {
                    input.skip_value()?;
                    input.finish_object()?;
                    return Err(ValError::LineErrors(errors));
                }
                match input.validate_next(py, &self.value_validator, state) {
                    Ok(value) => {
                        if let Some(output_key) = output_key {
                            output.set_item(output_key, value)?;
                            if self.max_length.is_some_and(|maximum| output.len() > maximum) {
                                input.finish_object()?;
                                max_length_check!(&*input, "Dictionary", self.max_length, output);
                            }
                        }
                    }
                    Err(ValError::LineErrors(line_errors)) => {
                        let name = cursor_key_at(input, object_start, key_start)?;
                        extend_dict_errors(&mut errors, line_errors, name, false);
                    }
                    Err(ValError::Omit) => (),
                    Err(ValError::UseDefault) => {
                        input.finish_object()?;
                        return Err(ValError::UseDefault);
                    }
                    Err(error) => return Err(error),
                }
                key_start = input.jiter.current_index();
                key = input.jiter.next_key().map_err(super::JsonCursor::parse_error)?;
            }
            if errors.is_empty() {
                let error_input = &*input;
                min_length_check!(error_input, "Dictionary", self.min_length, output);
                Ok(output.into_any().unbind())
            } else {
                Err(ValError::LineErrors(errors))
            }
        })
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}

/// Reconstruct the raw key only on rejected values, keeping successful entries allocation-free.
#[cold]
fn cursor_key_at(input: &super::JsonCursor<'_>, object_start: usize, key_start: usize) -> ValResult<String> {
    let mut parser = jiter::Jiter::new(&input.data[key_start..]).with_allow_inf_nan();
    let key = if key_start == object_start {
        parser.known_object()
    } else {
        parser.next_key()
    }
    .map_err(super::JsonCursor::parse_error)?;
    key.map(str::to_owned).ok_or_else(|| super::JsonCursor::parse_error(()))
}

/// Share dictionary location and key-error policy between ordinary and cursor validation.
#[cold]
fn extend_dict_errors<Key: Clone + Into<LocItem>>(
    errors: &mut Vec<ValLineError>,
    line_errors: Vec<ValLineError>,
    key: Key,
    key_error: bool,
) {
    errors.extend(line_errors.into_iter().map(|error| {
        let error = if key_error {
            error.with_outer_location("[key]")
        } else {
            error
        };
        error.with_outer_location(key.clone())
    }));
}

struct ValidateToDict<'a, 's, 'py, I: Input<'py> + ?Sized> {
    py: Python<'py>,
    input: &'a I,
    min_length: Option<usize>,
    max_length: Option<usize>,
    fail_fast: bool,
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
    type Output = ValResult<Py<PyAny>>;
    fn consume_iterator(self, iterator: impl Iterator<Item = ValResult<(Key, Value)>>) -> ValResult<Py<PyAny>> {
        let output = PyDict::new(self.py);
        let mut errors: Vec<ValLineError> = Vec::new();
        let allow_partial = self.state.allow_partial;

        macro_rules! should_fail_fast {
            () => {
                self.fail_fast && !errors.is_empty()
            };
        }

        for (_, is_last_partial, item_result) in self.state.enumerate_last_partial(iterator) {
            self.state.allow_partial = false.into();
            let (key, value) = item_result?;
            let output_key = match self.key_validator.validate(self.py, key.borrow_input(), self.state) {
                Ok(value) => Some(value),
                Err(ValError::LineErrors(line_errors)) => {
                    extend_dict_errors(&mut errors, line_errors, key.clone(), true);
                    None
                }
                Err(ValError::Omit) => continue,
                Err(err) => return Err(err),
            };
            self.state.allow_partial = match is_last_partial {
                true => allow_partial,
                false => false.into(),
            };

            if should_fail_fast!() {
                break;
            }

            let output_value = match self.value_validator.validate(self.py, value.borrow_input(), self.state) {
                Ok(value) => value,
                Err(ValError::LineErrors(line_errors)) => {
                    if !is_last_partial {
                        extend_dict_errors(&mut errors, line_errors, key.clone(), false);
                    }
                    continue;
                }
                Err(ValError::Omit) => continue,
                Err(err) => return Err(err),
            };

            if should_fail_fast!() {
                break;
            }

            if let Some(key) = output_key {
                output.set_item(key, output_value)?;
                max_length_check!(self.input, "Dictionary", self.max_length, output);
            }
        }

        if errors.is_empty() {
            let input = self.input;
            min_length_check!(input, "Dictionary", self.min_length, output);
            Ok(output.into())
        } else {
            Err(ValError::LineErrors(errors))
        }
    }
}
