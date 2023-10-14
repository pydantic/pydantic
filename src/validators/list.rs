use std::sync::OnceLock;

use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::errors::ValResult;
use crate::input::{GenericIterable, Input};
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
    schema: &PyDict,
    config: Option<&PyDict>,
    definitions: &mut DefinitionsBuilder<CombinedValidator>,
) -> PyResult<Option<CombinedValidator>> {
    match schema.get_item(pyo3::intern!(schema.py(), "items_schema"))? {
        Some(d) => {
            let validator = build_validator(d, config, definitions)?;
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
        schema: &PyDict,
        config: Option<&PyDict>,
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
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        let seq = input.validate_list(state.strict_or(self.strict))?;

        let output = match self.item_validator {
            Some(ref v) => seq.validate_to_vec(py, input, self.max_length, "List", v, state)?,
            None => match seq {
                GenericIterable::List(list) => {
                    length_check!(input, "List", self.min_length, self.max_length, list);
                    let list_copy = list.get_slice(0, usize::MAX);
                    return Ok(list_copy.into_py(py));
                }
                _ => seq.to_vec(py, input, "List", self.max_length)?,
            },
        };
        min_length_check!(input, "List", self.min_length, output);
        Ok(output.into_py(py))
    }

    fn different_strict_behavior(&self, ultra_strict: bool) -> bool {
        if ultra_strict {
            match self.item_validator {
                Some(ref v) => v.different_strict_behavior(true),
                None => false,
            }
        } else {
            true
        }
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

    fn complete(&self) -> PyResult<()> {
        if let Some(v) = &self.item_validator {
            v.complete()?;
        }
        Ok(())
    }
}
