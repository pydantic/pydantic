use pyo3::prelude::*;
use pyo3::types::{PyBool, PyDict};

use super::TypeValidator;

#[derive(Debug, Clone)]
pub struct BoolValidator;

impl TypeValidator for BoolValidator {
    fn is_match(type_: &str, _dict: &PyDict) -> bool {
        type_ == "bool"
    }

    fn build(_dict: &PyDict) -> PyResult<Self> {
        Ok(Self)
    }

    fn validate(&self, py: Python, obj: PyObject) -> PyResult<PyObject> {
        let obj: &PyBool = obj.extract(py)?;
        Ok(obj.to_object(py))
    }

    fn clone_dyn(&self) -> Box<dyn TypeValidator> {
        Box::new(self.clone())
    }
}
