#![cfg_attr(has_coverage_attribute, feature(coverage_attribute))]

extern crate core;

use std::sync::OnceLock;

use jiter::{FloatMode, PartialMode, PythonParse, StringCacheMode, map_json_error};
use pyo3::exceptions::PyTypeError;
use pyo3::{prelude::*, sync::PyOnceLock};
use serializers::BytesMode;
use validators::ValBytesMode;

// parse this first to get access to the contained macro
#[macro_use]
mod py_gc;

mod argument_markers;
mod build_tools;
mod common;
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
    PydanticCustomError, PydanticKnownError, PydanticOmit, PydanticUseDefault, ValidationError, list_all_errors,
};
pub use serializers::{
    PydanticSerializationError, PydanticSerializationUnexpectedValue, SchemaSerializer, WarningsArg, to_json,
    to_jsonable_python,
};
pub use validators::{PySome, SchemaValidator};

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
        float_mode: FloatMode::Float,
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
    static PYDANTIC_VERSION: PyOnceLock<Option<String>> = PyOnceLock::new();

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
        "profile={} pgo={}",
        env!("PROFILE"),
        // We use a `cfg!` here not `env!`/`option_env!` as those would
        // embed `RUSTFLAGS` into the generated binary which causes problems
        // with reproducible builds.
        cfg!(specified_profile_use),
    )
}

#[pymodule(gil_used = false)]
pub mod _pydantic_core {
    #[allow(clippy::wildcard_imports)]
    use super::*;

    #[pymodule_export]
    use crate::{
        ArgsKwargs, PyMultiHostUrl, PySome, PyUrl, PydanticCustomError, PydanticKnownError, PydanticOmit,
        PydanticSerializationError, PydanticSerializationUnexpectedValue, PydanticUndefinedType, PydanticUseDefault,
        SchemaError, SchemaSerializer, SchemaValidator, TzInfo, ValidationError, from_json, list_all_errors, to_json,
        to_jsonable_python,
    };

    #[pymodule_init]
    fn module_init(m: &Bound<'_, PyModule>) -> PyResult<()> {
        m.add("__version__", get_pydantic_core_version())?;
        m.add("build_profile", env!("PROFILE"))?;
        m.add("build_info", build_info())?;
        m.add("_recursion_limit", recursion_guard::RECURSION_GUARD_LIMIT)?;
        m.add("PydanticUndefined", PydanticUndefinedType::get(m.py()))?;
        // ---------------------------------------------------------------------------
        // Fix for pydantic_core.TzInfo shutdown SIGSEGV (pydantic#12867)
        //
        // The Rust TzInfo struct has no C-level `extends = PyTzInfo` so its tp_base
        // chain is simply `object`.  Here we create a Python-level class that inherits
        // from *both* the Rust-backed TzInfo *and* `datetime.tzinfo`:
        //
        //   class TzInfo(RustTzInfo, datetime.tzinfo): pass
        //
        // This gives instances the correct MRO so that PyTZInfo_Check still passes
        // (datetime.tzinfo is in the MRO), while tp_base stays as RustTzInfo (the
        // "best base" — largest basicsize).  subtype_dealloc therefore traverses:
        //   TzInfo → RustTzInfo → object
        // ...and never touches PyDateTime_CAPI pointers that may be dangling after
        // _datetime module cleanup.
        //
        // The PyOnceLock in `input::datetime` holds a strong Py<PyAny> reference to
        // the new class.  PyOnceLock is intentionally never dropped (static lifetime),
        // which keeps the class alive past _PyImport_Cleanup — fixing the class-freed-
        // before-instances race (Bug 1) without a manual Py_INCREF.
        // ---------------------------------------------------------------------------
        let py = m.py();
        let rust_tzinfo = py.get_type::<TzInfo>().into_any();
        let datetime_mod = py.import("datetime")?;
        let py_tzinfo_base = datetime_mod.getattr("tzinfo")?;
        let bases = pyo3::types::PyTuple::new(py, [rust_tzinfo, py_tzinfo_base])?;
        let class_dict = pyo3::types::PyDict::new(py);
        class_dict.set_item("__module__", "pydantic_core._pydantic_core")?;
        let new_tzinfo: Bound<'_, PyAny> = py
            .get_type::<pyo3::types::PyType>()
            .call1(("TzInfo", bases, class_dict))?;
        m.setattr("TzInfo", &new_tzinfo)?;
        crate::input::set_tzinfo_py_class(py, new_tzinfo.unbind());
        Ok(())
    }
}
