use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyTuple};
use std::collections::VecDeque;

use crate::build_tools::is_strict;
use crate::errors::{py_err_string, ErrorType, ErrorTypeDefaults, ValError, ValLineError, ValResult};
use crate::input::ConsumeIterator;
use crate::input::{BorrowInput, Input, ValidatedTuple};
use crate::tools::SchemaDict;

use super::{build_validator, BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

#[derive(Debug)]
pub struct TupleValidator {
    strict: bool,
    validators: Vec<CombinedValidator>,
    variadic_item_index: Option<usize>,
    min_length: Option<usize>,
    max_length: Option<usize>,
    name: String,
}

impl BuildValidator for TupleValidator {
    const EXPECTED_TYPE: &'static str = "tuple";
    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let items: Bound<'_, PyList> = schema.get_as_req(intern!(py, "items_schema"))?;
        let validators: Vec<CombinedValidator> = items
            .iter()
            .map(|item| build_validator(&item, config, definitions))
            .collect::<PyResult<_>>()?;

        let mut validator_names = validators.iter().map(Validator::get_name).collect::<Vec<_>>();
        let variadic_item_index: Option<usize> = schema.get_as(intern!(py, "variadic_item_index"))?;
        // FIXME add friendly schema error if item out of bounds
        if let Some(variadic_item_index) = variadic_item_index {
            validator_names.insert(variadic_item_index + 1, "...");
        }
        let name = format!("tuple[{}]", validator_names.join(", "));

        Ok(Self {
            strict: is_strict(schema, config)?,
            validators,
            variadic_item_index,
            min_length: schema.get_as(intern!(py, "min_length"))?,
            max_length: schema.get_as(intern!(py, "max_length"))?,
            name,
        }
        .into())
    }
}

impl_py_gc_traverse!(TupleValidator { validators });

impl TupleValidator {
    #[allow(clippy::too_many_arguments)]
    fn validate_tuple_items<'py, I: BorrowInput<'py>>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
        output: &mut Vec<PyObject>,
        errors: &mut Vec<ValLineError>,
        item_validators: &[CombinedValidator],
        collection_iter: &mut NextCountingIterator<impl Iterator<Item = I>>,
        actual_length: Option<usize>,
    ) -> ValResult<()> {
        // Validate the head:
        for validator in item_validators {
            match collection_iter.next() {
                Some((index, input_item)) => match validator.validate(py, input_item.borrow_input(), state) {
                    Ok(item) => self.push_output_item(input, output, item, actual_length)?,
                    Err(ValError::LineErrors(line_errors)) => {
                        errors.extend(line_errors.into_iter().map(|err| err.with_outer_location(index)));
                    }
                    Err(ValError::Omit) => (),
                    Err(err) => return Err(err),
                },
                None => {
                    let index = collection_iter.next_calls() - 1;
                    if let Some(value) = validator.default_value(py, Some(index), state)? {
                        output.push(value);
                    } else {
                        errors.push(ValLineError::new_with_loc(ErrorTypeDefaults::Missing, input, index));
                    }
                }
            }
        }

        Ok(())
    }

    #[allow(clippy::too_many_arguments)]
    fn validate_tuple_variable<'py, I: BorrowInput<'py>>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
        errors: &mut Vec<ValLineError>,
        collection_iter: &mut NextCountingIterator<impl Iterator<Item = I>>,
        actual_length: Option<usize>,
    ) -> ValResult<Vec<PyObject>> {
        let expected_length = if self.variadic_item_index.is_some() {
            actual_length.unwrap_or(self.validators.len())
        } else {
            self.validators.len()
        };
        let mut output = Vec::with_capacity(expected_length);
        if let Some(variable_validator_index) = self.variadic_item_index {
            let (head_validators, [variable_validator, tail_validators @ ..]) =
                self.validators.split_at(variable_validator_index)
            else {
                unreachable!("validators will always contain variable validator")
            };

            // Validate the "head" items
            self.validate_tuple_items(
                py,
                input,
                state,
                &mut output,
                errors,
                head_validators,
                collection_iter,
                actual_length,
            )?;

            let n_tail_validators = tail_validators.len();
            if n_tail_validators == 0 {
                for (index, input_item) in collection_iter {
                    match variable_validator.validate(py, input_item.borrow_input(), state) {
                        Ok(item) => self.push_output_item(input, &mut output, item, actual_length)?,
                        Err(ValError::LineErrors(line_errors)) => {
                            errors.extend(line_errors.into_iter().map(|err| err.with_outer_location(index)));
                        }
                        Err(ValError::Omit) => (),
                        Err(err) => return Err(err),
                    }
                }
            } else {
                // Populate a buffer with the first n_tail_validators items
                // NB: We take from collection_iter.inner to avoid increasing the next calls count
                // while populating the buffer. This means the index in the following loop is the
                // right one for user errors.
                let mut tail_buffer: VecDeque<I> = collection_iter.inner.by_ref().take(n_tail_validators).collect();

                // Save the current index for the tail validation below when we recreate a new NextCountingIterator
                let mut index = collection_iter.next_calls();

                // Iterate over all remaining collection items, validating as items "leave" the buffer
                for (buffer_item_index, input_item) in collection_iter {
                    index = buffer_item_index;
                    // This `unwrap` is safe because you can only get here
                    // if there were at least `n_tail_validators` (> 0) items in the iterator
                    let buffered_item = tail_buffer.pop_front().unwrap();
                    tail_buffer.push_back(input_item);

                    match variable_validator.validate(py, buffered_item.borrow_input(), state) {
                        Ok(item) => self.push_output_item(input, &mut output, item, actual_length)?,
                        Err(ValError::LineErrors(line_errors)) => {
                            errors.extend(
                                line_errors
                                    .into_iter()
                                    .map(|err| err.with_outer_location(buffer_item_index)),
                            );
                        }
                        Err(ValError::Omit) => (),
                        Err(err) => return Err(err),
                    }
                }

                // Validate the buffered items using the tail validators
                self.validate_tuple_items(
                    py,
                    input,
                    state,
                    &mut output,
                    errors,
                    tail_validators,
                    &mut NextCountingIterator::new(tail_buffer.into_iter(), index),
                    actual_length,
                )?;
            }
        } else {
            // Validate all items as positional
            self.validate_tuple_items(
                py,
                input,
                state,
                &mut output,
                errors,
                &self.validators,
                collection_iter,
                actual_length,
            )?;

            // Generate an error if there are any extra items:
            if collection_iter.next().is_some() {
                return Err(ValError::new(
                    ErrorType::TooLong {
                        field_type: "Tuple".to_string(),
                        max_length: self.validators.len(),
                        actual_length,
                        context: None,
                    },
                    input,
                ));
            }
        }
        Ok(output)
    }

    fn push_output_item<'py>(
        &self,
        input: &(impl Input<'py> + ?Sized),
        output: &mut Vec<PyObject>,
        item: PyObject,
        actual_length: Option<usize>,
    ) -> ValResult<()> {
        output.push(item);
        if let Some(max_length) = self.max_length {
            if output.len() > max_length {
                return Err(ValError::new(
                    ErrorType::TooLong {
                        field_type: "Tuple".to_string(),
                        max_length,
                        actual_length,
                        context: None,
                    },
                    input,
                ));
            }
        }
        Ok(())
    }
}

