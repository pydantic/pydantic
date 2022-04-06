extern crate pyo3;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::{create_exception, wrap_pyfunction};

mod core;
mod validators;

const VERSION: &str = env!("CARGO_PKG_VERSION");

create_exception!(_pydantic_core, ValidationError, PyValueError);

#[pymodule]
fn _pydantic_core(py: Python, m: &PyModule) -> PyResult<()> {
    m.add("ValidationError", py.get_type::<ValidationError>())?;
    m.add("__version__", VERSION)?;
    m.add_wrapped(wrap_pyfunction!(validators::validate_str))?;
    m.add_wrapped(wrap_pyfunction!(validators::validate_str_full))?;
    m.add_wrapped(wrap_pyfunction!(validators::validate_str_recursive))?;
    m.add_class::<core::SchemaValidator>()?;
    Ok(())
}
