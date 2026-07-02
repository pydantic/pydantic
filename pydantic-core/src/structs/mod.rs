use pyo3::{prelude::*, types::PyType};

#[pyfunction]
pub fn create_struct_type<'py>(class: &Bound<'py, PyType>) -> Bound<'py, PyType> {
    class.clone()
}
