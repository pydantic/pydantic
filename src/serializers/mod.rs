use std::fmt::Debug;
use std::sync::atomic::{AtomicUsize, Ordering};

use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict};
use pyo3::{PyTraverseError, PyVisit};

use crate::definitions::{Definitions, DefinitionsBuilder};
use crate::py_gc::PyGcTraverse;

use config::SerializationConfig;
pub use errors::{PydanticSerializationError, PydanticSerializationUnexpectedValue};
use extra::{CollectWarnings, SerRecursionState};
pub(crate) use extra::{Extra, SerMode, SerializationState};
pub use shared::CombinedSerializer;
use shared::{to_json_bytes, BuildSerializer, TypeSerializer};

mod computed_fields;
mod config;
mod errors;
mod extra;
mod fields;
mod filter;
mod infer;
mod ob_type;
pub mod ser;
mod shared;
mod type_serializers;

#[pyclass(module = "pydantic_core._pydantic_core", frozen)]
#[derive(Debug)]
pub struct SchemaSerializer {
    serializer: CombinedSerializer,
    definitions: Definitions<CombinedSerializer>,
    expected_json_size: AtomicUsize,
    config: SerializationConfig,
    // References to the Python schema and config objects are saved to enable
    // reconstructing the object for pickle support (see `__reduce__`).
    py_schema: Py<PyDict>,
    py_config: Option<Py<PyDict>>,
}

impl SchemaSerializer {
    #[allow(clippy::too_many_arguments)]
    pub(crate) fn build_extra<'b, 'a: 'b>(
        &'b self,
        py: Python<'a>,
        mode: &'a SerMode,
        by_alias: bool,
        warnings: &'a CollectWarnings,
        exclude_unset: bool,
        exclude_defaults: bool,
        exclude_none: bool,
        round_trip: bool,
        rec_guard: &'a SerRecursionState,
        serialize_unknown: bool,
        fallback: Option<&'a PyAny>,
        context: Option<&'a PyAny>,
    ) -> Extra<'b> {
        Extra::new(
            py,
            mode,
            by_alias,
            warnings,
            exclude_unset,
            exclude_defaults,
            exclude_none,
            round_trip,
            &self.config,
            rec_guard,
            serialize_unknown,
            fallback,
            context,
        )
    }
}

#[pymethods]
impl SchemaSerializer {
    #[new]
    pub fn py_new(py: Python, schema: &PyDict, config: Option<&PyDict>) -> PyResult<Self> {
        let mut definitions_builder = DefinitionsBuilder::new();
        let serializer = CombinedSerializer::build(schema.downcast()?, config, &mut definitions_builder)?;
        Ok(Self {
            serializer,
            definitions: definitions_builder.finish()?,
            expected_json_size: AtomicUsize::new(1024),
            config: SerializationConfig::from_config(config)?,
            py_schema: schema.into_py(py),
            py_config: match config {
                Some(c) if !c.is_empty() => Some(c.into_py(py)),
                _ => None,
            },
        })
    }

    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (value, *, mode = None, include = None, exclude = None, by_alias = true,
        exclude_unset = false, exclude_defaults = false, exclude_none = false, round_trip = false, warnings = true,
        fallback = None, context = None))]
    pub fn to_python(
        &self,
        py: Python,
        value: &PyAny,
        mode: Option<&str>,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        by_alias: bool,
        exclude_unset: bool,
        exclude_defaults: bool,
        exclude_none: bool,
        round_trip: bool,
        warnings: bool,
        fallback: Option<&PyAny>,
        context: Option<&PyAny>,
    ) -> PyResult<PyObject> {
        let mode: SerMode = mode.into();
        let warnings = CollectWarnings::new(warnings);
        let rec_guard = SerRecursionState::default();
        let extra = self.build_extra(
            py,
            &mode,
            by_alias,
            &warnings,
            exclude_unset,
            exclude_defaults,
            exclude_none,
            round_trip,
            &rec_guard,
            false,
            fallback,
            context,
        );
        let v = self.serializer.to_python(value, include, exclude, &extra)?;
        warnings.final_check(py)?;
        Ok(v)
    }

    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (value, *, indent = None, include = None, exclude = None, by_alias = true,
        exclude_unset = false, exclude_defaults = false, exclude_none = false, round_trip = false, warnings = true,
        fallback = None, context = None))]
    pub fn to_json(
        &self,
        py: Python,
        value: &PyAny,
        indent: Option<usize>,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        by_alias: bool,
        exclude_unset: bool,
        exclude_defaults: bool,
        exclude_none: bool,
        round_trip: bool,
        warnings: bool,
        fallback: Option<&PyAny>,
        context: Option<&PyAny>,
    ) -> PyResult<PyObject> {
        let warnings = CollectWarnings::new(warnings);
        let rec_guard = SerRecursionState::default();
        let extra = self.build_extra(
            py,
            &SerMode::Json,
            by_alias,
            &warnings,
            exclude_unset,
            exclude_defaults,
            exclude_none,
            round_trip,
            &rec_guard,
            false,
            fallback,
            context,
        );
        let bytes = to_json_bytes(
            value,
            &self.serializer,
            include,
            exclude,
            &extra,
            indent,
            self.expected_json_size.load(Ordering::Relaxed),
        )?;

        warnings.final_check(py)?;

        self.expected_json_size.store(bytes.len(), Ordering::Relaxed);
        let py_bytes = PyBytes::new(py, &bytes);
        Ok(py_bytes.into())
    }

    pub fn __reduce__(slf: &PyCell<Self>) -> PyResult<(PyObject, (PyObject, PyObject))> {
        // Enables support for `pickle` serialization.
        let py = slf.py();
        let cls = slf.get_type().into();
        let init_args = (slf.get().py_schema.to_object(py), slf.get().py_config.to_object(py));
        Ok((cls, init_args))
    }

    pub fn __repr__(&self) -> String {
        format!(
            "SchemaSerializer(serializer={:#?}, definitions={:#?})",
            self.serializer, self.definitions
        )
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        visit.call(&self.py_schema)?;
        if let Some(ref py_config) = self.py_config {
            visit.call(py_config)?;
        }
        self.serializer.py_gc_traverse(&visit)?;
        self.definitions.py_gc_traverse(&visit)?;
        Ok(())
    }
}

