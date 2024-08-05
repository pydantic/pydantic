#![cfg_attr(has_coverage_attribute, feature(coverage_attribute))]

extern crate core;

use std::sync::OnceLock;

use jiter::{map_json_error, PartialMode, PythonParse, StringCacheMode};
use pyo3::exceptions::PyTypeError;
use pyo3::{prelude::*, sync::GILOnceCell};
use serializers::BytesMode;
use validators::ValBytesMode;

// parse this first to get access to the contained macro
#[macro_use]
mod py_gc;

mod argument_markers;
mod build_tools;
mod definitions;
mod errors;
mod input;
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
    WarningsArg,
};
pub use validators::{validate_core_schema, PySome, SchemaValidator};

use crate::input::Input;

#[pyfunction(signature = (data, *, allow_inf_nan=true, cache_strings=StringCacheMode::All, allow_partial=PartialMode::Off))]
pub fn from_json<'py>(
    py: Python<'py>,
    data: &Bound<'_, PyAny>,
    allow_inf_nan: bool,
    cache_strings: StringCacheMode,
    allow_partial: PartialMode,
) -> PyResult<Bound<'py, PyAny>> {
    let v_match = data
        .validate_bytes(false, ValBytesMode { ser: BytesMode::Utf8 })
        .map_err(|_| PyTypeError::new_err("Expected bytes, bytearray or str"))?;
    let json_either_bytes = v_match.into_inner();
    let json_bytes = json_either_bytes.as_slice();
    let parse_builder = PythonParse {
        allow_inf_nan,
        cache_mode: cache_strings,
        partial_mode: allow_partial,
        catch_duplicate_keys: false,
        lossless_floats: false,
    };
    parse_builder
        .python_parse(py, json_bytes)
        .map_err(|e| map_json_error(json_bytes, &e))
}

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
            py.import_bound("pydantic")
                .and_then(|pydantic| pydantic.getattr("__version__")?.extract())
                .ok()
        })
        .as_deref()
}

pub fn build_info() -> String {
    format!(
        "profile={} pgo={}",
        env!("PROFILE"),
        option_env!("RUSTFLAGS").unwrap_or("").contains("-Cprofile-use="),
    )
}

#[pymodule]
fn _pydantic_core(py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
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
    m.add_function(wrap_pyfunction!(from_json, m)?)?;
    m.add_function(wrap_pyfunction!(to_jsonable_python, m)?)?;
    m.add_function(wrap_pyfunction!(list_all_errors, m)?)?;
    m.add_function(wrap_pyfunction!(validate_core_schema, m)?)?;
    Ok(())
}
