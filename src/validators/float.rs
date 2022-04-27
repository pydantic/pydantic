use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::{is_strict, SchemaDict};
use crate::errors::{context, err_val_error, ErrorKind, InputValue, ValResult};
use crate::input::Input;

use super::{validator_boilerplate, Extra, Validator, ValidatorArc};

#[derive(Debug, Clone)]
pub struct FloatValidator;

impl FloatValidator {
    pub const EXPECTED_TYPE: &'static str = "float";
}

impl Validator for FloatValidator {
    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        let use_constrained = schema.get_item("multiple_of").is_some()
            || schema.get_item("le").is_some()
            || schema.get_item("lt").is_some()
            || schema.get_item("ge").is_some()
            || schema.get_item("gt").is_some();
        if use_constrained {
            ConstrainedFloatValidator::build(schema, config)
        } else if is_strict(schema, config)? {
            StrictFloatValidator::build(schema, config)
        } else {
            Ok(Box::new(Self))
        }
    }

    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        Ok(input.lax_float(py)?.into_py(py))
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        Ok(input.strict_float(py)?.into_py(py))
    }

    validator_boilerplate!(Self::EXPECTED_TYPE);
}

#[derive(Debug, Clone)]
struct StrictFloatValidator;

impl Validator for StrictFloatValidator {
    fn build(_schema: &PyDict, _config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        Ok(Box::new(Self))
    }

    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        Ok(input.strict_float(py)?.into_py(py))
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        self.validate(py, input, extra)
    }

    validator_boilerplate!("strict-float");
}

#[derive(Debug, Clone)]
struct ConstrainedFloatValidator {
    strict: bool,
    multiple_of: Option<f64>,
    le: Option<f64>,
    lt: Option<f64>,
    ge: Option<f64>,
    gt: Option<f64>,
}

impl Validator for ConstrainedFloatValidator {
    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        Ok(Box::new(Self {
            strict: is_strict(schema, config)?,
            multiple_of: schema.get_as("multiple_of")?,
            le: schema.get_as("le")?,
            lt: schema.get_as("lt")?,
            ge: schema.get_as("ge")?,
            gt: schema.get_as("gt")?,
        }))
    }

    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        let float = match self.strict {
            true => input.strict_float(py)?,
            false => input.lax_float(py)?,
        };
        self._validation_logic(py, input, float)
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        self._validation_logic(py, input, input.strict_float(py)?)
    }

    validator_boilerplate!("constrained-float");
}

impl ConstrainedFloatValidator {
    fn _validation_logic<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        float: f64,
    ) -> ValResult<'data, PyObject> {
        if let Some(multiple_of) = self.multiple_of {
            if float % multiple_of != 0.0 {
                return err_val_error!(
                    input_value = InputValue::InputRef(input),
                    kind = ErrorKind::FloatMultiple,
                    context = context!("multiple_of" => multiple_of)
                );
            }
        }
        if let Some(le) = self.le {
            if float > le {
                return err_val_error!(
                    input_value = InputValue::InputRef(input),
                    kind = ErrorKind::FloatLessThanEqual,
                    context = context!("le" => le)
                );
            }
        }
        if let Some(lt) = self.lt {
            if float >= lt {
                return err_val_error!(
                    input_value = InputValue::InputRef(input),
                    kind = ErrorKind::FloatLessThan,
                    context = context!("lt" => lt)
                );
            }
        }
        if let Some(ge) = self.ge {
            if float < ge {
                return err_val_error!(
                    input_value = InputValue::InputRef(input),
                    kind = ErrorKind::FloatGreaterThanEqual,
                    context = context!("ge" => ge)
                );
            }
        }
        if let Some(gt) = self.gt {
            if float <= gt {
                return err_val_error!(
                    input_value = InputValue::InputRef(input),
                    kind = ErrorKind::FloatGreaterThan,
                    context = context!("gt" => gt)
                );
            }
        }
        Ok(float.into_py(py))
    }
}
