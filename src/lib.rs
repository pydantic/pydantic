#![cfg_attr(has_no_coverage, feature(no_coverage))]
#![allow(clippy::borrow_deref_ref)]

extern crate core;

use pyo3::prelude::*;

#[cfg(feature = "mimalloc")]
#[global_allocator]
static GLOBAL: mimalloc::MiMalloc = mimalloc::MiMalloc;

mod build_context;
mod build_tools;
mod errors;
mod input;
mod lookup_key;
mod questions;
mod recursion_guard;
mod serializers;
mod url;
mod validators;

// required for benchmarks
pub use self::url::{PyMultiHostUrl, PyUrl};
pub use build_tools::SchemaError;
pub use errors::{list_all_errors, PydanticCustomError, PydanticKnownError, PydanticOmit, ValidationError};
pub use serializers::{to_json, PydanticSerializationError, PydanticSerializationUnexpectedValue, SchemaSerializer};
pub use validators::SchemaValidator;

pub fn get_version() -> String {
    let version = env!("CARGO_PKG_VERSION").to_string();
    // cargo uses "1.0-alpha1" etc. while python uses "1.0.0a1", this is not full compatibility,
    // but it's good enough for now
    // see https://docs.rs/semver/1.0.9/semver/struct.Version.html#method.parse for rust spec
    // see https://peps.python.org/pep-0440/ for python spec
    // it seems the dot after "alpha/beta" e.g. "-alpha.1" is not necessary, hence why this works
    version.replace("-alpha", "a").replace("-beta", "b")
}

#[pymodule]
fn _pydantic_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add("__version__", get_version())?;
    m.add("build_profile", env!("PROFILE"))?;
    m.add_class::<SchemaValidator>()?;
    m.add_class::<ValidationError>()?;
    m.add_class::<SchemaError>()?;
    m.add_class::<PydanticCustomError>()?;
    m.add_class::<PydanticKnownError>()?;
    m.add_class::<PydanticOmit>()?;
    m.add_class::<PydanticSerializationError>()?;
    m.add_class::<PydanticSerializationUnexpectedValue>()?;
    m.add_class::<PyUrl>()?;
    m.add_class::<PyMultiHostUrl>()?;
    m.add_class::<SchemaSerializer>()?;
    m.add_function(wrap_pyfunction!(to_json, m)?)?;
    m.add_function(wrap_pyfunction!(list_all_errors, m)?)?;
    Ok(())
}
