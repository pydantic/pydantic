#![cfg_attr(has_coverage_attribute, feature(coverage_attribute))]

extern crate core;

use std::ffi::c_void;
use std::sync::OnceLock;
use std::sync::atomic::{AtomicPtr, Ordering};

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

// ---------------------------------------------------------------------------
// Two-part fix for pydantic_core.TzInfo shutdown SIGSEGV (pydantic#12867)
//
// Part 1 — keep TzInfo *class* alive past _PyImport_Cleanup.
//   pydantic_core._pydantic_core is finalized before __main__, so the TzInfo
//   class object can be freed while datetime objects in __main__ still hold
//   TzInfo instances.  _Py_Dealloc then dereferences the freed class ->
//   SIGSEGV before tp_dealloc is even called.  A deliberate Py_INCREF at
//   module init (stored in a raw AtomicPtr with no Drop) keeps the class
//   alive for the rest of the process lifetime.
//
// Part 2 — skip the base-class dealloc chain during shutdown.
//   TzInfo.tp_base = PyDateTime_TZInfoType; subtype_dealloc traverses this
//   chain.  After _PyImport_Cleanup, PyDateTimeAPI type pointers may be
//   dangling -> SIGSEGV inside subtype_dealloc.  We replace tp_dealloc with
//   tzinfo_dealloc_guarded, which skips the chain when _Py_IsFinalizing().
//   TzInfo holds only `seconds: i32` — no Python refs, nothing to leak.
// ---------------------------------------------------------------------------

// Detect interpreter shutdown without depending on version-specific private symbols.
//
// CPython 3.13+ exports Py_IsFinalizing() as a real symbol; pyo3::ffi exposes it
// under the Py_3_13 cfg flag. On CPython 3.9–3.12 the public Py_IsFinalizing()
// is a static inline, so we link against the internal _Py_IsFinalizing() which
// is exported in those versions. PyPy and GraalPy have different GC/shutdown
// semantics; the CPython _PyImport_Cleanup race does not apply to them, so we
// simply return false there (taking the normal dealloc path is always safe).
#[cfg(all(not(PyPy), not(GraalPy), not(Py_3_13)))]
unsafe extern "C" {
    fn _Py_IsFinalizing() -> std::os::raw::c_int;
}

#[inline]
fn is_finalizing() -> bool {
    #[cfg(any(PyPy, GraalPy))]
    let finalizing = false;
    #[cfg(all(not(PyPy), not(GraalPy), Py_3_13))]
    let finalizing = unsafe { pyo3::ffi::Py_IsFinalizing() != 0 };
    #[cfg(all(not(PyPy), not(GraalPy), not(Py_3_13)))]
    let finalizing = unsafe { _Py_IsFinalizing() != 0 };
    finalizing
}

// Stores a raw (uncounted by Rust) pointer to the original PyO3-generated
// tp_dealloc for TzInfo. Set once at module init.
static TZINFO_ORIG_DEALLOC: AtomicPtr<c_void> = AtomicPtr::new(std::ptr::null_mut());

// Stores a raw pointer to the TzInfo PyTypeObject with a deliberate Py_INCREF
// (never balanced — AtomicPtr has no Drop impl). Keeps the class alive past
// _PyImport_Cleanup so _Py_Dealloc(instance) can safely read tp_dealloc.
static TZINFO_CLASS_PTR: AtomicPtr<c_void> = AtomicPtr::new(std::ptr::null_mut());

/// Replacement tp_dealloc for pydantic_core.TzInfo.
///
/// Part 1 of the fix ensures the TzInfo class is still alive when this
/// function is reached. Part 2 skips the datetime.tzinfo base-class dealloc
/// chain, which accesses PyDateTimeAPI pointers that may be dangling during
/// interpreter shutdown.
unsafe extern "C" fn tzinfo_dealloc_guarded(slf: *mut pyo3::ffi::PyObject) {
    use pyo3::ffi;
    if is_finalizing() {
        // Shutdown path: skip tp_base (datetime.tzinfo) dealloc chain.
        // PyDateTimeAPI type pointers may be dangling after _datetime cleanup.
        // TzInfo holds only `seconds: i32` — nothing to release beyond memory.
        // TzInfo is not GC-tracked; tp_free is PyObject_Free. Safe to call directly.
        let tp_ptr = TZINFO_CLASS_PTR.load(Ordering::Relaxed).cast::<ffi::PyTypeObject>();
        if let Some(tp_free) = unsafe { (*tp_ptr).tp_free } {
            unsafe { tp_free(slf.cast()) };
        }
        return;
    }
    // Normal path: call the original PyO3-generated dealloc, which drops Rust
    // data and then chains through the datetime.tzinfo base-class dealloc.
    let orig_ptr = TZINFO_ORIG_DEALLOC.load(Ordering::Relaxed);
    if !orig_ptr.is_null() {
        let orig: unsafe extern "C" fn(*mut pyo3::ffi::PyObject) = unsafe { std::mem::transmute(orig_ptr) };
        unsafe { orig(slf) };
    }
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
        // Install the two-part shutdown-safety fix for TzInfo.
        // See https://github.com/pydantic/pydantic/issues/12867
        //
        // SAFETY:
        //   - type_ptr is valid; TzInfo is registered via #[pymodule_export]
        //     before module_init is called, so its type object is initialized.
        //   - TZINFO_CLASS_PTR receives a deliberate Py_INCREF that is never
        //     balanced (AtomicPtr has no Drop), intentionally keeping the class
        //     alive for the lifetime of the process to prevent use-after-free
        //     in _Py_Dealloc during interpreter shutdown.
        unsafe {
            use pyo3::ffi;
            let type_ptr = m.py().get_type::<TzInfo>().as_type_ptr();
            // Part 1: keep the class alive past _PyImport_Cleanup.
            ffi::Py_INCREF(type_ptr.cast::<ffi::PyObject>());
            TZINFO_CLASS_PTR.store(type_ptr.cast::<c_void>(), Ordering::Relaxed);
            // Part 2: replace tp_dealloc with the shutdown-safe version.
            let orig = (*type_ptr).tp_dealloc;
            let orig_ptr: *mut c_void = orig.map_or(std::ptr::null_mut(), |f| f as *mut c_void);
            TZINFO_ORIG_DEALLOC.store(orig_ptr, Ordering::Relaxed);
            (*type_ptr).tp_dealloc = Some(tzinfo_dealloc_guarded);
            ffi::PyType_Modified(type_ptr);
        }
        Ok(())
    }
}
