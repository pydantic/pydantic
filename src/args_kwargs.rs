use pyo3::prelude::*;
use pyo3::types::{PyDict, PyTuple};

#[pyclass(module = "pydantic_core._pydantic_core", get_all, frozen, freelist = 100)]
#[derive(Debug, Clone)]
pub struct ArgsKwargs {
    pub(crate) args: Py<PyTuple>,
    pub(crate) kwargs: Option<Py<PyDict>>,
}

#[pymethods]
impl ArgsKwargs {
    #[new]
    fn py_new(py: Python, args: &PyTuple, kwargs: Option<&PyDict>) -> Self {
        Self {
            args: args.into_py(py),
            kwargs: kwargs.map(|d| d.into_py(py)),
        }
    }

    pub fn __repr__(&self, py: Python) -> String {
        let args = self.args.as_ref(py);
        match self.kwargs {
            Some(ref d) => format!("ArgsKwargs(args={args}, kwargs={})", d.as_ref(py)),
            None => format!("ArgsKwargs(args={args}, kwargs={{}})"),
        }
    }
}
