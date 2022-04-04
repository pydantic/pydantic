extern crate pyo3;

use pyo3::exceptions::{PyNotImplementedError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict};
use pyo3::{create_exception, wrap_pyfunction};

mod schema;

use schema::Schema;

const VERSION: &str = env!("CARGO_PKG_VERSION");

create_exception!(_pydantic_core, ValidationError, PyValueError);

fn parse_obj(py: Python, schema: Schema, obj: &PyAny) -> PyResult<PyObject> {
    match schema {
        Schema::Object {
            properties,
            additional_properties: _,
            min_properties: _,
            max_properties: _,
        } => {
            let obj_dict = <PyDict as PyTryFrom>::try_from(obj)?;
            let new_obj = PyDict::new(py);
            let mut errors = Vec::new();
            for property in properties {
                if let Some(value) = obj_dict.get_item(property.key.clone()) {
                    // let value = value.extract(py)?;
                    let value = parse_obj(py, property.schema, value)?;
                    new_obj.set_item(property.key, value)?;
                } else if property.required {
                    errors.push(format!("Missing property: {}", property.key));
                }
            }
            if errors.is_empty() {
                Ok(new_obj.into())
            } else {
                Err(ValidationError::new_err(errors))
            }
        }
        Schema::String {
            min_length,
            max_length,
            enum_: _,
            const_: _,
            pattern: _,
        } => {
            let s = String::extract(obj)?;
            if let Some(min_length) = min_length {
                if s.len() < min_length {
                    return Err(ValidationError::new_err(format!(
                        "String is too short (min length: {})",
                        min_length
                    )));
                }
            }
            if let Some(max_length) = max_length {
                if s.len() > max_length {
                    return Err(ValidationError::new_err(format!(
                        "String is too long (max length: {})",
                        max_length
                    )));
                }
            }
            Ok(s.to_object(py))
        }
        _ => Err(PyNotImplementedError::new_err(format!("TODO: {:?}", schema))),
    }
}

#[pyfunction]
fn parse(py: Python, schema: PyObject, obj: PyObject) -> PyResult<PyObject> {
    let schema: &PyAny = schema.extract(py)?;
    let schema = Schema::extract(schema)?;
    //
    let obj: &PyAny = obj.extract(py)?;
    parse_obj(py, schema, obj)

    // let msg = format!("{:#?}", schema);
    // Ok(msg.to_object(py))
}

#[pymodule]
fn _pydantic_core(py: Python, m: &PyModule) -> PyResult<()> {
    m.add("ValidationError", py.get_type::<ValidationError>())?;
    m.add("__version__", VERSION)?;
    m.add_wrapped(wrap_pyfunction!(parse))?;
    Ok(())
}
