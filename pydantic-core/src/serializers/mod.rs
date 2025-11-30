use std::fmt::Debug;
use std::sync::Arc;
use std::sync::atomic::{AtomicUsize, Ordering};

use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict, PyTuple, PyType};
use pyo3::{PyTraverseError, PyVisit};
use type_serializers::any::AnySerializer;

use crate::definitions::{Definitions, DefinitionsBuilder};
use crate::py_gc::PyGcTraverse;

pub(crate) use config::{BytesMode, SerializationConfig};
pub use errors::{PydanticSerializationError, PydanticSerializationUnexpectedValue};
pub(crate) use extra::{Extra, SerMode, SerializationState, WarningsMode};
pub use shared::CombinedSerializer;
use shared::to_json_bytes;

mod computed_fields;
mod config;
mod errors;
mod extra;
mod fields;
mod filter;
mod infer;
mod ob_type;
mod prebuilt;
pub mod ser;
mod shared;
mod type_serializers;

#[derive(FromPyObject)]
pub enum WarningsArg {
    Bool(bool),
    Literal(WarningsMode),
}

#[pyclass(module = "pydantic_core._pydantic_core", frozen)]
#[derive(Debug)]
pub struct SchemaSerializer {
    serializer: Arc<CombinedSerializer>,
    definitions: Definitions<Arc<CombinedSerializer>>,
    expected_json_size: AtomicUsize,
    config: SerializationConfig,
    // References to the Python schema and config objects are saved to enable
    // reconstructing the object for pickle support (see `__reduce__`).
    py_schema: Py<PyDict>,
    py_config: Option<Py<PyDict>>,
}

impl_py_gc_traverse!(SchemaSerializer {
    serializer,
    definitions,
    py_schema,
    py_config,
});

#[pymethods]
impl SchemaSerializer {
    #[new]
    #[pyo3(signature = (schema, config=None))]
    pub fn py_new(schema: Bound<'_, PyDict>, config: Option<&Bound<'_, PyDict>>) -> PyResult<Self> {
        let mut definitions_builder = DefinitionsBuilder::new();
        let serializer = CombinedSerializer::build_base(schema.cast()?, config, &mut definitions_builder)?;
        Ok(Self {
            serializer,
            definitions: definitions_builder.finish()?,
            expected_json_size: AtomicUsize::new(1024),
            config: SerializationConfig::from_config(config)?,
            py_schema: schema.into(),
            py_config: match config {
                Some(c) if !c.is_empty() => Some(c.clone().into()),
                _ => None,
            },
        })
    }

    #[pyo3(signature = (value, *, mode = None, **kwargs))]
    pub fn to_python(
        &self,
        value: &Bound<'_, PyAny>,
        mode: Option<SerMode>,
        kwargs: Option<&Bound<'_, PyDict>>,
    ) -> PyResult<Py<PyAny>> {
        let py = value.py();
        let mut state = SerializationState::from_kwargs(py, mode.unwrap_or(SerMode::Python), self.config, kwargs)?;
        let v = self.serializer.to_python(value, &mut state)?;
        state.warnings.final_check(py)?;
        Ok(v)
    }

    #[pyo3(signature = (value, *, indent = None, ensure_ascii = false, **kwargs))]
    pub fn to_json(
        &self,
        value: &Bound<'_, PyAny>,
        indent: Option<usize>,
        ensure_ascii: Option<bool>,
        kwargs: Option<&Bound<'_, PyDict>>,
    ) -> PyResult<Py<PyAny>> {
        let py = value.py();
        let mut state = SerializationState::from_kwargs(py, SerMode::Json, self.config, kwargs)?;
        let bytes = to_json_bytes(
            value,
            &self.serializer,
            &mut state,
            indent,
            ensure_ascii.unwrap_or(false),
            self.expected_json_size.load(Ordering::Relaxed),
        )?;

        state.warnings.final_check(py)?;

        self.expected_json_size.store(bytes.len(), Ordering::Relaxed);
        let py_bytes = PyBytes::new(py, &bytes);
        Ok(py_bytes.into())
    }

    pub fn __reduce__<'py>(slf: &Bound<'py, Self>) -> PyResult<(Bound<'py, PyType>, Bound<'py, PyTuple>)> {
        let init_args = (&slf.get().py_schema, &slf.get().py_config).into_pyobject(slf.py())?;
        Ok((slf.get_type(), init_args))
    }

    pub fn __repr__(&self) -> String {
        format!(
            "SchemaSerializer(serializer={:#?}, definitions={:#?})",
            self.serializer, self.definitions
        )
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        self.py_gc_traverse(&visit)
    }
}

#[pyfunction]
#[pyo3(signature = (value, *, indent = None, ensure_ascii = false, **kwargs))]
pub fn to_json(
    value: &Bound<'_, PyAny>,
    indent: Option<usize>,
    ensure_ascii: Option<bool>,
    kwargs: Option<&Bound<'_, PyDict>>,
) -> PyResult<Py<PyAny>> {
    let py = value.py();
    let mut state = SerializationState::from_extended_kwargs(py, SerMode::Json, kwargs)?;
    let bytes = to_json_bytes(
        value,
        AnySerializer::get(),
        &mut state,
        indent,
        ensure_ascii.unwrap_or(false),
        1024,
    )?;
    state.final_check(py)?;
    let py_bytes = PyBytes::new(py, &bytes);
    Ok(py_bytes.into())
}

#[pyfunction]
#[pyo3(signature = (value, *, **kwargs))]
pub fn to_jsonable_python(value: &Bound<'_, PyAny>, kwargs: Option<&Bound<'_, PyDict>>) -> PyResult<Py<PyAny>> {
    let py = value.py();
    let mut state = SerializationState::from_extended_kwargs(py, SerMode::Json, kwargs)?;
    let v = infer::infer_to_python(value, &mut state)?;
    state.final_check(py)?;
    Ok(v)
}
