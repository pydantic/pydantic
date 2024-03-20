use std::sync::OnceLock;

use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::errors::ValResult;
use crate::input::{
    no_validator_iter_to_vec, validate_iter_to_vec, BorrowInput, ConsumeIterator, Input, MaxLengthCheck, ValidatedList,
};
use crate::tools::SchemaDict;

use super::{build_validator, BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

#[derive(Debug)]
pub struct ListValidator {
    strict: bool,
    item_validator: Option<Box<CombinedValidator>>,
    min_length: Option<usize>,
    max_length: Option<usize>,
    name: OnceLock<String>,
}

pub fn get_items_schema(
    schema: &Bound<'_, PyDict>,
    config: Option<&Bound<'_, PyDict>>,
    definitions: &mut DefinitionsBuilder<CombinedValidator>,
) -> PyResult<Option<CombinedValidator>> {
    match schema.get_item(pyo3::intern!(schema.py(), "items_schema"))? {
        Some(d) => {
            let validator = build_validator(&d, config, definitions)?;
            match validator {
                CombinedValidator::Any(_) => Ok(None),
                _ => Ok(Some(validator)),
            }
        }
        None => Ok(None),
    }
}

macro_rules! length_check {
    ($input:ident, $field_type:literal, $min_length:expr, $max_length:expr, $obj:ident) => {{
        let mut op_actual_length: Option<usize> = None;
        if let Some(min_length) = $min_length {
            let actual_length = $obj.len();
            if actual_length < min_length {
                return Err(crate::errors::ValError::new(
                    crate::errors::ErrorType::TooShort {
                        field_type: $field_type.to_string(),
                        min_length,
                        actual_length,
                        context: None,
                    },
                    $input,
                ));
            }
            op_actual_length = Some(actual_length);
        }
        if let Some(max_length) = $max_length {
            let actual_length = op_actual_length.unwrap_or_else(|| $obj.len());
            if actual_length > max_length {
                return Err(crate::errors::ValError::new(
                    crate::errors::ErrorType::TooLong {
                        field_type: $field_type.to_string(),
                        max_length,
                        actual_length: Some(actual_length),
                        context: None,
                    },
                    $input,
                ));
            }
        }
    }};
}
pub(crate) use length_check;

macro_rules! min_length_check {
    ($input:ident, $field_type:literal, $min_length:expr, $obj:ident) => {{
        if let Some(min_length) = $min_length {
            let actual_length = $obj.len();
            if actual_length < min_length {
                return Err(crate::errors::ValError::new(
                    crate::errors::ErrorType::TooShort {
                        field_type: $field_type.to_string(),
                        min_length,
                        actual_length,
                        context: None,
                    },
                    $input,
                ));
            }
        }
    }};
}
pub(crate) use min_length_check;

impl BuildValidator for ListValidator {
    const EXPECTED_TYPE: &'static str = "list";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let item_validator = get_items_schema(schema, config, definitions)?.map(Box::new);
        Ok(Self {
            strict: crate::build_tools::is_strict(schema, config)?,
            item_validator,
            min_length: schema.get_as(pyo3::intern!(py, "min_length"))?,
            max_length: schema.get_as(pyo3::intern!(py, "max_length"))?,
            name: OnceLock::new(),
        }
        .into())
    }
}

impl_py_gc_traverse!(ListValidator { item_validator });

impl Validator for ListValidator {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<PyObject> {
        let seq = input.validate_list(state.strict_or(self.strict))?.unpack(state);

        let actual_length = seq.len();
        let output = match self.item_validator {
            Some(ref v) => seq.iterate(ValidateToVec {
                py,
                input,
                actual_length,
                max_length: self.max_length,
                field_type: "List",
                item_validator: v,
                state,
            })??,
            None => {
                if let Some(py_list) = seq.as_py_list() {
                    length_check!(input, "List", self.min_length, self.max_length, py_list);
                    let list_copy = py_list.get_slice(0, usize::MAX);
                    return Ok(list_copy.into_py(py));
                }

                seq.iterate(ToVec {
                    py,
                    input,
                    actual_length,
                    max_length: self.max_length,
                    field_type: "List",
                })??
            }
        };
        min_length_check!(input, "List", self.min_length, output);
        Ok(output.into_py(py))
    }

    fn get_name(&self) -> &str {
        // The logic here is a little janky, it's done to try to cache the formatted name
        // while also trying to render definitions correctly when possible.
        //
        // Probably an opportunity for a future refactor
        match self.name.get() {
            Some(s) => s.as_str(),
            None => {
                let name = self.item_validator.as_ref().map_or("any", |v| v.get_name());
                if name == "..." {
                    // when inner name is not initialized yet, don't cache it here
                    "list[...]"
                } else {
                    self.name.get_or_init(|| format!("list[{name}]")).as_str()
                }
            }
        }
    }
}

struct ValidateToVec<'a, 's, 'py, I: Input<'py> + ?Sized> {
    py: Python<'py>,
    input: &'a I,
    actual_length: Option<usize>,
    max_length: Option<usize>,
    field_type: &'static str,
    item_validator: &'a CombinedValidator,
    state: &'a mut ValidationState<'s, 'py>,
}

// pretty arbitrary default capacity when creating vecs from iteration
const DEFAULT_CAPACITY: usize = 10;

impl<'py, T, I: Input<'py> + ?Sized> ConsumeIterator<PyResult<T>> for ValidateToVec<'_, '_, 'py, I>
where
    T: BorrowInput<'py>,
{
    type Output = ValResult<Vec<PyObject>>;
    fn consume_iterator(self, iterator: impl Iterator<Item = PyResult<T>>) -> ValResult<Vec<PyObject>> {
        let capacity = self.actual_length.unwrap_or(DEFAULT_CAPACITY);
        let max_length_check = MaxLengthCheck::new(self.max_length, self.field_type, self.input, self.actual_length);
        validate_iter_to_vec(
            self.py,
            iterator,
            capacity,
            max_length_check,
            self.item_validator,
            self.state,
        )
    }
}

struct ToVec<'a, 'py, I: Input<'py> + ?Sized> {
    py: Python<'py>,
    input: &'a I,
    actual_length: Option<usize>,
    max_length: Option<usize>,
    field_type: &'static str,
}

impl<'py, T, I: Input<'py> + ?Sized> ConsumeIterator<PyResult<T>> for ToVec<'_, 'py, I>
where
    T: BorrowInput<'py>,
{
    type Output = ValResult<Vec<PyObject>>;
    fn consume_iterator(self, iterator: impl Iterator<Item = PyResult<T>>) -> ValResult<Vec<PyObject>> {
        let max_length_check = MaxLengthCheck::new(self.max_length, self.field_type, self.input, self.actual_length);
        no_validator_iter_to_vec(self.py, self.input, iterator, max_length_check)
    }
}
