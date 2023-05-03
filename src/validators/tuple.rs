use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyTuple};

use crate::build_tools::{is_strict, SchemaDict};
use crate::errors::{ErrorType, ValError, ValLineError, ValResult};
use crate::input::{GenericCollection, Input};
use crate::recursion_guard::RecursionGuard;

use super::list::{get_items_schema, length_check};
use super::{build_validator, BuildValidator, CombinedValidator, Definitions, DefinitionsBuilder, Extra, Validator};

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
        let inner_name = item_validator.as_ref().map(|v| v.get_name()).unwrap_or("any");
        let name = format!("tuple[{inner_name}, ...]");
        Ok(Self {
            strict: crate::build_tools::is_strict(schema, config)?,
            item_validator,
            min_length: schema.get_as(pyo3::intern!(py, "min_length"))?,
            max_length: schema.get_as(pyo3::intern!(py, "max_length"))?,
            name,
        }
        .into())
    }
}

impl Validator for TupleVariableValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        definitions: &'data Definitions<CombinedValidator>,
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let seq = input.validate_tuple(extra.strict.unwrap_or(self.strict))?;

        let output = match self.item_validator {
            Some(ref v) => seq.validate_to_vec(
                py,
                input,
                self.max_length,
                "Tuple",
                self.max_length,
                v,
                extra,
                definitions,
                recursion_guard,
            )?,
            None => match seq {
                GenericCollection::Tuple(tuple) => {
                    length_check!(input, "Tuple", self.min_length, self.max_length, tuple);
                    return Ok(tuple.into_py(py));
                }
                _ => seq.to_vec(py, input, "Tuple", self.max_length)?,
            },
        };
        length_check!(input, "Tuple", self.min_length, self.max_length, output);
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
    extra_validator: Option<Box<CombinedValidator>>,
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

        let descr = validators.iter().map(|v| v.get_name()).collect::<Vec<_>>().join(", ");
        Ok(Self {
            strict: is_strict(schema, config)?,
            items_validators: validators,
            extra_validator: match schema.get_item(intern!(py, "extra_schema")) {
                Some(v) => Some(Box::new(build_validator(v, config, definitions)?)),
                None => None,
            },
            name: format!("tuple[{descr}]"),
        }
        .into())
    }
}

impl Validator for TuplePositionalValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        definitions: &'data Definitions<CombinedValidator>,
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let collection = input.validate_tuple(extra.strict.unwrap_or(self.strict))?;
        let expected_length = self.items_validators.len();

        let mut output: Vec<PyObject> = Vec::with_capacity(expected_length);
        let mut errors: Vec<ValLineError> = Vec::new();
        macro_rules! iter {
            ($collection_iter:expr) => {{
                for (index, validator) in self.items_validators.iter().enumerate() {
                    match $collection_iter.next() {
                        Some(item) => match validator.validate(py, item, extra, definitions, recursion_guard) {
                            Ok(item) => output.push(item),
                            Err(ValError::LineErrors(line_errors)) => {
                                errors.extend(
                                    line_errors
                                        .into_iter()
                                        .map(|err| err.with_outer_location(index.into())),
                                );
                            }
                            Err(err) => return Err(err),
                        },
                        None => {
                            if let Some(value) =
                                validator.default_value(py, Some(index), extra, definitions, recursion_guard)?
                            {
                                output.push(value);
                            } else {
                                errors.push(ValLineError::new_with_loc(ErrorType::Missing, input, index));
                            }
                        }
                    }
                }
                for (index, item) in $collection_iter.enumerate() {
                    match self.extra_validator {
                        Some(ref extra_validator) => {
                            match extra_validator.validate(py, item, extra, definitions, recursion_guard) {
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
                            }
                        }
                        None => {
                            errors.push(ValLineError::new(
                                ErrorType::TooLong {
                                    field_type: "Tuple".to_string(),
                                    max_length: expected_length,
                                    actual_length: collection.generic_len()?,
                                },
                                input,
                            ));
                            // no need to continue through further items
                            break;
                        }
                    }
                }
            }};
        }
        match collection {
            GenericCollection::List(collection) => {
                let mut iter = collection.iter();
                iter!(iter)
            }
            GenericCollection::Tuple(collection) => {
                let mut iter = collection.iter();
                iter!(iter)
            }
            GenericCollection::PyAny(collection) => {
                let vec: Vec<&PyAny> = collection.iter()?.collect::<PyResult<_>>()?;
                let mut iter = vec.into_iter();
                iter!(iter)
            }
            GenericCollection::JsonArray(collection) => {
                let mut iter = collection.iter();
                iter!(iter)
            }
            _ => unreachable!(),
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
            } else if let Some(ref v) = self.extra_validator {
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
        match &mut self.extra_validator {
            Some(v) => v.complete(definitions),
            None => Ok(()),
        }
    }
}
