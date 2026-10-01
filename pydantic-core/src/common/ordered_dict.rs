use pyo3::prelude::*;
use pyo3::sync::PyOnceLock;
use pyo3::types::PyType;

static ORDERED_DICT_TYPE: PyOnceLock<Py<PyType>> = PyOnceLock::new();

// No PyO3 interface can be provided (similar to https://github.com/PyO3/pyo3/issues/2655)
pub fn get_ordered_dict_type(py: Python<'_>) -> PyResult<&Bound<'_, PyType>> {
    ORDERED_DICT_TYPE.import(py, "collections", "OrderedDict")
}
