use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_macros::{dict_get, is_strict};
use crate::errors::{context, err_val_error, ErrorKind, ValResult};
use crate::input::{Input, ToPy};

use super::{Extra, Validator};

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
        } else if is_strict!(schema, config) {
            StrictIntValidator::build(schema, config)
        } else {
            Ok(Box::new(Self))
        }
    }

    fn validate(&self, py: Python, input: &dyn Input, _extra: &Extra) -> ValResult<PyObject> {
        Ok(input.lax_int(py)?.into_py(py))
    }

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

    fn validate(&self, py: Python, input: &dyn Input, _extra: &Extra) -> ValResult<PyObject> {
        Ok(input.strict_int(py)?.into_py(py))
    }

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
            strict: is_strict!(schema, config),
            multiple_of: dict_get!(schema, "multiple_of", i64),
            le: dict_get!(schema, "le", i64),
            lt: dict_get!(schema, "lt", i64),
            ge: dict_get!(schema, "ge", i64),
            gt: dict_get!(schema, "gt", i64),
        }))
    }

    fn validate(&self, py: Python, input: &dyn Input, _extra: &Extra) -> ValResult<PyObject> {
        let int = match self.strict {
            true => input.strict_int(py)?,
            false => input.lax_int(py)?,
        };
        if let Some(multiple_of) = self.multiple_of {
            if int % multiple_of != 0 {
                return err_val_error!(
                    py,
                    int,
                    kind = ErrorKind::IntMultiple,
                    context = context!("multiple_of" => multiple_of)
                );
            }
        }
        if let Some(le) = self.le {
            if int > le {
                return err_val_error!(
                    py,
                    int,
                    kind = ErrorKind::IntLessThanEqual,
                    context = context!("le" => le)
                );
            }
        }
        if let Some(lt) = self.lt {
            if int >= lt {
                return err_val_error!(py, int, kind = ErrorKind::IntLessThan, context = context!("lt" => lt));
            }
        }
        if let Some(ge) = self.ge {
            if int < ge {
                return err_val_error!(
                    py,
                    int,
                    kind = ErrorKind::IntGreaterThanEqual,
                    context = context!("ge" => ge)
                );
            }
        }
        if let Some(gt) = self.gt {
            if int <= gt {
                return err_val_error!(
                    py,
                    int,
                    kind = ErrorKind::IntGreaterThan,
                    context = context!("gt" => gt)
                );
            }
        }
        Ok(int.into_py(py))
    }

    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}
