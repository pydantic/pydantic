use pyo3::prelude::*;
use pyo3::types::PyDict;
use pyo3::ToPyObject;

use super::{SchemaValidator, TypeValidator};
use crate::utils::{dict_get, py_error};

#[derive(Debug, Clone)]
struct ModelField {
    name: String,
    // alias: Option<String>,
    required: bool,
    validator: Box<SchemaValidator>,
}

#[derive(Debug, Clone)]
pub struct ModelValidator {
    fields: Vec<ModelField>,
}

impl TypeValidator for ModelValidator {
    fn is_match(type_: &str, _dict: &PyDict) -> bool {
        type_ == "model"
    }

    fn build(dict: &PyDict) -> PyResult<Self> {
        let fields_dict: &PyDict = match dict_get!(dict, "fields", &PyDict) {
            Some(fields) => fields,
            None => {
                // allow an empty model, is this is a good idea?
                return Ok(Self { fields: vec![] });
            }
        };
        let mut fields: Vec<ModelField> = Vec::with_capacity(fields_dict.len());

        for (key, value) in fields_dict.iter() {
            let field_dict: &PyDict = value.cast_as()?;

            fields.push(ModelField {
                name: key.to_string(),
                // alias: dict_get!(field_dict, "alias", String),
                required: dict_get!(field_dict, "required", bool).unwrap_or(false),
                validator: Box::new(SchemaValidator::build(field_dict)?),
            });
        }
        Ok(Self { fields })
    }

    fn validate(&self, py: Python, obj: PyObject) -> PyResult<PyObject> {
        let obj_dict: &PyDict = obj.cast_as(py)?;
        let output = PyDict::new(py);
        let mut errors = Vec::new();
        for field in &self.fields {
            if let Some(value) = obj_dict.get_item(field.name.clone()) {
                let value = field.validator.validate(py, value.to_object(py))?;
                output.set_item(field.name.clone(), value)?;
            } else if field.required {
                errors.push(format!("Missing field: {}", field.name));
            }
        }
        if errors.is_empty() {
            Ok(output.into())
        } else {
            py_error!("errors: {:?}", errors)
        }
    }

    fn clone_dyn(&self) -> Box<dyn TypeValidator> {
        Box::new(self.clone())
    }
}
