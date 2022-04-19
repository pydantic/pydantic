extern crate core;
extern crate lazy_static;
extern crate pyo3;
extern crate regex;
extern crate serde_json;
extern crate strum;

use pyo3::create_exception;
use pyo3::exceptions::PyException;
use pyo3::prelude::*;

mod errors;
mod input;
mod utils;
mod validators;

create_exception!(_pydantic_core, SchemaError, PyException);

const VERSION: &str = env!("CARGO_PKG_VERSION");

#[pymodule]
fn _pydantic_core(py: Python, m: &PyModule) -> PyResult<()> {
    m.add("ValidationError", py.get_type::<errors::ValidationError>())?;
    m.add("SchemaError", py.get_type::<SchemaError>())?;
    m.add("__version__", VERSION)?;
    m.add_class::<validators::SchemaValidator>()?;
    Ok(())
}
