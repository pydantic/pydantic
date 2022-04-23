use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_macros::{dict_get, is_strict};
use crate::errors::{context, err_val_error, ErrorKind, ValResult};
use crate::input::{Input, ToPy};

use super::{Extra, Validator};

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
        } else if is_strict!(schema, config) {
            StrictFloatValidator::build(schema, config)
        } else {
            Ok(Box::new(Self))
        }
    }

    fn validate(&self, py: Python, input: &dyn Input, _extra: &Extra) -> ValResult<PyObject> {
        Ok(input.lax_float(py)?.into_py(py))
    }

    fn validate_strict(&self, py: Python, input: &dyn Input, _extra: &Extra) -> ValResult<PyObject> {
        Ok(input.strict_float(py)?.into_py(py))
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
struct StrictFloatValidator;

impl Validator for StrictFloatValidator {
    fn build(_schema: &PyDict, _config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        Ok(Box::new(Self))
    }

    fn validate(&self, py: Python, input: &dyn Input, _extra: &Extra) -> ValResult<PyObject> {
        Ok(input.strict_float(py)?.into_py(py))
    }

    fn validate_strict(&self, py: Python, input: &dyn Input, extra: &Extra) -> ValResult<PyObject> {
        self.validate(py, input, extra)
    }

    fn get_name(&self, _py: Python) -> String {
        "strict-float".to_string()
    }

    #[no_coverage]
    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
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
            strict: is_strict!(schema, config),
            multiple_of: dict_get!(schema, "multiple_of", f64),
            le: dict_get!(schema, "le", f64),
            lt: dict_get!(schema, "lt", f64),
            ge: dict_get!(schema, "ge", f64),
            gt: dict_get!(schema, "gt", f64),
        }))
    }

    fn validate(&self, py: Python, input: &dyn Input, _extra: &Extra) -> ValResult<PyObject> {
        let float = match self.strict {
            true => input.strict_float(py)?,
            false => input.lax_float(py)?,
        };
        self._validation_logic(py, float)
    }

    fn validate_strict(&self, py: Python, input: &dyn Input, _extra: &Extra) -> ValResult<PyObject> {
        self._validation_logic(py, input.strict_float(py)?)
    }

    fn get_name(&self, _py: Python) -> String {
        "constrained-float".to_string()
    }

    #[no_coverage]
    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}

impl ConstrainedFloatValidator {
    fn _validation_logic(&self, py: Python, float: f64) -> ValResult<PyObject> {
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
}
