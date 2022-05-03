use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::{is_strict, SchemaDict};
use crate::errors::{context, err_val_error, ErrorKind, InputValue, ValResult};
use crate::input::Input;

use super::{BuildValidator, CombinedValidator, Extra, SlotsBuilder, Validator};

#[derive(Debug, Clone)]
pub struct IntValidator;

impl BuildValidator for IntValidator {
    const EXPECTED_TYPE: &'static str = "int";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        _slots_builder: &mut SlotsBuilder,
    ) -> PyResult<CombinedValidator> {
        let use_constrained = schema.get_item("multiple_of").is_some()
            || schema.get_item("le").is_some()
            || schema.get_item("lt").is_some()
            || schema.get_item("ge").is_some()
            || schema.get_item("gt").is_some();
        if use_constrained {
            ConstrainedIntValidator::build(schema, config)
        } else if is_strict(schema, config)? {
            StrictIntValidator::build()
        } else {
            Ok(Self.into())
        }
    }
}

impl Validator for IntValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        Ok(input.lax_int()?.into_py(py))
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        Ok(input.strict_int()?.into_py(py))
    }

    fn get_name(&self, _py: Python) -> String {
        Self::EXPECTED_TYPE.to_string()
    }
}

#[derive(Debug, Clone)]
pub struct StrictIntValidator;

impl StrictIntValidator {
    fn build() -> PyResult<CombinedValidator> {
        Ok(Self.into())
    }
}

impl Validator for StrictIntValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        Ok(input.strict_int()?.into_py(py))
    }

    fn get_name(&self, _py: Python) -> String {
        "strict-int".to_string()
    }
}

#[derive(Debug, Clone)]
pub struct ConstrainedIntValidator {
    strict: bool,
    multiple_of: Option<i64>,
    le: Option<i64>,
    lt: Option<i64>,
    ge: Option<i64>,
    gt: Option<i64>,
}

impl Validator for ConstrainedIntValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        let int = match self.strict {
            true => input.strict_int()?,
            false => input.lax_int()?,
        };
        self._validation_logic(py, input, int)
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        self._validation_logic(py, input, input.strict_int()?)
    }

    fn get_name(&self, _py: Python) -> String {
        "constrained-int".to_string()
    }
}

impl ConstrainedIntValidator {
    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<CombinedValidator> {
        Ok(Self {
            strict: is_strict(schema, config)?,
            multiple_of: schema.get_as("multiple_of")?,
            le: schema.get_as("le")?,
            lt: schema.get_as("lt")?,
            ge: schema.get_as("ge")?,
            gt: schema.get_as("gt")?,
        }
        .into())
    }

    fn _validation_logic<'a>(&self, py: Python<'a>, input: &'a dyn Input, int: i64) -> ValResult<'a, PyObject> {
        if let Some(multiple_of) = self.multiple_of {
            if int % multiple_of != 0 {
                return err_val_error!(
                    input_value = InputValue::InputRef(input),
                    kind = ErrorKind::IntMultiple,
                    context = context!("multiple_of" => multiple_of)
                );
            }
        }
        if let Some(le) = self.le {
            if int > le {
                return err_val_error!(
                    input_value = InputValue::InputRef(input),
                    kind = ErrorKind::IntLessThanEqual,
                    context = context!("le" => le)
                );
            }
        }
        if let Some(lt) = self.lt {
            if int >= lt {
                return err_val_error!(
                    input_value = InputValue::InputRef(input),
                    kind = ErrorKind::IntLessThan,
                    context = context!("lt" => lt)
                );
            }
        }
        if let Some(ge) = self.ge {
            if int < ge {
                return err_val_error!(
                    input_value = InputValue::InputRef(input),
                    kind = ErrorKind::IntGreaterThanEqual,
                    context = context!("ge" => ge)
                );
            }
        }
        if let Some(gt) = self.gt {
            if int <= gt {
                return err_val_error!(
                    input_value = InputValue::InputRef(input),
                    kind = ErrorKind::IntGreaterThan,
                    context = context!("gt" => gt)
                );
            }
        }
        Ok(int.into_py(py))
    }
}