impl Validator for TupleValidator {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<PyObject> {
        let collection = input.validate_tuple(state.strict_or(self.strict))?.unpack(state);
        let actual_length = collection.len();

        let mut errors: Vec<ValLineError> = Vec::new();

        let output = collection.iterate(ValidateToTuple {
            py,
            input,
            actual_length,
            validator: self,
            errors: &mut errors,
            state,
        })??;

        if let Some(min_length) = self.min_length {
            let actual_length = output.len();
            if actual_length < min_length {
                errors.push(ValLineError::new(
                    ErrorType::TooShort {
                        field_type: "Tuple".to_string(),
                        min_length,
                        actual_length,
                        context: None,
                    },
                    input,
                ));
            }
        }

        if errors.is_empty() {
            Ok(PyTuple::new_bound(py, output).into_py(py))
        } else {
            Err(ValError::LineErrors(errors))
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}

struct ValidateToTuple<'a, 's, 'py, I: Input<'py> + ?Sized> {
    py: Python<'py>,
    input: &'a I,
    actual_length: Option<usize>,
    validator: &'a TupleValidator,
    errors: &'a mut Vec<ValLineError>,
    state: &'a mut ValidationState<'s, 'py>,
}

impl<'py, T, I> ConsumeIterator<PyResult<T>> for ValidateToTuple<'_, '_, 'py, I>
where
    T: BorrowInput<'py>,
    I: Input<'py> + ?Sized,
{
    type Output = ValResult<Vec<PyObject>>;
    fn consume_iterator(self, mut iterator: impl Iterator<Item = PyResult<T>>) -> ValResult<Vec<PyObject>> {
        let mut iteration_error = None;

        let output = self.validator.validate_tuple_variable(
            self.py,
            self.input,
            self.state,
            self.errors,
            &mut NextCountingIterator::new(
                {
                    let iteration_error = &mut iteration_error;
                    let mut index: usize = 0;
                    std::iter::from_fn(move || {
                        if iteration_error.is_some() {
                            return None;
                        }
                        index += 1;
                        match iterator.next() {
                            Some(Ok(item)) => Some(item),
                            Some(Err(e)) => {
                                *iteration_error = Some(ValError::new_with_loc(
                                    ErrorType::IterationError {
                                        error: py_err_string(self.py, e),
                                        context: None,
                                    },
                                    self.input,
                                    index,
                                ));
                                None
                            }
                            None => None,
                        }
                    })
                },
                0,
            ),
            self.actual_length,
        )?;

        if let Some(err) = iteration_error {
            return Err(err);
        }

        Ok(output)
    }
}

struct NextCountingIterator<I: Iterator> {
    inner: I,
    count: usize,
}

impl<I: Iterator> NextCountingIterator<I> {
    fn new(inner: I, count: usize) -> Self {
        Self { inner, count }
    }

    fn next_calls(&self) -> usize {
        self.count
    }
}

impl<I: Iterator> Iterator for NextCountingIterator<I> {
    type Item = (usize, I::Item);

    fn next(&mut self) -> Option<Self::Item> {
        let count = self.count;
        self.count += 1;
        self.inner.next().map(|item| (count, item))
    }
}
