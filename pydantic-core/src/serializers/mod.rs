use std::fmt::Debug;
use std::sync::Arc;
use std::sync::atomic::{AtomicUsize, Ordering};

use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict, PyTuple, PyType};
use pyo3::{PyTraverseError, PyVisit};
use type_serializers::any::AnySerializer;

use crate::definitions::{Definitions, DefinitionsBuilder};
use crate::py_gc::PyGcTraverse;
use crate::schema_core::{SchemaCore, SchemaCoreData};

pub(crate) use config::{BytesMode, SerializationConfig};
pub use errors::{PydanticSerializationError, PydanticSerializationUnexpectedValue};
pub(crate) use extra::{Extra, SerMode, SerializationState, WarningsMode};
pub use shared::CombinedSerializer;
use shared::{BuildSerializer, to_json_bytes};

mod computed_fields;
mod config;
mod errors;
mod extra;
mod fields;
mod filter;
mod infer;
mod ob_type;
mod polymorphism_trampoline;
mod prebuilt;
pub mod ser;
mod shared;
mod type_serializers;

#[derive(FromPyObject)]
pub enum WarningsArg {
    Bool(bool),
    Literal(WarningsMode),
}

/// The serialization half of a [`SchemaCoreData`]: the built serializer tree plus
/// serialization-specific configuration.
#[derive(Debug)]
pub struct SerializerPart {
    pub(crate) serializer: Arc<CombinedSerializer>,
    definitions: Definitions<Arc<CombinedSerializer>>,
    expected_json_size: AtomicUsize,
    pub(crate) config: SerializationConfig,
}

impl_py_gc_traverse!(SerializerPart {
    serializer,
    definitions,
});

impl SerializerPart {
    pub fn build(schema: &Bound<'_, PyDict>, config: Option<&Bound<'_, PyDict>>, use_prebuilt: bool) -> PyResult<Self> {
        // use_prebuilt=true by default, but false during rebuilds to avoid stale references
        // to old serializers (see https://github.com/pydantic/pydantic/issues/12446)
        let mut definitions_builder = DefinitionsBuilder::new(use_prebuilt);
        let serializer = CombinedSerializer::build(schema, config, &mut definitions_builder)?;
        Ok(Self {
            serializer,
            definitions: definitions_builder.finish()?,
            expected_json_size: AtomicUsize::new(1024),
            config: SerializationConfig::from_config(config)?,
        })
    }
}

#[pyclass(module = "pydantic_core._pydantic_core", frozen)]
#[derive(Debug)]
pub struct SchemaSerializer {
    // The `SchemaCore` Python object owns the serializer data; this view holds (and
    // reports to the GC) a single reference to it. See the GC note on `SchemaCoreData`.
    core: Py<SchemaCore>,
}

impl_py_gc_traverse!(SchemaSerializer { core });

impl SchemaSerializer {
    /// Create a serializer view over an existing core. The core must have a serializer part.
    pub(crate) fn from_core(core: Py<SchemaCore>) -> Self {
        debug_assert!(core.get().data.serializer.is_some());
        Self { core }
    }

    fn part(&self) -> &SerializerPart {
        self.core.get().data.serializer_part()
    }

    /// The root serializer of the tree, used by prebuilt serializers and inference.
    pub(crate) fn serializer(&self) -> &Arc<CombinedSerializer> {
        &self.part().serializer
    }

    /// The serialization config, used when serialization is driven through inference.
    pub(crate) fn config(&self) -> SerializationConfig {
        self.part().config
    }
}

