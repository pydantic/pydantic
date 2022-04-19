use pyo3::prelude::*;
use pyo3::types::PyDict;

use super::{Extra, Validator};
use crate::errors::{context, err_val_error, ErrorKind, ValResult};
use crate::input::{Input, ToPy};
use crate::utils::dict_get;

#[derive(Debug, Clone)]
pub struct FloatValidator;

impl FloatValidator {
    pub const EXPECTED_TYPE: &'static str = "float";
}

impl Validator for FloatValidator {
    fn build(_schema: &PyDict, _config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        Ok(Box::new(Self))
    }

    fn validate(&self, py: Python, input: &dyn Input, _extra: &Extra) -> ValResult<PyObject> {
        Ok(input.validate_float(py)?.into_py(py))
    }

    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}

#[derive(Debug, Clone)]
pub struct FloatConstrainedValidator {
    multiple_of: Option<f64>,
    le: Option<f64>,
    lt: Option<f64>,
    ge: Option<f64>,
    gt: Option<f64>,
}

impl FloatConstrainedValidator {
    pub const EXPECTED_TYPE: &'static str = "float-constrained";
}

impl Validator for FloatConstrainedValidator {
    fn build(schema: &PyDict, _config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        Ok(Box::new(Self {
            multiple_of: dict_get!(schema, "multiple_of", f64),
            le: dict_get!(schema, "le", f64),
            lt: dict_get!(schema, "lt", f64),
            ge: dict_get!(schema, "ge", f64),
            gt: dict_get!(schema, "gt", f64),
        }))
    }

    fn validate(&self, py: Python, input: &dyn Input, _extra: &Extra) -> ValResult<PyObject> {
        let float = input.validate_float(py)?;
        if let Some(multiple_of) = self.multiple_of {
            if float % multiple_of != 0.0 {
                return err_val_error!(
                    py,
                    float,
                    kind = ErrorKind::FloatMultiple,
                    context = context!("multiple_of" => multiple_of)
                );
            }
        }
        if let Some(le) = self.le {
            if float > le {
                return err_val_error!(
                    py,
                    float,
                    kind = ErrorKind::FloatLessThanEqual,
                    context = context!("le" => le)
                );
            }
        }
        if let Some(lt) = self.lt {
            if float >= lt {
                return err_val_error!(
                    py,
                    float,
                    kind = ErrorKind::FloatLessThan,
                    context = context!("lt" => lt)
                );
            }
        }
        if let Some(ge) = self.ge {
            if float < ge {
                return err_val_error!(
                    py,
                    float,
                    kind = ErrorKind::FloatGreaterThanEqual,
                    context = context!("ge" => ge)
                );
            }
        }
        if let Some(gt) = self.gt {
            if float <= gt {
                return err_val_error!(
                    py,
                    float,
                    kind = ErrorKind::FloatGreaterThan,
                    context = context!("gt" => gt)
                );
            }
        }
        Ok(float.into_py(py))
    }

    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}
