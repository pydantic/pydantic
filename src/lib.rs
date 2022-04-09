extern crate pyo3;
extern crate regex;
extern crate strum;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::{create_exception, wrap_pyfunction};

mod errors;
mod standalone_validators;
mod type_validators;
mod utils;

const VERSION: &str = env!("CARGO_PKG_VERSION");

create_exception!(_pydantic_core, ValidationError, PyValueError);

#[pymodule]
fn _pydantic_core(py: Python, m: &PyModule) -> PyResult<()> {
    m.add("ValidationError", py.get_type::<ValidationError>())?;
    m.add("__version__", VERSION)?;
    m.add_wrapped(wrap_pyfunction!(standalone_validators::validate_str))?;
    m.add_class::<type_validators::SchemaValidator>()?;
    m.add_class::<errors::SubError>()?;
    Ok(())
}
