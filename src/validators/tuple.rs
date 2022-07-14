use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyTuple};

use crate::build_tools::{is_strict, py_error, SchemaDict};
use crate::errors::{ErrorKind, ValError, ValLineError, ValResult};
use crate::input::{GenericSequence, Input};
use crate::recursion_guard::RecursionGuard;

use super::any::AnyValidator;
use super::list::sequence_build_function;
use super::{build_validator, BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct TupleVarLenValidator {
    strict: bool,
    item_validator: Box<CombinedValidator>,
    min_items: Option<usize>,
    max_items: Option<usize>,
    name: String,
}

impl BuildValidator for TupleVarLenValidator {
    const EXPECTED_TYPE: &'static str = "tuple-var-len";
    sequence_build_function!();
}

impl Validator for TupleVarLenValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let seq = input.validate_tuple(extra.strict.unwrap_or(self.strict))?;
        let length = seq.generic_len();
        if let Some(min_length) = self.min_items {
            if length < min_length {
                return Err(ValError::new(ErrorKind::TooShort { min_length }, input));
            }
        }
        if let Some(max_length) = self.max_items {
            if length > max_length {
                return Err(ValError::new(ErrorKind::TooLong { max_length }, input));
            }
        }

        let output = seq.validate_to_vec(py, length, &self.item_validator, extra, slots, recursion_guard)?;
        Ok(PyTuple::new(py, &output).into_py(py))
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, build_context: &BuildContext) -> PyResult<()> {
        self.item_validator.complete(build_context)
    }
}

#[derive(Debug, Clone)]
pub struct TupleFixLenValidator {
    strict: bool,
    items_validators: Vec<CombinedValidator>,
    name: String,
}

impl BuildValidator for TupleFixLenValidator {
    const EXPECTED_TYPE: &'static str = "tuple-fix-len";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext,
    ) -> PyResult<CombinedValidator> {
        let items: &PyList = schema.get_as_req("items_schema")?;
        if items.is_empty() {
            return py_error!("Missing schemas for tuple elements");
        }
        let validators: Vec<CombinedValidator> = items
            .iter()
            .map(|item| build_validator(item, config, build_context).map(|result| result.0))
            .collect::<PyResult<Vec<CombinedValidator>>>()?;

        let descr = validators.iter().map(|v| v.get_name()).collect::<Vec<_>>().join(", ");
        Ok(Self {
            strict: is_strict(schema, config)?,
            items_validators: validators,
            name: format!("{}[{}]", Self::EXPECTED_TYPE, descr),
        }
        .into())
    }
}

impl Validator for TupleFixLenValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let seq = input.validate_tuple(extra.strict.unwrap_or(self.strict))?;
        let expected_length = self.items_validators.len();

        if expected_length != seq.generic_len() {
            return Err(ValError::new(
                ErrorKind::TupleLengthMismatch {
                    expected_length,
                    plural: expected_length != 1,
                },
                input,
            ));
        }
        let mut output: Vec<PyObject> = Vec::with_capacity(expected_length);
        let mut errors: Vec<ValLineError> = Vec::new();
        macro_rules! iter {
            ($sequence:expr) => {
                for (validator, (index, item)) in self.items_validators.iter().zip($sequence.iter().enumerate()) {
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
        match seq {
            GenericSequence::List(sequence) => iter!(sequence),
            GenericSequence::Tuple(sequence) => iter!(sequence),
            GenericSequence::Set(sequence) => iter!(sequence),
            GenericSequence::FrozenSet(sequence) => iter!(sequence),
            GenericSequence::JsonArray(sequence) => iter!(sequence),
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
