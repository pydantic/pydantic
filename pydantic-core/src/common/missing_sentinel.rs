use pyo3::prelude::*;
use pyo3::sync::PyOnceLock;

static MISSING_SENTINEL_OBJECT: PyOnceLock<Py<PyAny>> = PyOnceLock::new();

pub fn get_missing_sentinel_object(py: Python<'_>) -> PyResult<&Bound<'_, PyAny>> {
    MISSING_SENTINEL_OBJECT.import(py, "pydantic_core", "MISSING")
}
