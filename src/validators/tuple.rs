use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyTuple};

use crate::build_tools::{is_strict, SchemaDict};
use crate::errors::{ErrorType, ValError, ValLineError, ValResult};
use crate::input::{GenericCollection, Input};
use crate::recursion_guard::RecursionGuard;

use super::list::{get_items_schema, length_check};
use super::with_default::get_default;
use super::{build_validator, BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug)]
pub struct TupleBuilder;

impl BuildValidator for TupleBuilder {
    const EXPECTED_TYPE: &'static str = "tuple";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        match schema.get_as::<&str>(intern!(schema.py(), "mode"))? {
            Some("positional") => TuplePositionalValidator::build(schema, config, build_context),
            _ => TupleVariableValidator::build(schema, config, build_context),
        }
    }
}

#[derive(Debug, Clone)]
pub struct TupleVariableValidator {
    strict: bool,
    item_validator: Option<Box<CombinedValidator>>,
    min_length: Option<usize>,
    max_length: Option<usize>,
    name: String,
}

impl TupleVariableValidator {
    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let item_validator = get_items_schema(schema, config, build_context)?;
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
        slots: &'data [CombinedValidator],
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
                slots,
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

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, build_context: &BuildContext<CombinedValidator>) -> PyResult<()> {
        match self.item_validator {
            Some(ref mut v) => v.complete(build_context),
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

impl TuplePositionalValidator {
    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let items: &PyList = schema.get_as_req(intern!(py, "items_schema"))?;
        let validators: Vec<CombinedValidator> = items
            .iter()
            .map(|item| build_validator(item, config, build_context))
            .collect::<PyResult<_>>()?;

        let descr = validators.iter().map(|v| v.get_name()).collect::<Vec<_>>().join(", ");
        Ok(Self {
            strict: is_strict(schema, config)?,
            items_validators: validators,
            extra_validator: match schema.get_item(intern!(py, "extra_schema")) {
                Some(v) => Some(Box::new(build_validator(v, config, build_context)?)),
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
        slots: &'data [CombinedValidator],
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
                        Some(item) => match validator.validate(py, item, extra, slots, recursion_guard) {
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
                            if let Some(value) = get_default(py, &validator)? {
                                output.push(value.as_ref().clone_ref(py));
                            } else {
                                errors.push(ValLineError::new_with_loc(ErrorType::Missing, input, index));
                            }
                        }
                    }
                }
                for (index, item) in $collection_iter.enumerate() {
                    match self.extra_validator {
                        Some(ref extra_validator) => {
                            match extra_validator.validate(py, item, extra, slots, recursion_guard) {
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

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, build_context: &BuildContext<CombinedValidator>) -> PyResult<()> {
        self.items_validators
            .iter_mut()
            .try_for_each(|v| v.complete(build_context))
    }
}
