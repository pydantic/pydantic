use std::borrow::Cow;
use std::sync::Arc;

use pyo3::IntoPyObjectExt;
use pyo3::PyTraverseError;
use pyo3::gc::PyVisit;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyIterator};

use serde::ser::SerializeSeq;

use crate::definitions::DefinitionsBuilder;
use crate::py_gc::PyGcTraverse;
use crate::serializers::SerializationState;
use crate::serializers::extra::IncludeExclude;
use crate::serializers::filter::SequenceFilter;
use crate::tools::SchemaDict;

use super::any::AnySerializer;
use super::{
    BuildSerializer, CombinedSerializer, ExtraOwned, PydanticSerializer, SchemaFilter, SerMode, TypeSerializer,
    infer_serialize, infer_to_python, py_err_se_err,
};

#[derive(Debug)]
pub struct GeneratorSerializer {
    item_serializer: Arc<CombinedSerializer>,
    filter: SchemaFilter<usize>,
}

impl BuildSerializer for GeneratorSerializer {
    const EXPECTED_TYPE: &'static str = "generator";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        let py = schema.py();
        let item_serializer = match schema.get_as(intern!(py, "items_schema"))? {
            Some(items_schema) => CombinedSerializer::build(&items_schema, config, definitions)?,
            None => AnySerializer::build(schema, config, definitions)?,
        };
        Ok(CombinedSerializer::Generator(Self {
            item_serializer,
            filter: SchemaFilter::from_schema(schema)?,
        })
        .into())
    }
}

impl_py_gc_traverse!(GeneratorSerializer { item_serializer });

impl TypeSerializer for GeneratorSerializer {
    fn to_python<'py>(&self, value: &Bound<'py, PyAny>, state: &mut SerializationState<'py>) -> PyResult<Py<PyAny>> {
        match value.cast::<PyIterator>() {
            Ok(py_iter) => {
                let py = value.py();
                match state.extra.mode {
                    SerMode::Json => {
                        let item_serializer = self.item_serializer.as_ref();

                        let mut items = match value.len() {
                            Ok(len) => Vec::with_capacity(len),
                            Err(_) => Vec::new(),
                        };
                        let filter = self.filter.for_sequence(state, None);
                        for (index, iter_result) in py_iter.clone().enumerate() {
                            let element = iter_result?;
                            if let Some(next_include_exclude) = filter.index_filter(index)? {
                                let state = &mut state.scoped_include_exclude(next_include_exclude);
                                items.push(item_serializer.to_python(&element, state)?);
                            }
                        }
                        items.into_py_any(py)
                    }
                    _ => {
                        let iter =
                            SerializationIterator::new(py_iter, &self.item_serializer, self.filter.clone(), state);
                        iter.into_py_any(py)
                    }
                }
            }
            Err(_) => {
                state.warn_fallback_py(self.get_name(), value)?;
                infer_to_python(value, state)
            }
        }
    }

    fn json_key<'a, 'py>(
        &self,
        key: &'a Bound<'py, PyAny>,
        state: &mut SerializationState<'py>,
    ) -> PyResult<Cow<'a, str>> {
        self.invalid_as_json_key(key, state, Self::EXPECTED_TYPE)
    }

    fn serde_serialize<'py, S: serde::ser::Serializer>(
        &self,
        value: &Bound<'py, PyAny>,
        serializer: S,
        state: &mut SerializationState<'py>,
    ) -> Result<S::Ok, S::Error> {
        match value.cast::<PyIterator>() {
            Ok(py_iter) => {
                let len = value.len().ok();
                let mut seq = serializer.serialize_seq(len)?;
                let item_serializer = self.item_serializer.as_ref();

                let filter = self.filter.for_sequence(state, None);
                for (index, iter_result) in py_iter.clone().enumerate() {
                    let element = iter_result.map_err(py_err_se_err)?;
                    let op_next = filter.index_filter(index).map_err(py_err_se_err)?;
                    if let Some(next_include_exclude) = op_next {
                        let state = &mut state.scoped_include_exclude(next_include_exclude);
                        let item_serialize = PydanticSerializer::new(&element, item_serializer, state);
                        seq.serialize_element(&item_serialize)?;
                    }
                }
                seq.end()
            }
            Err(_) => {
                state.warn_fallback_ser::<S>(self.get_name(), value)?;
                infer_serialize(value, serializer, state)
            }
        }
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}

