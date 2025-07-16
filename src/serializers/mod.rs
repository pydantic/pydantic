use std::fmt::Debug;
use std::sync::atomic::{AtomicUsize, Ordering};

use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict, PyTuple, PyType};
use pyo3::{PyTraverseError, PyVisit};
use type_serializers::any::AnySerializer;

use crate::definitions::{Definitions, DefinitionsBuilder};
use crate::py_gc::PyGcTraverse;

pub(crate) use config::BytesMode;
use config::SerializationConfig;
pub use errors::{PydanticSerializationError, PydanticSerializationUnexpectedValue};
use extra::{CollectWarnings, SerRecursionState, WarningsMode};
pub(crate) use extra::{Extra, SerMode, SerializationState};
use shared::to_json_bytes;
pub use shared::CombinedSerializer;

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
        by_alias: Option<bool>,
        warnings: &'a CollectWarnings,
        exclude_unset: bool,
        exclude_defaults: bool,
        exclude_none: bool,
        round_trip: bool,
        rec_guard: &'a SerRecursionState,
        serialize_unknown: bool,
        fallback: Option<&'a Bound<'a, PyAny>>,
        serialize_as_any: bool,
        context: Option<&'a Bound<'a, PyAny>>,
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
            serialize_as_any,
            context,
        )
    }
}

#[pymethods]
impl SchemaSerializer {
    #[new]
    #[pyo3(signature = (schema, config=None))]
    pub fn py_new(schema: Bound<'_, PyDict>, config: Option<&Bound<'_, PyDict>>) -> PyResult<Self> {
        let mut definitions_builder = DefinitionsBuilder::new();
        let serializer = CombinedSerializer::build_base(schema.downcast()?, config, &mut definitions_builder)?;
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

    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (value, *, mode = None, include = None, exclude = None, by_alias = None,
        exclude_unset = false, exclude_defaults = false, exclude_none = false, round_trip = false, warnings = WarningsArg::Bool(true),
        fallback = None, serialize_as_any = false, context = None))]
    pub fn to_python(
        &self,
        py: Python,
        value: &Bound<'_, PyAny>,
        mode: Option<&str>,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        by_alias: Option<bool>,
        exclude_unset: bool,
        exclude_defaults: bool,
        exclude_none: bool,
        round_trip: bool,
        warnings: WarningsArg,
        fallback: Option<&Bound<'_, PyAny>>,
        serialize_as_any: bool,
        context: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<PyObject> {
        let mode: SerMode = mode.into();
        let warnings_mode = match warnings {
            WarningsArg::Bool(b) => b.into(),
            WarningsArg::Literal(mode) => mode,
        };
        let warnings = CollectWarnings::new(warnings_mode);
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
            serialize_as_any,
            context,
        );
        let v = self.serializer.to_python(value, include, exclude, &extra)?;
        warnings.final_check(py)?;
        Ok(v)
    }

    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (value, *, indent = None, ensure_ascii = false, include = None, exclude = None, by_alias = None,
        exclude_unset = false, exclude_defaults = false, exclude_none = false, round_trip = false, warnings = WarningsArg::Bool(true),
        fallback = None, serialize_as_any = false, context = None))]
    pub fn to_json(
        &self,
        py: Python,
        value: &Bound<'_, PyAny>,
        indent: Option<usize>,
        ensure_ascii: Option<bool>,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        by_alias: Option<bool>,
        exclude_unset: bool,
        exclude_defaults: bool,
        exclude_none: bool,
        round_trip: bool,
        warnings: WarningsArg,
        fallback: Option<&Bound<'_, PyAny>>,
        serialize_as_any: bool,
        context: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<PyObject> {
        let warnings_mode = match warnings {
            WarningsArg::Bool(b) => b.into(),
            WarningsArg::Literal(mode) => mode,
        };
        let warnings = CollectWarnings::new(warnings_mode);
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
            serialize_as_any,
            context,
        );
        let bytes = to_json_bytes(
            value,
            &self.serializer,
            include,
            exclude,
            &extra,
            indent,
            ensure_ascii.unwrap_or(false),
            self.expected_json_size.load(Ordering::Relaxed),
        )?;

        warnings.final_check(py)?;

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
#[pyo3(signature = (value, *, indent = None, ensure_ascii = false, include = None, exclude = None, by_alias = true,
    exclude_none = false, round_trip = false, timedelta_mode = "iso8601", temporal_mode = "iso8601",
    bytes_mode = "utf8",  inf_nan_mode = "constants", serialize_unknown = false, fallback = None,
    serialize_as_any = false, context = None))]
pub fn to_json(
    py: Python,
    value: &Bound<'_, PyAny>,
    indent: Option<usize>,
    ensure_ascii: Option<bool>,
    include: Option<&Bound<'_, PyAny>>,
    exclude: Option<&Bound<'_, PyAny>>,
    by_alias: bool,
    exclude_none: bool,
    round_trip: bool,
    timedelta_mode: &str,
    temporal_mode: &str,
    bytes_mode: &str,
    inf_nan_mode: &str,
    serialize_unknown: bool,
    fallback: Option<&Bound<'_, PyAny>>,
    serialize_as_any: bool,
    context: Option<&Bound<'_, PyAny>>,
) -> PyResult<PyObject> {
    let state = SerializationState::new(timedelta_mode, temporal_mode, bytes_mode, inf_nan_mode)?;
    let extra = state.extra(
        py,
        &SerMode::Json,
        Some(by_alias),
        exclude_none,
        round_trip,
        serialize_unknown,
        fallback,
        serialize_as_any,
        context,
    );
    let bytes = to_json_bytes(
        value,
        AnySerializer::get(),
        include,
        exclude,
        &extra,
        indent,
        ensure_ascii.unwrap_or(false),
        1024,
    )?;
    state.final_check(py)?;
    let py_bytes = PyBytes::new(py, &bytes);
    Ok(py_bytes.into())
}

#[allow(clippy::too_many_arguments)]
#[pyfunction]
#[pyo3(signature = (value, *, include = None, exclude = None, by_alias = true, exclude_none = false, round_trip = false,
    timedelta_mode = "iso8601", temporal_mode = "iso8601", bytes_mode = "utf8", inf_nan_mode = "constants",
    serialize_unknown = false, fallback = None, serialize_as_any = false, context = None))]
pub fn to_jsonable_python(
    py: Python,
    value: &Bound<'_, PyAny>,
    include: Option<&Bound<'_, PyAny>>,
    exclude: Option<&Bound<'_, PyAny>>,
    by_alias: bool,
    exclude_none: bool,
    round_trip: bool,
    timedelta_mode: &str,
    temporal_mode: &str,
    bytes_mode: &str,
    inf_nan_mode: &str,
    serialize_unknown: bool,
    fallback: Option<&Bound<'_, PyAny>>,
    serialize_as_any: bool,
    context: Option<&Bound<'_, PyAny>>,
) -> PyResult<PyObject> {
    let state = SerializationState::new(timedelta_mode, temporal_mode, bytes_mode, inf_nan_mode)?;
    let extra = state.extra(
        py,
        &SerMode::Json,
        Some(by_alias),
        exclude_none,
        round_trip,
        serialize_unknown,
        fallback,
        serialize_as_any,
        context,
    );
    let v = infer::infer_to_python(value, include, exclude, &extra)?;
    state.final_check(py)?;
    Ok(v)
}
