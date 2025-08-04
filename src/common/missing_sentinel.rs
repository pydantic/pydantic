use pyo3::intern;
use pyo3::prelude::*;
use pyo3::sync::GILOnceCell;

static MISSING_SENTINEL_OBJECT: GILOnceCell<Py<PyAny>> = GILOnceCell::new();

pub fn get_missing_sentinel_object(py: Python<'_>) -> &Bound<'_, PyAny> {
    MISSING_SENTINEL_OBJECT
        .get_or_init(py, || {
            py.import(intern!(py, "pydantic_core"))
                .and_then(|core_module| core_module.getattr(intern!(py, "MISSING")))
                .unwrap()
                .into()
        })
        .bind(py)
}
