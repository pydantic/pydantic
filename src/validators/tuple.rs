use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyTuple};

use crate::build_tools::{is_strict, py_error, SchemaDict};
use crate::errors::{context, err_val_error, ErrorKind, InputValue, LocItem, ValError, ValLineError};
use crate::input::{GenericSequence, Input, SequenceLenIter};

use super::{build_validator, BuildContext, BuildValidator, CombinedValidator, Extra, ValResult, Validator};

#[derive(Debug, Clone)]
pub struct TupleVarLenValidator {
    strict: bool,
    item_validator: Option<Box<CombinedValidator>>,
    min_items: Option<usize>,
    max_items: Option<usize>,
}

impl BuildValidator for TupleVarLenValidator {
    const EXPECTED_TYPE: &'static str = "tuple-var-len";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext,
    ) -> PyResult<CombinedValidator> {
        Ok(Self {
            strict: is_strict(schema, config)?,
            item_validator: match schema.get_item("items") {
                Some(d) => Some(Box::new(build_validator(d, config, build_context)?.0)),
                None => None,
            },
            min_items: schema.get_as("min_items")?,
            max_items: schema.get_as("max_items")?,
        }
        .into())
    }
}

impl Validator for TupleVarLenValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
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
        input: &'data dyn Input,
        extra: &Extra,
        slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        self._validation_logic(py, input, input.strict_tuple()?, extra, slots)
    }

    fn get_name(&self, py: Python) -> String {
        match &self.item_validator {
            Some(v) => format!("{}-{}", Self::EXPECTED_TYPE, v.get_name(py)),
            None => Self::EXPECTED_TYPE.to_string(),
        }
    }
}

impl TupleVarLenValidator {
    fn _validation_logic<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        tuple: GenericSequence<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        let length = tuple.generic_len();
        if let Some(min_length) = self.min_items {
            if length < min_length {
                return err_val_error!(
                    input_value = InputValue::InputRef(input),
                    kind = ErrorKind::TupleTooShort,
                    context = context!("min_length" => min_length)
                );
            }
        }
        if let Some(max_length) = self.max_items {
            if length > max_length {
                return err_val_error!(
                    input_value = InputValue::InputRef(input),
                    kind = ErrorKind::TupleTooLong,
                    context = context!("max_length" => max_length)
                );
            }
        }

        match self.item_validator {
            Some(ref validator) => {
                let mut output: Vec<PyObject> = Vec::with_capacity(length);
                let mut errors: Vec<ValLineError> = Vec::new();
                for (index, item) in tuple.generic_iter() {
                    match validator.validate(py, item, extra, slots) {
                        Ok(item) => output.push(item),
                        Err(ValError::LineErrors(line_errors)) => {
                            let loc = vec![LocItem::I(index)];
                            errors.extend(line_errors.into_iter().map(|err| err.with_prefix_location(&loc)));
                        }
                        Err(err) => return Err(err),
                    }
                }
                if errors.is_empty() {
                    Ok(PyTuple::new(py, &output).into_py(py))
                } else {
                    Err(ValError::LineErrors(errors))
                }
            }
            None => {
                let output: Vec<PyObject> = tuple.generic_iter().map(|(_, item)| item.to_py(py)).collect();
                Ok(PyTuple::new(py, &output).into_py(py))
            }
        }
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
        input: &'data dyn Input,
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
        input: &'data dyn Input,
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
        input: &'data dyn Input,
        tuple: GenericSequence<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        let expected_length = self.items_validators.len();

        if expected_length != tuple.generic_len() {
            let plural = if expected_length == 1 { "" } else { "s" };
            return err_val_error!(
                input_value = InputValue::InputRef(input),
                kind = ErrorKind::TupleLengthMismatch,
                // TODO fix Context::new so context! accepts different value types
                context = context!(
                    "expected_length" => expected_length.to_string(),
                    "plural" => plural.to_string(),
                )
            );
        }
        let mut output: Vec<PyObject> = Vec::with_capacity(expected_length);
        let mut errors: Vec<ValLineError> = Vec::new();

        for (validator, (index, item)) in self.items_validators.iter().zip(tuple.generic_iter()) {
            match validator.validate(py, item, extra, slots) {
                Ok(item) => output.push(item),
                Err(ValError::LineErrors(line_errors)) => {
                    let loc = vec![LocItem::I(index)];
                    errors.extend(line_errors.into_iter().map(|err| err.with_prefix_location(&loc)));
                }
                Err(err) => return Err(err),
            }
        }
        if errors.is_empty() {
            Ok(PyTuple::new(py, &output).into_py(py))
        } else {
            Err(ValError::LineErrors(errors))
        }
    }
}
