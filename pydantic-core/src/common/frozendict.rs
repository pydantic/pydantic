use pyo3::prelude::*;
use pyo3::sync::PyOnceLock;
use pyo3::types::PyType;

static FROZENDICT_TYPE: PyOnceLock<Py<PyType>> = PyOnceLock::new();

// TODO: remove when https://github.com/PyO3/pyo3/pull/6174 gets released and use `PyFrozenDict` instead:
pub fn get_frozendict_type(py: Python<'_>) -> PyResult<&Bound<'_, PyType>> {
    FROZENDICT_TYPE.import(py, "builtins", "frozendict")
}
