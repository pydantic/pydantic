use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyTuple};

use crate::build_tools::is_strict;
use crate::errors::{ErrorType, ErrorTypeDefaults, ValError, ValLineError, ValResult};
use crate::input::{GenericIterable, Input};
use crate::tools::SchemaDict;

use super::list::{get_items_schema, min_length_check};
use super::{build_validator, BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

#[derive(Debug, Clone)]
pub struct TupleVariableValidator {
    strict: bool,
    item_validator: Option<Box<CombinedValidator>>,
    min_length: Option<usize>,
    max_length: Option<usize>,
    name: String,
}

impl BuildValidator for TupleVariableValidator {
    const EXPECTED_TYPE: &'static str = "tuple-variable";
    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let item_validator = get_items_schema(schema, config, definitions)?;
        let inner_name = item_validator.as_ref().map_or("any", |v| v.get_name());
        let name = format!("tuple[{inner_name}, ...]");
        Ok(Self {
            strict: is_strict(schema, config)?,
            item_validator,
            min_length: schema.get_as(intern!(py, "min_length"))?,
            max_length: schema.get_as(intern!(py, "max_length"))?,
            name,
        }
        .into())
    }
}

impl_py_gc_traverse!(TupleVariableValidator { item_validator });

impl Validator for TupleVariableValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        let seq = input.validate_tuple(state.strict_or(self.strict))?;

        let output = match self.item_validator {
            Some(ref v) => seq.validate_to_vec(py, input, self.max_length, "Tuple", v, state)?,
            None => seq.to_vec(py, input, "Tuple", self.max_length)?,
        };
        min_length_check!(input, "Tuple", self.min_length, output);
        Ok(PyTuple::new(py, &output).into_py(py))
    }

    fn different_strict_behavior(
        &self,
        definitions: Option<&DefinitionsBuilder<CombinedValidator>>,
        ultra_strict: bool,
    ) -> bool {
        if ultra_strict {
            match self.item_validator {
                Some(ref v) => v.different_strict_behavior(definitions, true),
                None => false,
            }
        } else {
            true
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, definitions: &DefinitionsBuilder<CombinedValidator>) -> PyResult<()> {
        match self.item_validator {
            Some(ref mut v) => v.complete(definitions),
            None => Ok(()),
        }
    }
}

#[derive(Debug, Clone)]
pub struct TuplePositionalValidator {
    strict: bool,
    items_validators: Vec<CombinedValidator>,
    extras_validator: Option<Box<CombinedValidator>>,
    name: String,
}

impl BuildValidator for TuplePositionalValidator {
    const EXPECTED_TYPE: &'static str = "tuple-positional";
    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let items: &PyList = schema.get_as_req(intern!(py, "items_schema"))?;
        let validators: Vec<CombinedValidator> = items
            .iter()
            .map(|item| build_validator(item, config, definitions))
            .collect::<PyResult<_>>()?;

        let descr = validators
            .iter()
            .map(Validator::get_name)
            .collect::<Vec<_>>()
            .join(", ");
        Ok(Self {
            strict: is_strict(schema, config)?,
            items_validators: validators,
            extras_validator: match schema.get_item(intern!(py, "extras_schema")) {
                Some(v) => Some(Box::new(build_validator(v, config, definitions)?)),
                None => None,
            },
            name: format!("tuple[{descr}]"),
        }
        .into())
    }
}

#[allow(clippy::too_many_arguments)]
fn validate_tuple_positional<'s, 'data, T: Iterator<Item = PyResult<&'data I>>, I: Input<'data> + 'data>(
    py: Python<'data>,
    input: &'data impl Input<'data>,
    state: &mut ValidationState,
    output: &mut Vec<PyObject>,
    errors: &mut Vec<ValLineError<'data>>,
    extras_validator: &Option<Box<CombinedValidator>>,
    items_validators: &[CombinedValidator],
    collection_iter: &mut T,
    collection_len: Option<usize>,
    expected_length: usize,
) -> ValResult<'data, ()> {
    for (index, validator) in items_validators.iter().enumerate() {
        match collection_iter.next() {
            Some(result) => match validator.validate(py, result?, state) {
                Ok(item) => output.push(item),
                Err(ValError::LineErrors(line_errors)) => {
                    errors.extend(line_errors.into_iter().map(|err| err.with_outer_location(index.into())));
                }
                Err(err) => return Err(err),
            },
            None => {
                if let Some(value) = validator.default_value(py, Some(index), state)? {
                    output.push(value);
                } else {
                    errors.push(ValLineError::new_with_loc(ErrorTypeDefaults::Missing, input, index));
                }
            }
        }
    }
    for (index, result) in collection_iter.enumerate() {
        let item = result?;
        match extras_validator {
            Some(ref extras_validator) => match extras_validator.validate(py, item, state) {
                Ok(item) => output.push(item),
                Err(ValError::LineErrors(line_errors)) => {
                    errors.extend(
                        line_errors
                            .into_iter()
                            .map(|err| err.with_outer_location((index + expected_length).into())),
                    );
                }
                Err(ValError::Omit) => (),
                Err(err) => return Err(err),
            },
            None => {
                errors.push(ValLineError::new(
                    ErrorType::TooLong {
                        field_type: "Tuple".to_string(),
                        max_length: expected_length,
                        actual_length: collection_len.unwrap_or(index),
                        context: None,
                    },
                    input,
                ));
                // no need to continue through further items
                break;
            }
        }
    }
    Ok(())
}

impl_py_gc_traverse!(TuplePositionalValidator {
    items_validators,
    extras_validator
});

impl Validator for TuplePositionalValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        let collection = input.validate_tuple(state.strict_or(self.strict))?;
        let expected_length = self.items_validators.len();
        let collection_len = collection.generic_len();

        let mut output: Vec<PyObject> = Vec::with_capacity(expected_length);
        let mut errors: Vec<ValLineError> = Vec::new();

        macro_rules! iter {
            ($collection_iter:expr) => {{
                validate_tuple_positional(
                    py,
                    input,
                    state,
                    &mut output,
                    &mut errors,
                    &self.extras_validator,
                    &self.items_validators,
                    &mut $collection_iter,
                    collection_len,
                    expected_length,
                )?
            }};
        }

        match collection {
            GenericIterable::List(collection_iter) => iter!(collection_iter.iter().map(Ok)),
            GenericIterable::Tuple(collection_iter) => iter!(collection_iter.iter().map(Ok)),
            GenericIterable::JsonArray(collection_iter) => iter!(collection_iter.iter().map(Ok)),
            other => iter!(other.as_sequence_iterator(py)?),
        }
        if errors.is_empty() {
            Ok(PyTuple::new(py, &output).into_py(py))
        } else {
            Err(ValError::LineErrors(errors))
        }
    }

    fn different_strict_behavior(
        &self,
        definitions: Option<&DefinitionsBuilder<CombinedValidator>>,
        ultra_strict: bool,
    ) -> bool {
        if ultra_strict {
            if self
                .items_validators
                .iter()
                .any(|v| v.different_strict_behavior(definitions, true))
            {
                true
            } else if let Some(ref v) = self.extras_validator {
                v.different_strict_behavior(definitions, true)
            } else {
                false
            }
        } else {
            true
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, definitions: &DefinitionsBuilder<CombinedValidator>) -> PyResult<()> {
        self.items_validators
            .iter_mut()
            .try_for_each(|v| v.complete(definitions))?;
        match &mut self.extras_validator {
            Some(v) => v.complete(definitions),
            None => Ok(()),
        }
    }
}
