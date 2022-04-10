use pyo3::prelude::*;
use pyo3::types::PyDict;

use super::TypeValidator;
use crate::errors::{err_val_error, ErrorKind, ValResult};
use crate::standalone_validators::validate_float;
use crate::utils::{dict_create, dict_get};

#[derive(Debug, Clone)]
pub struct SimpleFloatValidator;

impl TypeValidator for SimpleFloatValidator {
    fn is_match(type_: &str, dict: &PyDict) -> bool {
        type_ == "float"
            && dict.get_item("multiple_of").is_none()
            && dict.get_item("le").is_none()
            && dict.get_item("lt").is_none()
            && dict.get_item("ge").is_none()
            && dict.get_item("gt").is_none()
    }

    fn build(_dict: &PyDict) -> PyResult<Self> {
        Ok(Self)
    }

    fn validate(&self, py: Python, obj: &PyAny) -> ValResult<PyObject> {
        Ok(validate_float(py, obj)?.to_object(py))
    }

    fn clone_dyn(&self) -> Box<dyn TypeValidator> {
        Box::new(self.clone())
    }
}

#[derive(Debug, Clone)]
pub struct FullFloatValidator {
    multiple_of: Option<f64>,
    le: Option<f64>,
    lt: Option<f64>,
    ge: Option<f64>,
    gt: Option<f64>,
}

impl TypeValidator for FullFloatValidator {
    fn is_match(type_: &str, _dict: &PyDict) -> bool {
        type_ == "int"
    }

    fn build(dict: &PyDict) -> PyResult<Self> {
        Ok(Self {
            multiple_of: dict_get!(dict, "multiple_of", f64),
            le: dict_get!(dict, "le", f64),
            lt: dict_get!(dict, "lt", f64),
            ge: dict_get!(dict, "ge", f64),
            gt: dict_get!(dict, "gt", f64),
        })
    }

    fn validate(&self, py: Python, obj: &PyAny) -> ValResult<PyObject> {
        let float = validate_float(py, obj)?;
        if let Some(multiple_of) = self.multiple_of {
            if float % multiple_of != 0.0 {
                return err_val_error!(
                    py,
                    float,
                    kind = ErrorKind::FloatMultiple,
                    context = Some(dict_create!(py, "multiple_of" => multiple_of))
                );
            }
        }
        if let Some(le) = self.le {
            if float > le {
                return err_val_error!(
                    py,
                    float,
                    kind = ErrorKind::FloatLessThanEqual,
                    context = Some(dict_create!(py, "le" => le))
                );
            }
        }
        if let Some(lt) = self.lt {
            if float >= lt {
                return err_val_error!(
                    py,
                    float,
                    kind = ErrorKind::FloatLessThan,
                    context = Some(dict_create!(py, "lt" => lt))
                );
            }
        }
        if let Some(ge) = self.ge {
            if float < ge {
                return err_val_error!(
                    py,
                    float,
                    kind = ErrorKind::FloatGreaterThanEqual,
                    context = Some(dict_create!(py, "ge" => ge))
                );
            }
        }
        if let Some(gt) = self.gt {
            if float <= gt {
                return err_val_error!(
                    py,
                    float,
                    kind = ErrorKind::FloatGreaterThan,
                    context = Some(dict_create!(py, "gt" => gt))
                );
            }
        }
        Ok(float.to_object(py))
    }

    fn clone_dyn(&self) -> Box<dyn TypeValidator> {
        Box::new(self.clone())
    }
}
