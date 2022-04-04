extern crate indexmap;
extern crate pyo3;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::{create_exception, wrap_pyfunction};

mod schema;

const VERSION: &str = env!("CARGO_PKG_VERSION");

create_exception!(_pydantic_core, PydanticParsingError, PyValueError);

#[pyfunction]
fn parse(py: Python, schema: PyObject, _obj: PyObject) -> PyResult<PyObject> {
    let schema_any: &PyAny = schema.extract(py)?;
    let schema = schema::SchemaDef::extract(schema_any)?;
    println!("schema: {:?}", schema);

    let msg = format!("{:?}", schema);
    Ok(msg.to_object(py))
}

#[pymodule]
fn _pydantic_core(py: Python, m: &PyModule) -> PyResult<()> {
    m.add("PydanticParsingError", py.get_type::<PydanticParsingError>())?;
    m.add("__version__", VERSION)?;
    m.add_wrapped(wrap_pyfunction!(parse))?;
    Ok(())
}
