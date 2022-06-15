#![feature(no_coverage)]
#![feature(trait_upcasting)]
#![allow(clippy::borrow_deref_ref)]

extern crate core;
extern crate enum_dispatch;
extern crate indexmap;
extern crate pyo3;
extern crate regex;
extern crate serde;
extern crate serde_json;
extern crate strum;

use pyo3::create_exception;
use pyo3::exceptions::PyException;
use pyo3::prelude::*;

#[cfg(feature = "mimalloc")]
#[global_allocator]
static GLOBAL: mimalloc::MiMalloc = mimalloc::MiMalloc;

mod build_tools;
mod errors;
mod input;
mod validators;

// required for benchmarks
pub use validators::SchemaValidator;

create_exception!(_pydantic_core, SchemaError, PyException);

#[pymodule]
fn _pydantic_core(py: Python, m: &PyModule) -> PyResult<()> {
    let mut version = env!("CARGO_PKG_VERSION").to_string();
    // cargo uses "1.0-alpha1" etc. while python uses "1.0.0a1", this is not full compatibility,
    // but it's good enough for now
    // see https://docs.rs/semver/1.0.9/semver/struct.Version.html#method.parse for rust spec
    // see https://peps.python.org/pep-0440/ for python spec
    // it seems the dot after "alpha/beta" e.g. "-alpha.1" is not necessary, hence why this works
    version = version.replace("-alpha", "a").replace("-beta", "b");
    m.add("__version__", version)?;
    m.add("ValidationError", py.get_type::<errors::ValidationError>())?;
    m.add("SchemaError", py.get_type::<SchemaError>())?;
    m.add_class::<validators::SchemaValidator>()?;
    Ok(())
}
