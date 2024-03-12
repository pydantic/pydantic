use std::borrow::Cow;

use pyo3::gc::PyVisit;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyIterator};
use pyo3::PyTraverseError;

use serde::ser::SerializeSeq;

use crate::definitions::DefinitionsBuilder;
use crate::tools::SchemaDict;

use super::any::AnySerializer;
use super::{
    infer_serialize, infer_to_python, py_err_se_err, BuildSerializer, CombinedSerializer, Extra, ExtraOwned,
    PydanticSerializer, SchemaFilter, SerMode, TypeSerializer,
};

#[derive(Debug, Clone)]
pub struct GeneratorSerializer {
    item_serializer: Box<CombinedSerializer>,
    filter: SchemaFilter<usize>,
}

impl BuildSerializer for GeneratorSerializer {
    const EXPECTED_TYPE: &'static str = "generator";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let py = schema.py();
        let item_serializer = match schema.get_as(intern!(py, "items_schema"))? {
            Some(items_schema) => CombinedSerializer::build(&items_schema, config, definitions)?,
            None => AnySerializer::build(schema, config, definitions)?,
        };
        Ok(Self {
            item_serializer: Box::new(item_serializer),
            filter: SchemaFilter::from_schema(schema)?,
        }
        .into())
    }
}

impl_py_gc_traverse!(GeneratorSerializer { item_serializer });

impl TypeSerializer for GeneratorSerializer {
    fn to_python(
        &self,
        value: &Bound<'_, PyAny>,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        match value.downcast::<PyIterator>() {
            Ok(py_iter) => {
                let py = value.py();
                match extra.mode {
                    SerMode::Json => {
                        let item_serializer = self.item_serializer.as_ref();

                        let mut items = match value.len() {
                            Ok(len) => Vec::with_capacity(len),
                            Err(_) => Vec::new(),
                        };
                        for (index, iter_result) in py_iter.clone().enumerate() {
                            let element = iter_result?;
                            let op_next = self.filter.index_filter(index, include, exclude, None)?;
                            if let Some((next_include, next_exclude)) = op_next {
                                items.push(item_serializer.to_python(
                                    &element,
                                    next_include.as_ref(),
                                    next_exclude.as_ref(),
                                    extra,
                                )?);
                            }
                        }
                        Ok(items.into_py(py))
                    }
                    _ => {
                        let iter = SerializationIterator::new(
                            py_iter,
                            self.item_serializer.as_ref().clone(),
                            self.filter.clone(),
                            include,
                            exclude,
                            extra,
                        );
                        Ok(iter.into_py(py))
                    }
                }
            }
            Err(_) => {
                extra.warnings.on_fallback_py(self.get_name(), value, extra)?;
                infer_to_python(value, include, exclude, extra)
            }
        }
    }

    fn json_key<'a>(&self, key: &'a Bound<'_, PyAny>, extra: &Extra) -> PyResult<Cow<'a, str>> {
        self._invalid_as_json_key(key, extra, Self::EXPECTED_TYPE)
    }

    fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        value: &Bound<'_, PyAny>,
        serializer: S,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> Result<S::Ok, S::Error> {
        match value.downcast::<PyIterator>() {
            Ok(py_iter) => {
                let len = match value.len() {
                    Ok(len) => Some(len),
                    Err(_) => None,
                };
                let mut seq = serializer.serialize_seq(len)?;
                let item_serializer = self.item_serializer.as_ref();

                for (index, iter_result) in py_iter.clone().enumerate() {
                    let element = iter_result.map_err(py_err_se_err)?;
                    let op_next = self
                        .filter
                        .index_filter(index, include, exclude, None)
                        .map_err(py_err_se_err)?;
                    if let Some((next_include, next_exclude)) = op_next {
                        let item_serialize = PydanticSerializer::new(
                            &element,
                            item_serializer,
                            next_include.as_ref(),
                            next_exclude.as_ref(),
                            extra,
                        );
                        seq.serialize_element(&item_serialize)?;
                    }
                }
                seq.end()
            }
            Err(_) => {
                extra.warnings.on_fallback_ser::<S>(self.get_name(), value, extra)?;
                infer_serialize(value, serializer, include, exclude, extra)
            }
        }
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}

#[pyclass(module = "pydantic_core._pydantic_core")]
#[derive(Clone)]
#[cfg_attr(debug_assertions, derive(Debug))]
pub(crate) struct SerializationIterator {
    iterator: Py<PyIterator>,
    #[pyo3(get)]
    index: usize,
    item_serializer: CombinedSerializer,
    extra_owned: ExtraOwned,
    filter: SchemaFilter<usize>,
    include: Option<PyObject>,
    exclude: Option<PyObject>,
}

impl SerializationIterator {
    pub fn new(
        py_iter: &Bound<'_, PyIterator>,
        item_serializer: CombinedSerializer,
        filter: SchemaFilter<usize>,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> Self {
        Self {
            iterator: py_iter.clone().into(),
            index: 0,
            item_serializer,
            extra_owned: ExtraOwned::new(extra),
            filter,
            include: include.map(|v| v.clone().into()),
            exclude: exclude.map(|v| v.clone().into()),
        }
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        if let Some(include) = &self.include {
            visit.call(include)?;
        }
        if let Some(exclude) = &self.exclude {
            visit.call(exclude)?;
        }
        if let Some(model) = &self.extra_owned.model {
            visit.call(model)?;
        }
        if let Some(fallback) = &self.extra_owned.fallback {
            visit.call(fallback)?;
        }
        if let Some(context) = &self.extra_owned.context {
            visit.call(context)?;
        }
        Ok(())
    }

    fn __clear__(&mut self) {
        self.include = None;
        self.exclude = None;
        self.extra_owned.model = None;
        self.extra_owned.fallback = None;
        self.extra_owned.context = None;
    }
}

#[pymethods]
impl SerializationIterator {
    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__(&mut self, py: Python) -> PyResult<Option<PyObject>> {
        let iterator = self.iterator.bind(py);
        let include = self.include.as_ref().map(|o| o.bind(py));
        let exclude = self.exclude.as_ref().map(|o| o.bind(py));
        let extra = self.extra_owned.to_extra(py);

        for iter_result in iterator.clone() {
            let element = iter_result?;
            let filter = self.filter.index_filter(self.index, include, exclude, None)?;
            self.index += 1;
            if let Some((next_include, next_exclude)) = filter {
                let v = self
                    .item_serializer
                    // TODO do we need error_on_fallback to be customizable?
                    .to_python(&element, next_include.as_ref(), next_exclude.as_ref(), &extra)?;
                extra.warnings.final_check(py)?;
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