#[pymethods]
impl SchemaSerializer {
    #[new]
    #[pyo3(signature = (schema, config=None, _use_prebuilt=true))]
    pub fn py_new(
        schema: Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        _use_prebuilt: bool,
    ) -> PyResult<Self> {
        let py = schema.py();
        let data = SchemaCoreData::build(py, schema.as_any(), config, _use_prebuilt, false, true)?;
        Ok(Self {
            core: SchemaCore::new_py(py, data)?,
        })
    }

    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (value, *, mode = None, include = None, exclude = None, by_alias = None,
        exclude_unset = false, exclude_defaults = false, exclude_none = false, exclude_computed_fields = false,
        round_trip = false, warnings = WarningsArg::Bool(true), fallback = None, serialize_as_any = false,
        polymorphic_serialization = None, context = None))]
    pub fn to_python(
        &self,
        py: Python,
        value: &Bound<'_, PyAny>,
        mode: Option<&str>,
        include: Option<Bound<'_, PyAny>>,
        exclude: Option<Bound<'_, PyAny>>,
        by_alias: Option<bool>,
        exclude_unset: bool,
        exclude_defaults: bool,
        exclude_none: bool,
        exclude_computed_fields: bool,
        round_trip: bool,
        warnings: WarningsArg,
        fallback: Option<Bound<'_, PyAny>>,
        serialize_as_any: bool,
        polymorphic_serialization: Option<bool>,
        context: Option<Bound<'_, PyAny>>,
    ) -> PyResult<Py<PyAny>> {
        let mode: SerMode = mode.into();
        let warnings_mode = match warnings {
            WarningsArg::Bool(b) => b.into(),
            WarningsArg::Literal(mode) => mode,
        };
        let extra = Extra::new(
            py,
            mode,
            by_alias,
            exclude_unset,
            exclude_defaults,
            exclude_none,
            exclude_computed_fields,
            round_trip,
            false,
            fallback,
            serialize_as_any,
            polymorphic_serialization,
            context,
        );
        let part = self.part();
        let mut state = SerializationState::new(part.config, warnings_mode, include, exclude, extra)?;
        let v = part.serializer.to_python(value, &mut state)?;
        state.warnings.final_check(py)?;
        Ok(v)
    }

    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (value, *, indent = None, ensure_ascii = false, include = None, exclude = None, by_alias = None,
        exclude_unset = false, exclude_defaults = false, exclude_none = false, exclude_computed_fields = false,
        round_trip = false, warnings = WarningsArg::Bool(true), fallback = None, serialize_as_any = false,
        polymorphic_serialization = None, context = None))]
    pub fn to_json(
        &self,
        py: Python,
        value: &Bound<'_, PyAny>,
        indent: Option<usize>,
        ensure_ascii: Option<bool>,
        include: Option<Bound<'_, PyAny>>,
        exclude: Option<Bound<'_, PyAny>>,
        by_alias: Option<bool>,
        exclude_unset: bool,
        exclude_defaults: bool,
        exclude_none: bool,
        exclude_computed_fields: bool,
        round_trip: bool,
        warnings: WarningsArg,
        fallback: Option<Bound<'_, PyAny>>,
        serialize_as_any: bool,
        polymorphic_serialization: Option<bool>,
        context: Option<Bound<'_, PyAny>>,
    ) -> PyResult<Py<PyAny>> {
        let warnings_mode = match warnings {
            WarningsArg::Bool(b) => b.into(),
            WarningsArg::Literal(mode) => mode,
        };
        let extra = Extra::new(
            py,
            SerMode::Json,
            by_alias,
            exclude_unset,
            exclude_defaults,
            exclude_none,
            exclude_computed_fields,
            round_trip,
            false,
            fallback,
            serialize_as_any,
            polymorphic_serialization,
            context,
        );
        let part = self.part();
        let mut state = SerializationState::new(part.config, warnings_mode, include, exclude, extra)?;
        let bytes = to_json_bytes(
            value,
            &part.serializer,
            &mut state,
            indent,
            ensure_ascii.unwrap_or(false),
            part.expected_json_size.load(Ordering::Relaxed),
        )?;

        state.warnings.final_check(py)?;

        part.expected_json_size.store(bytes.len(), Ordering::Relaxed);
        let py_bytes = PyBytes::new(py, &bytes);
        Ok(py_bytes.into())
    }

    pub fn __reduce__<'py>(slf: &Bound<'py, Self>) -> PyResult<(Bound<'py, PyType>, Bound<'py, PyTuple>)> {
        // Passing _use_prebuilt=false avoids reusing prebuilt serializers when unpickling
        let core = &slf.get().core.get().data;
        let init_args = (&core.py_schema, &core.py_config, false).into_pyobject(slf.py())?;
        Ok((slf.get_type(), init_args))
    }

    pub fn __repr__(&self) -> String {
        let part = self.part();
        format!(
            "SchemaSerializer(serializer={:#?}, definitions={:#?})",
            part.serializer, part.definitions
        )
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        self.py_gc_traverse(&visit)
    }
}

