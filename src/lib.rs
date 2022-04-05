extern crate pyo3;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
// use pyo3::types::{PyAny, PyFunction};
use pyo3::{create_exception, wrap_pyfunction};

mod core;

const VERSION: &str = env!("CARGO_PKG_VERSION");

create_exception!(_pydantic_core, ValidationError, PyValueError);

#[pyfunction]
fn parse(py: Python, _schema: PyObject, _obj: PyObject) -> PyResult<PyObject> {
    Ok("foobar".to_object(py))
    // let schema: &PyAny = schema.extract(py)?;
    // let schema = core::Schema::extract(schema)?;
    // //
    // let obj: &PyAny = obj.extract(py)?;
    // core::parse(py, &schema, obj)

    // let msg = format!("{:#?}", schema);
    // Ok(msg.to_object(py))
}

#[pymodule]
fn _pydantic_core(py: Python, m: &PyModule) -> PyResult<()> {
    m.add("ValidationError", py.get_type::<ValidationError>())?;
    m.add("__version__", VERSION)?;
    m.add_wrapped(wrap_pyfunction!(parse))?;
    m.add_class::<core::SchemaValidator>()?;
    Ok(())
}
