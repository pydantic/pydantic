use pyo3::prelude::*;
use pyo3::types::PyDict;

use super::TypeValidator;


#[derive(Debug, Clone)]
pub struct NoneValidator;

impl TypeValidator for NoneValidator {
    fn is_match(type_: &str, _dict: &PyDict) -> bool {
        type_ == "null"
    }

    fn build(_dict: &PyDict) -> PyResult<Self> {
        Ok(Self)
    }

    fn validate(&self, py: Python, _obj: PyObject) -> PyResult<PyObject> {
        Ok(py.None())
    }

    fn clone_dyn(&self) -> Box<dyn TypeValidator> {
        Box::new(self.clone())
    }
}