#[allow(clippy::too_many_arguments)]
#[pyfunction]
#[pyo3(signature = (value, *, indent = None, ensure_ascii = false, include = None, exclude = None, by_alias = true,
    exclude_none = false, round_trip = false, timedelta_mode = "iso8601", temporal_mode = "iso8601",
    bytes_mode = "utf8",  inf_nan_mode = "constants", serialize_unknown = false, fallback = None,
    serialize_as_any = false, polymorphic_serialization = None, context = None))]
pub fn to_json(
    py: Python,
    value: &Bound<'_, PyAny>,
    indent: Option<usize>,
    ensure_ascii: Option<bool>,
    include: Option<Bound<'_, PyAny>>,
    exclude: Option<Bound<'_, PyAny>>,
    by_alias: bool,
    exclude_none: bool,
    round_trip: bool,
    timedelta_mode: &str,
    temporal_mode: &str,
    bytes_mode: &str,
    inf_nan_mode: &str,
    serialize_unknown: bool,
    fallback: Option<Bound<'_, PyAny>>,
    serialize_as_any: bool,
    polymorphic_serialization: Option<bool>,
    context: Option<Bound<'_, PyAny>>,
) -> PyResult<Py<PyAny>> {
    let config = SerializationConfig::from_args(timedelta_mode, temporal_mode, bytes_mode, inf_nan_mode)?;
    let extra = Extra::new(
        py,
        SerMode::Json,
        Some(by_alias),
        false,
        false,
        exclude_none,
        false,
        round_trip,
        serialize_unknown,
        fallback,
        serialize_as_any,
        polymorphic_serialization,
        context,
    );
    let mut state = SerializationState::new(config, WarningsMode::None, include, exclude, extra)?;
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

#[allow(clippy::too_many_arguments)]
#[pyfunction]
#[pyo3(signature = (value, *, include = None, exclude = None, by_alias = true, exclude_none = false, round_trip = false,
    timedelta_mode = "iso8601", temporal_mode = "iso8601", bytes_mode = "utf8", inf_nan_mode = "constants",
    serialize_unknown = false, fallback = None, serialize_as_any = false, polymorphic_serialization = None, context = None))]
pub fn to_jsonable_python(
    py: Python,
    value: &Bound<'_, PyAny>,
    include: Option<Bound<'_, PyAny>>,
    exclude: Option<Bound<'_, PyAny>>,
    by_alias: bool,
    exclude_none: bool,
    round_trip: bool,
    timedelta_mode: &str,
    temporal_mode: &str,
    bytes_mode: &str,
    inf_nan_mode: &str,
    serialize_unknown: bool,
    fallback: Option<Bound<'_, PyAny>>,
    serialize_as_any: bool,
    polymorphic_serialization: Option<bool>,
    context: Option<Bound<'_, PyAny>>,
) -> PyResult<Py<PyAny>> {
    let config = SerializationConfig::from_args(timedelta_mode, temporal_mode, bytes_mode, inf_nan_mode)?;
    let extra = Extra::new(
        py,
        SerMode::Json,
        Some(by_alias),
        false,
        false,
        exclude_none,
        false,
        round_trip,
        serialize_unknown,
        fallback,
        serialize_as_any,
        polymorphic_serialization,
        context,
    );
    let mut state = SerializationState::new(config, WarningsMode::None, include, exclude, extra)?;
    let v = infer::infer_to_python(value, &mut state)?;
    state.final_check(py)?;
    Ok(v)
}
