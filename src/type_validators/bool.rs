use pyo3::prelude::*;
use pyo3::types::{PyBool, PyDict};

use super::TypeValidator;
use crate::errors::{ErrorKind, Location, ValLineError, ValResult};

#[derive(Debug, Clone)]
pub struct BoolValidator;

impl TypeValidator for BoolValidator {
    fn is_match(type_: &str, _dict: &PyDict) -> bool {
        type_ == "bool"
    }

    fn build(_dict: &PyDict) -> PyResult<Self> {
        Ok(Self)
    }

    fn validate(&self, py: Python, obj: &PyAny, _loc: &Location) -> ValResult {
        let obj: &PyBool = match obj.extract() {
            Ok(obj) => obj,
            Err(_e) => {
                return ValResult::VErr(vec![ValLineError {
                    kind: ErrorKind::Bool,
                    value: Some(obj.to_object(py)),
                    ..Default::default()
                }])
            }
        };
        ValResult::Ok(obj.to_object(py))
    }

    fn clone_dyn(&self) -> Box<dyn TypeValidator> {
        Box::new(self.clone())
    }
}
