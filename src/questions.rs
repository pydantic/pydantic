use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::SchemaDict;

#[derive(Debug, PartialEq, Eq)]
pub enum Question {
    ReturnFieldsSet,
}

#[derive(Debug, Clone)]
pub struct Answers {
    return_fields_set: bool,
}

impl Answers {
    pub fn new(schema: &PyDict) -> PyResult<Self> {
        let key = intern!(schema.py(), "return_fields_set");
        let return_fields_set = schema.get_as(key)?.unwrap_or(false);
        Ok(Self { return_fields_set })
    }

    pub fn ask(&self, question: &Question) -> bool {
        match question {
            Question::ReturnFieldsSet => self.return_fields_set,
        }
    }
}
