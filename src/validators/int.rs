use pyo3::prelude::*;
use pyo3::types::PyDict;

use super::Validator;
use crate::errors::{context, err_val_error, ErrorKind, ValResult};
use crate::standalone_validators::validate_int;
use crate::utils::dict_get;

#[derive(Debug, Clone)]
pub struct IntValidator;

impl Validator for IntValidator {
    fn is_match(type_: &str, _dict: &PyDict) -> bool {
        type_ == "int"
    }

    fn build(_dict: &PyDict) -> PyResult<Self> {
        Ok(Self)
    }

    fn validate(&self, py: Python, input: &PyAny, _data: &PyDict) -> ValResult<PyObject> {
        Ok(validate_int(py, input)?.into_py(py))
    }

    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}

#[derive(Debug, Clone)]
pub struct IntConstrainedValidator {
    multiple_of: Option<i64>,
    le: Option<i64>,
    lt: Option<i64>,
    ge: Option<i64>,
    gt: Option<i64>,
}

impl Validator for IntConstrainedValidator {
    fn is_match(type_: &str, _dict: &PyDict) -> bool {
        type_ == "int-constrained"
    }

    fn build(dict: &PyDict) -> PyResult<Self> {
        Ok(Self {
            multiple_of: dict_get!(dict, "multiple_of", i64),
            le: dict_get!(dict, "le", i64),
            lt: dict_get!(dict, "lt", i64),
            ge: dict_get!(dict, "ge", i64),
            gt: dict_get!(dict, "gt", i64),
        })
    }

    fn validate(&self, py: Python, input: &PyAny, _data: &PyDict) -> ValResult<PyObject> {
        let int = validate_int(py, input)?;
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
