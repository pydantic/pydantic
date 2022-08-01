use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyTuple};

use crate::build_tools::{is_strict, SchemaDict};
use crate::errors::{ErrorKind, ValError, ValLineError, ValResult};
use crate::input::{GenericListLike, Input};
use crate::recursion_guard::RecursionGuard;

use super::list::generic_list_like_build;
use super::{build_validator, BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug)]
pub struct TupleBuilder;

impl BuildValidator for TupleBuilder {
    const EXPECTED_TYPE: &'static str = "tuple";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext,
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
    size_range: Option<(Option<usize>, Option<usize>)>,
    name: String,
}

impl TupleVariableValidator {
    generic_list_like_build!("{}[{}, ...]", "tuple");
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

        let length = seq.check_len(self.size_range, input)?;

        let output = match self.item_validator {
            Some(ref v) => seq.validate_to_vec(py, length, v, extra, slots, recursion_guard)?,
            None => match seq {
                GenericListLike::Tuple(tuple) => return Ok(tuple.into_py(py)),
                _ => seq.to_vec(py),
            },
        };
        Ok(PyTuple::new(py, &output).into_py(py))
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, build_context: &BuildContext) -> PyResult<()> {
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
        build_context: &mut BuildContext,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let items: &PyList = schema.get_as_req(intern!(py, "items_schema"))?;
        let validators: Vec<CombinedValidator> = items
            .iter()
            .map(|item| build_validator(item, config, build_context))
            .collect::<PyResult<Vec<CombinedValidator>>>()?;

        let descr = validators.iter().map(|v| v.get_name()).collect::<Vec<_>>().join(", ");
        Ok(Self {
            strict: is_strict(schema, config)?,
            items_validators: validators,
            extra_validator: match schema.get_item(intern!(py, "extra_schema")) {
                Some(v) => Some(Box::new(build_validator(v, config, build_context)?)),
                None => None,
            },
            name: format!("tuple[{}]", descr),
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
        let list_like = input.validate_tuple(extra.strict.unwrap_or(self.strict))?;
        let expected_length = self.items_validators.len();

        let ll_length = list_like.generic_len();
        if ll_length < expected_length {
            return Err(ValError::LineErrors(
                (ll_length..expected_length)
                    .map(|index| ValLineError::new_with_loc(ErrorKind::Missing, input, index))
                    .collect(),
            ));
        }
        let mut output: Vec<PyObject> = Vec::with_capacity(expected_length);
        let mut errors: Vec<ValLineError> = Vec::new();
        macro_rules! iter {
            ($list_like:expr) => {
                for (index, item) in $list_like.iter().enumerate() {
                    let validator = match self.items_validators.get(index) {
                        Some(ref v) => v,
                        None => match self.extra_validator {
                            Some(ref v) => v.as_ref(),
                            None => {
                                return Err(ValError::new(
                                    ErrorKind::TooLong {
                                        max_length: expected_length,
                                        input_length: ll_length,
                                    },
                                    input,
                                ));
                            }
                        },
                    };

                    match validator.validate(py, item, extra, slots, recursion_guard) {
                        Ok(item) => output.push(item),
                        Err(ValError::LineErrors(line_errors)) => {
                            errors.extend(
                                line_errors
                                    .into_iter()
                                    .map(|err| err.with_outer_location(index.into())),
                            );
                        }
                        Err(err) => return Err(err),
                    }
                }
            };
        }
        match list_like {
            GenericListLike::List(list_like) => iter!(list_like),
            GenericListLike::Tuple(list_like) => iter!(list_like),
            GenericListLike::Set(list_like) => iter!(list_like),
            GenericListLike::FrozenSet(list_like) => iter!(list_like),
            GenericListLike::JsonArray(list_like) => iter!(list_like),
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

    fn complete(&mut self, build_context: &BuildContext) -> PyResult<()> {
        self.items_validators
            .iter_mut()
            .try_for_each(|v| v.complete(build_context))
    }
}
