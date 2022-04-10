extern crate lazy_static;
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

create_exception!(_pydantic_core, SchemaError, PyValueError);

const VERSION: &str = env!("CARGO_PKG_VERSION");

#[pymodule]
fn _pydantic_core(py: Python, m: &PyModule) -> PyResult<()> {
    m.add("ValidationError", py.get_type::<errors::ValidationError>())?;
    m.add("SchemaError", py.get_type::<SchemaError>())?;
    m.add("__version__", VERSION)?;
    m.add_wrapped(wrap_pyfunction!(standalone_validators::validate_str_py))?;
    m.add_class::<type_validators::SchemaValidator>()?;
    Ok(())
}
