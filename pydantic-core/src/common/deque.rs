use pyo3::intern;
use pyo3::prelude::*;
use pyo3::sync::PyOnceLock;
use pyo3::types::{PyDict, PyList, PyType};

static DEQUE_TYPE: PyOnceLock<Py<PyType>> = PyOnceLock::new();

// No PyO3 interface can be provided (https://github.com/PyO3/pyo3/issues/2655)
pub fn get_deque_type(py: Python<'_>) -> PyResult<&Bound<'_, PyType>> {
    DEQUE_TYPE.import(py, "collections", "deque")
}

/// Get the `maxlen` of a `deque` instance.
pub fn deque_maxlen(value: &Bound<'_, PyAny>) -> PyResult<Option<usize>> {
    value.getattr(intern!(value.py(), "maxlen"))?.extract()
}

/// Build a new `deque` from `items`, with the given `maxlen`.
pub fn new_deque<'py>(py: Python<'py>, items: Bound<'py, PyList>, maxlen: Option<usize>) -> PyResult<Py<PyAny>> {
    let deque_type = get_deque_type(py)?;
    let deque = match maxlen {
        Some(maxlen) => {
            let kwargs = PyDict::new(py);
            kwargs.set_item(intern!(py, "maxlen"), maxlen)?;
            deque_type.call((items,), Some(&kwargs))?
        }
        None => deque_type.call1((items,))?,
    };
    Ok(deque.unbind())
}
