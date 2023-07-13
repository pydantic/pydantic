#![cfg_attr(has_no_coverage, feature(no_coverage))]

extern crate core;

use std::sync::OnceLock;

use pyo3::{prelude::*, sync::GILOnceCell};

#[cfg(feature = "mimalloc")]
#[global_allocator]
static GLOBAL: mimalloc::MiMalloc = mimalloc::MiMalloc;

mod argument_markers;
mod build_tools;
mod definitions;
mod errors;
mod input;
mod lazy_index_map;
mod lookup_key;
mod recursion_guard;
mod serializers;
mod tools;
mod url;
mod validators;

// required for benchmarks
pub use self::input::TzInfo;
pub use self::url::{PyMultiHostUrl, PyUrl};
pub use argument_markers::{ArgsKwargs, PydanticUndefinedType};
pub use build_tools::SchemaError;
pub use errors::{
    list_all_errors, PydanticCustomError, PydanticKnownError, PydanticOmit, PydanticUseDefault, ValidationError,
};
pub use serializers::{
    to_json, to_jsonable_python, PydanticSerializationError, PydanticSerializationUnexpectedValue, SchemaSerializer,
};
pub use validators::{PySome, SchemaValidator};

pub fn get_pydantic_core_version() -> &'static str {
    static PYDANTIC_CORE_VERSION: OnceLock<String> = OnceLock::new();

    PYDANTIC_CORE_VERSION.get_or_init(|| {
        let version = env!("CARGO_PKG_VERSION");
        // cargo uses "1.0-alpha1" etc. while python uses "1.0.0a1", this is not full compatibility,
        // but it's good enough for now
        // see https://docs.rs/semver/1.0.9/semver/struct.Version.html#method.parse for rust spec
        // see https://peps.python.org/pep-0440/ for python spec
        // it seems the dot after "alpha/beta" e.g. "-alpha.1" is not necessary, hence why this works
        version.replace("-alpha", "a").replace("-beta", "b")
    })
}

/// Returns the installed version of pydantic.
fn get_pydantic_version(py: Python<'_>) -> Option<&'static str> {
    static PYDANTIC_VERSION: GILOnceCell<Option<String>> = GILOnceCell::new();

    PYDANTIC_VERSION
        .get_or_init(py, || {
            py.import("pydantic")
                .and_then(|pydantic| pydantic.getattr("__version__")?.extract())
                .ok()
        })
        .as_deref()
}

pub fn build_info() -> String {
    format!(
        "profile={} pgo={} mimalloc={}",
        env!("PROFILE"),
        option_env!("RUSTFLAGS").unwrap_or("").contains("-Cprofile-use="),
        cfg!(feature = "mimalloc")
    )
}

#[pymodule]
fn _pydantic_core(py: Python, m: &PyModule) -> PyResult<()> {
    m.add("__version__", get_pydantic_core_version())?;
    m.add("build_profile", env!("PROFILE"))?;
    m.add("build_info", build_info())?;
    m.add("_recursion_limit", recursion_guard::RECURSION_GUARD_LIMIT)?;
    m.add("PydanticUndefined", PydanticUndefinedType::new(py))?;
    m.add_class::<PydanticUndefinedType>()?;
    m.add_class::<PySome>()?;
    m.add_class::<SchemaValidator>()?;
    m.add_class::<ValidationError>()?;
    m.add_class::<SchemaError>()?;
    m.add_class::<PydanticCustomError>()?;
    m.add_class::<PydanticKnownError>()?;
    m.add_class::<PydanticOmit>()?;
    m.add_class::<PydanticUseDefault>()?;
    m.add_class::<PydanticSerializationError>()?;
    m.add_class::<PydanticSerializationUnexpectedValue>()?;
    m.add_class::<PyUrl>()?;
    m.add_class::<PyMultiHostUrl>()?;
    m.add_class::<ArgsKwargs>()?;
    m.add_class::<SchemaSerializer>()?;
    m.add_class::<TzInfo>()?;
    m.add_function(wrap_pyfunction!(to_json, m)?)?;
    m.add_function(wrap_pyfunction!(to_jsonable_python, m)?)?;
    m.add_function(wrap_pyfunction!(list_all_errors, m)?)?;

    #[cfg(not(feature = "mimalloc"))]
    m.setattr("__pydantic_core_default_allocator__", true)?; // uses setattr so this is not in __all__

    Ok(())
}
