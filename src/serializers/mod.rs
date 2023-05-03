use std::fmt::Debug;

use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict};
use pyo3::{PyTraverseError, PyVisit};

use crate::definitions::DefinitionsBuilder;
use crate::validators::SelfValidator;

use config::SerializationConfig;
pub use errors::{PydanticSerializationError, PydanticSerializationUnexpectedValue};
use extra::{CollectWarnings, SerRecursionGuard};
pub(crate) use extra::{Extra, SerMode, SerializationState};
pub use shared::CombinedSerializer;
use shared::{to_json_bytes, BuildSerializer, TypeSerializer};

mod computed_fields;
mod config;
mod errors;
mod extra;
mod filter;
mod infer;
mod ob_type;
mod shared;
mod type_serializers;

#[pyclass(module = "pydantic_core._pydantic_core")]
#[derive(Debug, Clone)]
pub struct SchemaSerializer {
    serializer: CombinedSerializer,
    definitions: Vec<CombinedSerializer>,
    json_size: usize,
    config: SerializationConfig,
}

#[pymethods]
impl SchemaSerializer {
    #[new]
    pub fn py_new(py: Python, schema: &PyDict, config: Option<&PyDict>) -> PyResult<Self> {
        let self_validator = SelfValidator::new(py)?;
        let schema = self_validator.validate_schema(py, schema)?;
        let mut definitions_builder = DefinitionsBuilder::new();

        let serializer = CombinedSerializer::build(schema.downcast()?, config, &mut definitions_builder)?;
        Ok(Self {
            serializer,
            definitions: definitions_builder.finish()?,
            json_size: 1024,
            config: SerializationConfig::from_config(config)?,
        })
    }

    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (value, *, mode = None, include = None, exclude = None, by_alias = true,
        exclude_unset = false, exclude_defaults = false, exclude_none = false, round_trip = false, warnings = true,
        fallback = None))]
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
    ) -> PyResult<PyObject> {
        let mode: SerMode = mode.into();
        let warnings = CollectWarnings::new(warnings);
        let rec_guard = SerRecursionGuard::default();
        let extra = Extra::new(
            py,
            &mode,
            &self.definitions,
            by_alias,
            &warnings,
            exclude_unset,
            exclude_defaults,
            exclude_none,
            round_trip,
            &self.config,
            &rec_guard,
            false,
            fallback,
        );
        let v = self.serializer.to_python(value, include, exclude, &extra)?;
        warnings.final_check(py)?;
        Ok(v)
    }

    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (value, *, indent = None, include = None, exclude = None, by_alias = true,
        exclude_unset = false, exclude_defaults = false, exclude_none = false, round_trip = false, warnings = true,
        fallback = None))]
    pub fn to_json(
        &mut self,
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
    ) -> PyResult<PyObject> {
        let warnings = CollectWarnings::new(warnings);
        let rec_guard = SerRecursionGuard::default();
        let extra = Extra::new(
            py,
            &SerMode::Json,
            &self.definitions,
            by_alias,
            &warnings,
            exclude_unset,
            exclude_defaults,
            exclude_none,
            round_trip,
            &self.config,
            &rec_guard,
            false,
            fallback,
        );
        let bytes = to_json_bytes(
            value,
            &self.serializer,
            include,
            exclude,
            &extra,
            indent,
            self.json_size,
        )?;

        warnings.final_check(py)?;

        self.json_size = bytes.len();
        let py_bytes = PyBytes::new(py, &bytes);
        Ok(py_bytes.into())
    }

    pub fn __repr__(&self) -> String {
        format!(
            "SchemaSerializer(serializer={:#?}, definitions={:#?})",
            self.serializer, self.definitions
        )
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        self.serializer.py_gc_traverse(&visit)?;
        for slot in self.definitions.iter() {
            slot.py_gc_traverse(&visit)?;
        }
        Ok(())
    }

    fn __clear__(&mut self) {
        self.serializer.py_gc_clear();
        for slot in self.definitions.iter_mut() {
            slot.py_gc_clear();
        }
    }
}

#[allow(clippy::too_many_arguments)]
#[pyfunction]
#[pyo3(signature = (value, *, indent = None, include = None, exclude = None, by_alias = true,
    exclude_none = false, round_trip = false, timedelta_mode = None, bytes_mode = None,
    serialize_unknown = false, fallback = None))]
pub fn to_json(
    py: Python,
    value: &PyAny,
    indent: Option<usize>,
    include: Option<&PyAny>,
    exclude: Option<&PyAny>,
    by_alias: bool,
    exclude_none: bool,
    round_trip: bool,
    timedelta_mode: Option<&str>,
    bytes_mode: Option<&str>,
    serialize_unknown: bool,
    fallback: Option<&PyAny>,
) -> PyResult<PyObject> {
    let state = SerializationState::new(timedelta_mode, bytes_mode);
    let extra = state.extra(
        py,
        &SerMode::Json,
        by_alias,
        exclude_none,
        round_trip,
        serialize_unknown,
        fallback,
    );
    let serializer = type_serializers::any::AnySerializer::default().into();
    let bytes = to_json_bytes(value, &serializer, include, exclude, &extra, indent, 1024)?;
    state.final_check(py)?;
    let py_bytes = PyBytes::new(py, &bytes);
    Ok(py_bytes.into())
}

#[allow(clippy::too_many_arguments)]
#[pyfunction]
#[pyo3(signature = (value, *, include = None, exclude = None, by_alias = true, exclude_none = false, round_trip = false,
    timedelta_mode = None, bytes_mode = None, serialize_unknown = false, fallback = None))]
pub fn to_jsonable_python(
    py: Python,
    value: &PyAny,
    include: Option<&PyAny>,
    exclude: Option<&PyAny>,
    by_alias: bool,
    exclude_none: bool,
    round_trip: bool,
    timedelta_mode: Option<&str>,
    bytes_mode: Option<&str>,
    serialize_unknown: bool,
    fallback: Option<&PyAny>,
) -> PyResult<PyObject> {
    let state = SerializationState::new(timedelta_mode, bytes_mode);
    let extra = state.extra(
        py,
        &SerMode::Json,
        by_alias,
        exclude_none,
        round_trip,
        serialize_unknown,
        fallback,
    );
    let v = infer::infer_to_python(value, include, exclude, &extra)?;
    state.final_check(py)?;
    Ok(v)
}