#[allow(clippy::too_many_arguments)]
#[pyfunction]
#[pyo3(signature = (value, *, indent = None, include = None, exclude = None, by_alias = true,
    exclude_none = false, round_trip = false, timedelta_mode = "iso8601", bytes_mode = "utf8",
    inf_nan_mode = "constants", serialize_unknown = false, fallback = None, context = None))]
pub fn to_json(
    py: Python,
    value: &PyAny,
    indent: Option<usize>,
    include: Option<&PyAny>,
    exclude: Option<&PyAny>,
    by_alias: bool,
    exclude_none: bool,
    round_trip: bool,
    timedelta_mode: &str,
    bytes_mode: &str,
    inf_nan_mode: &str,
    serialize_unknown: bool,
    fallback: Option<&PyAny>,
    context: Option<&PyAny>,
) -> PyResult<PyObject> {
    let state = SerializationState::new(timedelta_mode, bytes_mode, inf_nan_mode)?;
    let extra = state.extra(
        py,
        &SerMode::Json,
        by_alias,
        exclude_none,
        round_trip,
        serialize_unknown,
        fallback,
        context,
    );
    let serializer = type_serializers::any::AnySerializer.into();
    let bytes = to_json_bytes(value, &serializer, include, exclude, &extra, indent, 1024)?;
    state.final_check(py)?;
    let py_bytes = PyBytes::new(py, &bytes);
    Ok(py_bytes.into())
}

#[allow(clippy::too_many_arguments)]
#[pyfunction]
#[pyo3(signature = (value, *, include = None, exclude = None, by_alias = true, exclude_none = false, round_trip = false,
    timedelta_mode = "iso8601", bytes_mode = "utf8", inf_nan_mode = "constants", serialize_unknown = false, fallback = None, context = None))]
pub fn to_jsonable_python(
    py: Python,
    value: &PyAny,
    include: Option<&PyAny>,
    exclude: Option<&PyAny>,
    by_alias: bool,
    exclude_none: bool,
    round_trip: bool,
    timedelta_mode: &str,
    bytes_mode: &str,
    inf_nan_mode: &str,
    serialize_unknown: bool,
    fallback: Option<&PyAny>,
    context: Option<&PyAny>,
) -> PyResult<PyObject> {
    let state = SerializationState::new(timedelta_mode, bytes_mode, inf_nan_mode)?;
    let extra = state.extra(
        py,
        &SerMode::Json,
        by_alias,
        exclude_none,
        round_trip,
        serialize_unknown,
        fallback,
        context,
    );
    let v = infer::infer_to_python(value, include, exclude, &extra)?;
    state.final_check(py)?;
    Ok(v)
}
