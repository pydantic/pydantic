use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyTuple};

use crate::build_tools::{is_strict, py_error, SchemaDict};
use crate::errors::{context, err_val_error, ErrorKind, LocItem, ValError, ValLineError};
use crate::input::{GenericSequence, Input};

use super::any::AnyValidator;
use super::list::sequence_build_function;
use super::{build_validator, BuildContext, BuildValidator, CombinedValidator, Extra, ValResult, Validator};

#[derive(Debug, Clone)]
pub struct TupleVarLenValidator {
    strict: bool,
    item_validator: Box<CombinedValidator>,
    min_items: Option<usize>,
    max_items: Option<usize>,
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
    ) -> ValResult<'data, PyObject> {
        let tuple = match self.strict {
            true => input.strict_tuple()?,
            false => input.lax_tuple()?,
        };
        self._validation_logic(py, input, tuple, extra, slots)
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        self._validation_logic(py, input, input.strict_tuple()?, extra, slots)
    }

    fn get_name(&self, py: Python) -> String {
        format!("{}-{}", Self::EXPECTED_TYPE, self.item_validator.get_name(py))
    }
}

impl TupleVarLenValidator {
    fn _validation_logic<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        tuple: GenericSequence<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        let length = tuple.generic_len();
        if let Some(min_length) = self.min_items {
            if length < min_length {
                return err_val_error!(
                    input_value = input.as_error_value(),
                    kind = ErrorKind::TooShort,
                    context = context!("type" => "Tuple", "min_length" => min_length)
                );
            }
        }
        if let Some(max_length) = self.max_items {
            if length > max_length {
                return err_val_error!(
                    input_value = input.as_error_value(),
                    kind = ErrorKind::TooLong,
                    context = context!("type" => "Tuple", "max_length" => max_length)
                );
            }
        }

        let output = tuple.validate_to_vec(py, length, &self.item_validator, extra, slots)?;
        Ok(PyTuple::new(py, &output).into_py(py))
    }
}

#[derive(Debug, Clone)]
pub struct TupleFixLenValidator {
    strict: bool,
    items_validators: Vec<CombinedValidator>,
}

impl BuildValidator for TupleFixLenValidator {
    const EXPECTED_TYPE: &'static str = "tuple-fix-len";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext,
    ) -> PyResult<CombinedValidator> {
        let items: &PyList = schema.get_as_req("items")?;
        if items.is_empty() {
            return py_error!("Missing schemas for tuple elements");
        }
        let validators: Vec<CombinedValidator> = items
            .iter()
            .map(|item| build_validator(item, config, build_context).map(|result| result.0))
            .collect::<PyResult<Vec<CombinedValidator>>>()?;

        Ok(Self {
            strict: is_strict(schema, config)?,
            items_validators: validators,
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
    ) -> ValResult<'data, PyObject> {
        let tuple = match self.strict {
            true => input.strict_tuple()?,
            false => input.lax_tuple()?,
        };
        self._validation_logic(py, input, tuple, extra, slots)
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        self._validation_logic(py, input, input.strict_tuple()?, extra, slots)
    }

    fn get_name(&self, _py: Python) -> String {
        format!("{}-{}-items", Self::EXPECTED_TYPE, self.items_validators.len())
    }
}

impl TupleFixLenValidator {
    fn _validation_logic<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        tuple: GenericSequence<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        let expected_length = self.items_validators.len();

        if expected_length != tuple.generic_len() {
            let plural = if expected_length == 1 { "" } else { "s" };
            return err_val_error!(
                input_value = input.as_error_value(),
                kind = ErrorKind::TupleLengthMismatch,
                // TODO fix Context::new so context! accepts different value types
                context = context!(
                    "expected_length" => expected_length,
                    "plural" => plural.to_string(),
                )
            );
        }
        let mut output: Vec<PyObject> = Vec::with_capacity(expected_length);
        let mut errors: Vec<ValLineError> = Vec::new();
        macro_rules! iter {
            ($sequence:expr) => {
                for (validator, (index, item)) in self.items_validators.iter().zip($sequence.iter().enumerate()) {
                    match validator.validate(py, item, extra, slots) {
                        Ok(item) => output.push(item),
                        Err(ValError::LineErrors(line_errors)) => {
                            let loc = vec![LocItem::I(index)];
                            errors.extend(line_errors.into_iter().map(|err| err.with_prefix_location(&loc)));
                        }
                        Err(err) => return Err(err),
                    }
                }
            };
        }
        match tuple {
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
}
