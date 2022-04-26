use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::{is_strict, SchemaDict};
use crate::errors::{context, err_val_error, ErrorKind, InputValue, ValResult};
use crate::input::Input;

use super::{Extra, Validator, ValidatorArc};

#[derive(Debug, Clone)]
pub struct IntValidator;

impl IntValidator {
    pub const EXPECTED_TYPE: &'static str = "int";
}

impl Validator for IntValidator {
    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        let use_constrained = schema.get_item("multiple_of").is_some()
            || schema.get_item("le").is_some()
            || schema.get_item("lt").is_some()
            || schema.get_item("ge").is_some()
            || schema.get_item("gt").is_some();
        if use_constrained {
            ConstrainedIntValidator::build(schema, config)
        } else if is_strict(schema, config)? {
            StrictIntValidator::build(schema, config)
        } else {
            Ok(Box::new(Self))
        }
    }

    fn set_ref(&mut self, _name: &str, _validator_arc: &ValidatorArc) -> PyResult<()> {
        Ok(())
    }

    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        Ok(input.lax_int(py)?.into_py(py))
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        Ok(input.strict_int(py)?.into_py(py))
    }

    fn get_name(&self, _py: Python) -> String {
        Self::EXPECTED_TYPE.to_string()
    }

    #[no_coverage]
    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}

#[derive(Debug, Clone)]
struct StrictIntValidator;

impl Validator for StrictIntValidator {
    fn build(_schema: &PyDict, _config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        Ok(Box::new(Self))
    }

    fn set_ref(&mut self, _name: &str, _validator_arc: &ValidatorArc) -> PyResult<()> {
        Ok(())
    }

    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        Ok(input.strict_int(py)?.into_py(py))
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        self.validate(py, input, extra)
    }

    fn get_name(&self, _py: Python) -> String {
        "strict-int".to_string()
    }

    #[no_coverage]
    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}

#[derive(Debug, Clone)]
struct ConstrainedIntValidator {
    strict: bool,
    multiple_of: Option<i64>,
    le: Option<i64>,
    lt: Option<i64>,
    ge: Option<i64>,
    gt: Option<i64>,
}

impl Validator for ConstrainedIntValidator {
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

    fn set_ref(&mut self, _name: &str, _validator_arc: &ValidatorArc) -> PyResult<()> {
        Ok(())
    }

    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        let int = match self.strict {
            true => input.strict_int(py)?,
            false => input.lax_int(py)?,
        };
        self._validation_logic(py, input, int)
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        self._validation_logic(py, input, input.strict_int(py)?)
    }

    fn get_name(&self, _py: Python) -> String {
        "constrained-int".to_string()
    }

    #[no_coverage]
    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}

impl ConstrainedIntValidator {
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
