use pyo3::prelude::*;
use pyo3::sync::PyOnceLock;
use pyo3::types::PyType;

static COUNTER_TYPE: PyOnceLock<Py<PyType>> = PyOnceLock::new();

// No PyO3 interface can be provided (similar to https://github.com/PyO3/pyo3/issues/2655)
pub fn get_counter_type(py: Python<'_>) -> PyResult<&Bound<'_, PyType>> {
    COUNTER_TYPE.import(py, "collections", "Counter")
}
