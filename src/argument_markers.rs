use pyo3::exceptions::PyNotImplementedError;
use pyo3::prelude::*;
use pyo3::sync::GILOnceCell;
use pyo3::types::{PyDict, PyTuple};

use crate::tools::safe_repr;

#[pyclass(module = "pydantic_core._pydantic_core", get_all, frozen, freelist = 100)]
#[derive(Debug, Clone)]
pub struct ArgsKwargs {
    pub(crate) args: Py<PyTuple>,
    pub(crate) kwargs: Option<Py<PyDict>>,
}

#[pymethods]
impl ArgsKwargs {
    #[new]
    #[pyo3(signature = (args, kwargs = None))]
    fn py_new(args: Bound<'_, PyTuple>, kwargs: Option<Bound<'_, PyDict>>) -> Self {
        Self {
            args: args.unbind(),
            kwargs: kwargs.filter(|d| !d.is_empty()).map(Bound::unbind),
        }
    }

    fn __eq__(&self, py: Python, other: &Self) -> PyResult<bool> {
        if !self.args.bind(py).eq(&other.args)? {
            return Ok(false);
        }

        match (&self.kwargs, &other.kwargs) {
            (Some(d1), Some(d2)) => d1.bind(py).eq(d2),
            (None, None) => Ok(true),
            _ => Ok(false),
        }
    }

    pub fn __repr__(&self, py: Python) -> String {
        let args = safe_repr(self.args.bind(py));
        match self.kwargs {
            Some(ref d) => format!("ArgsKwargs({args}, {})", safe_repr(d.bind(py))),
            None => format!("ArgsKwargs({args})"),
        }
    }
}

static UNDEFINED_CELL: GILOnceCell<Py<PydanticUndefinedType>> = GILOnceCell::new();

#[pyclass(module = "pydantic_core._pydantic_core", frozen)]
#[derive(Debug)]
pub struct PydanticUndefinedType {}

#[pymethods]
impl PydanticUndefinedType {
    #[new]
    pub fn py_new(_py: Python) -> PyResult<Self> {
        Err(PyNotImplementedError::new_err(
            "Creating instances of \"UndefinedType\" is not supported",
        ))
    }

    #[staticmethod]
    pub fn new(py: Python) -> Py<Self> {
        UNDEFINED_CELL
            .get_or_init(py, || Py::new(py, PydanticUndefinedType {}).unwrap())
            .clone_ref(py)
    }

    fn __repr__(&self) -> &'static str {
        "PydanticUndefined"
    }

    fn __copy__(&self, py: Python) -> Py<Self> {
        UNDEFINED_CELL.get(py).unwrap().clone_ref(py)
    }

    #[pyo3(signature = (_memo, /))]
    fn __deepcopy__(&self, py: Python, _memo: &Bound<'_, PyAny>) -> Py<Self> {
        self.__copy__(py)
    }

    fn __reduce__(&self) -> &'static str {
        "PydanticUndefined"
    }
}
