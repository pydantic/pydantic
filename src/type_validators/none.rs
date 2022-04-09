use pyo3::prelude::*;
use pyo3::types::PyDict;

use super::TypeValidator;
use crate::errors::{ErrorKind, Location, ValLineError, ValResult};

#[derive(Debug, Clone)]
pub struct NoneValidator;

impl TypeValidator for NoneValidator {
    fn is_match(type_: &str, _dict: &PyDict) -> bool {
        type_ == "null"
    }

    fn build(_dict: &PyDict) -> PyResult<Self> {
        Ok(Self)
    }

    fn validate(&self, py: Python, obj: &PyAny, _loc: &Location) -> ValResult {
        if obj.is_none() {
            ValResult::Ok(obj.to_object(py))
        } else {
            ValResult::VErr(vec![ValLineError {
                kind: ErrorKind::NoneRequired,
                value: Some(obj.to_object(py)),
                ..Default::default()
            }])
        }
    }

    fn clone_dyn(&self) -> Box<dyn TypeValidator> {
        Box::new(self.clone())
    }
}