#[pyclass(module = "pydantic_core._pydantic_core")]
pub(crate) struct SerializationIterator {
    iterator: Py<PyIterator>,
    #[pyo3(get)]
    index: usize,
    item_serializer: Arc<CombinedSerializer>,
    extra_owned: ExtraOwned,
    filter: SchemaFilter<usize>,
    /// The include/exclude values with negative indices resolved, set on the first `__next__()` call.
    resolved_filters: bool,
    resolved_include: Option<Py<PyAny>>,
    resolved_exclude: Option<Py<PyAny>>,
}

// `item_serializer` is intentionally not traversed: it is an `Arc` clone of a subtree owned (and
// traversed) by the `SchemaSerializer`. Visiting it here as well would report twice for a single reference,
// which corrupts the GC's refcount logic.
impl_py_gc_traverse!(SerializationIterator {
    iterator,
    extra_owned,
    resolved_include,
    resolved_exclude
});

impl SerializationIterator {
    pub fn new(
        py_iter: &Bound<'_, PyIterator>,
        item_serializer: &Arc<CombinedSerializer>,
        filter: SchemaFilter<usize>,
        state: &mut SerializationState<'_>,
    ) -> Self {
        Self {
            iterator: py_iter.clone().into(),
            index: 0,
            item_serializer: item_serializer.clone(),
            extra_owned: ExtraOwned::new(state),
            filter,
            resolved_filters: false,
            resolved_include: None,
            resolved_exclude: None,
        }
    }
}

#[pymethods]
impl SerializationIterator {
    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        self.py_gc_traverse(&visit)
    }

    fn __clear__(&mut self) {
        self.extra_owned.model = None;
        self.extra_owned.fallback = None;
        self.extra_owned.context = None;
        self.resolved_include = None;
        self.resolved_exclude = None;
    }

    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__(&mut self, py: Python) -> PyResult<Option<Py<PyAny>>> {
        let iterator = self.iterator.bind(py);
        let state = &mut self.extra_owned.to_state(py);
        let filter = if self.resolved_filters {
            SequenceFilter::from_resolved(
                &self.filter,
                IncludeExclude::new(
                    self.resolved_include.as_ref().map(|v| v.bind(py).clone()),
                    self.resolved_exclude.as_ref().map(|v| v.bind(py).clone()),
                ),
            )
        } else {
            self.filter.for_sequence(state, None)
        };

        for iter_result in iterator.clone() {
            let element = iter_result?;
            let op_next = filter.index_filter(self.index)?;
            if !self.resolved_filters {
                let resolved = filter.resolved()?;
                self.resolved_include = resolved.include.as_ref().map(|v| v.clone().unbind());
                self.resolved_exclude = resolved.exclude.as_ref().map(|v| v.clone().unbind());
                self.resolved_filters = true;
            }
            self.index += 1;
            if let Some(next_include_exclude) = op_next {
                let state = &mut state.scoped_include_exclude(next_include_exclude);
                let v = self.item_serializer.to_python(&element, state)?;
                state.warnings.final_check(py)?;
                return Ok(Some(v));
            }
        }
        Ok(None)
    }

    fn __repr__(&self, py: Python) -> PyResult<String> {
        let iterator = self.iterator.bind(py);
        Ok(format!(
            "SerializationIterator(index={}, iterator={})",
            self.index,
            iterator.repr()?
        ))
    }

    fn __str__(&self, py: Python) -> PyResult<String> {
        self.__repr__(py)
    }
}
