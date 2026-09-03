use pyo3::prelude::*;
use pyo3::sync::PyOnceLock;
use pyo3::types::PyType;

static DEQUE_TYPE: PyOnceLock<Py<PyType>> = PyOnceLock::new();

// No PyO3 interface can be provided (https://github.com/PyO3/pyo3/issues/2655):
pub fn get_deque_type(py: Python<'_>) -> PyResult<&Bound<'_, PyType>> {
    DEQUE_TYPE.import(py, "collections", "deque")
}
