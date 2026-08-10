//! `pydantic._internal._model_construction._ModelNamespaceDict` with its `__setitem__()` implemented
//! natively: this is the mapping returned by `ModelMetaclass.__prepare__()`, so every name bound while
//! executing the body of a model class goes through it. The pure Python version (used as a fallback on
//! other Python implementations) costs a Python function call per store; the logic is otherwise
//! identical: warn when a name overrides an existing Pydantic decorator (`PydanticDescriptorProxy`).
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::sync::PyOnceLock;
use pyo3::types::{PyDict, PyString, PyType};

/// A dictionary subclass that intercepts attribute setting on model classes and
/// warns about overriding of decorators.
#[pyclass(extends = PyDict, module = "pydantic_core._pydantic_core", name = "_ModelNamespaceDict", dict, weakref, subclass)]
pub struct ModelNamespaceDict {}

static DESCRIPTOR_PROXY_TYPE: PyOnceLock<Py<PyType>> = PyOnceLock::new();

fn descriptor_proxy_type(py: Python<'_>) -> PyResult<&Bound<'_, PyType>> {
    DESCRIPTOR_PROXY_TYPE
        .get_or_try_init(py, || {
            py.import("pydantic._internal._decorators")?
                .getattr("PydanticDescriptorProxy")?
                .cast_into::<PyType>()
                .map(Bound::unbind)
                .map_err(Into::into)
        })
        .map(|t| t.bind(py))
}

#[pymethods]
impl ModelNamespaceDict {
    #[new]
    #[pyo3(signature = (*_args, **_kwargs))]
    fn py_new(_args: &Bound<'_, PyAny>, _kwargs: Option<&Bound<'_, PyAny>>) -> Self {
        Self {}
    }

    fn __setitem__(slf: &Bound<'_, Self>, k: &Bound<'_, PyAny>, v: &Bound<'_, PyAny>) -> PyResult<()> {
        let py = slf.py();
        // SAFETY: `Self` extends `dict`.
        let dict = unsafe { slf.cast_unchecked::<PyDict>() };
        // `existing = self.get(k, None)`
        if let Some(existing) = dict.get_item(k)? {
            // `if existing and v is not existing and isinstance(existing, PydanticDescriptorProxy):`
            if existing.is_truthy()? && !v.is(&existing) && existing.is_instance(descriptor_proxy_type(py)?.as_any())? {
                let decorator_repr = existing
                    .getattr(intern!(py, "decorator_info"))?
                    .getattr(intern!(py, "decorator_repr"))?;
                let message = PyString::new(py, "`{}` overrides an existing Pydantic `{}` decorator")
                    .call_method1(intern!(py, "format"), (k, decorator_repr))?;
                // Equivalent to `warnings.warn(message, stacklevel=2)` from a Python-level `__setitem__()`:
                // there is no Python frame for this method, so the frame setting the item is at level 1.
                let kwargs = PyDict::new(py);
                kwargs.set_item(intern!(py, "stacklevel"), 1)?;
                py.import(intern!(py, "warnings"))?
                    .getattr(intern!(py, "warn"))?
                    .call((message,), Some(&kwargs))?;
            }
        }
        // `dict.__setitem__(self, k, v)`
        dict.set_item(k, v)
    }

    fn __delitem__(slf: &Bound<'_, Self>, k: &Bound<'_, PyAny>) -> PyResult<()> {
        // Not overridden by the pure Python version: plain `dict` item deletion.
        // SAFETY: `Self` extends `dict`.
        let dict = unsafe { slf.cast_unchecked::<PyDict>() };
        dict.del_item(k)
    }
}
