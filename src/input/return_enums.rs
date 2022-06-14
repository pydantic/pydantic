use pyo3::prelude::*;
use pyo3::types::PyBytes;

pub enum EitherBytes<'a> {
    Rust(Vec<u8>),
    Python(&'a PyBytes),
}

impl<'a> EitherBytes<'a> {
    pub fn len(&'a self) -> PyResult<usize> {
        match self {
            EitherBytes::Rust(bytes) => Ok(bytes.len()),
            EitherBytes::Python(py_bytes) => py_bytes.len(),
        }
    }
}

impl<'a> IntoPy<PyObject> for EitherBytes<'a> {
    fn into_py(self, py: Python<'_>) -> PyObject {
        match self {
            EitherBytes::Rust(bytes) => PyBytes::new(py, &bytes).into_py(py),
            EitherBytes::Python(py_bytes) => py_bytes.into_py(py),
        }
    }
}
