use pyo3::prelude::*;
use pyo3::types::{PyDict, PyTuple, PyType};
use pyo3::{PyTraverseError, PyVisit};

use crate::py_gc::PyGcTraverse;
use crate::serializers::{SchemaSerializer, SerializerPart};
use crate::validators::{SchemaValidator, ValidatorPart};

/// Data shared by the validator and serializer built from a single core schema.
///
/// This is the unified structure behind `SchemaValidator`, `SchemaSerializer` and
/// `SchemaCore`: the two former pyclasses are thin views holding a `Py<SchemaCore>`,
/// which owns this data. When only one of validation or serialization is needed
/// (e.g. direct construction of a `SchemaValidator`), the other part is simply
/// `None`. When both are needed, constructing a `SchemaCore` builds both parts
/// around a single shared owner, so common data (schema and config references,
/// and in the future shared build artifacts) is stored only once.
///
/// Note on garbage collection: because the two views can both reach this data, it
/// is owned by a single Python object (`SchemaCore`) which the views reference and
/// traverse. This keeps the CPython GC invariant that every strong reference is
/// reported exactly once: only `SchemaCore.__traverse__` reports the references
/// held by the validator/serializer trees.
#[derive(Debug)]
pub struct SchemaCoreData {
    // References to the Python schema and config objects are saved to enable
    // reconstructing the objects for (cloud)pickle support (see `__reduce__`).
    pub(crate) py_schema: Py<PyAny>,
    pub(crate) py_config: Option<Py<PyDict>>,
    pub(crate) validator: Option<ValidatorPart>,
    pub(crate) serializer: Option<SerializerPart>,
}

impl_py_gc_traverse!(SchemaCoreData {
    py_schema,
    py_config,
    validator,
    serializer
});

impl SchemaCoreData {
    pub fn build(
        py: Python,
        schema: &Bound<'_, PyAny>,
        config: Option<&Bound<'_, PyDict>>,
        use_prebuilt: bool,
        with_validator: bool,
        with_serializer: bool,
    ) -> PyResult<Self> {
        let validator = if with_validator {
            Some(ValidatorPart::build(py, schema, config, use_prebuilt)?)
        } else {
            None
        };
        let serializer = if with_serializer {
            Some(SerializerPart::build(schema.cast()?, config, use_prebuilt)?)
        } else {
            None
        };
        Ok(Self {
            py_schema: schema.clone().unbind(),
            py_config: match config {
                Some(c) if !c.is_empty() => Some(c.clone().into()),
                _ => None,
            },
            validator,
            serializer,
        })
    }

    pub(crate) fn validator_part(&self) -> &ValidatorPart {
        self.validator
            .as_ref()
            .expect("SchemaCoreData without a validator part accessed through a validator view")
    }

    pub(crate) fn serializer_part(&self) -> &SerializerPart {
        self.serializer
            .as_ref()
            .expect("SchemaCoreData without a serializer part accessed through a serializer view")
    }
}

/// Unified owner of the validation and serialization machinery for a core schema.
///
/// The `validator` and `serializer` attributes expose regular `SchemaValidator` /
/// `SchemaSerializer` objects which share this same underlying [`SchemaCoreData`],
/// making this cheaper than constructing the two separately.
#[pyclass(module = "pydantic_core._pydantic_core", frozen)]
#[derive(Debug)]
pub struct SchemaCore {
    pub(crate) data: SchemaCoreData,
}

impl SchemaCore {
    /// Create a `SchemaCore` Python object owning already-built data. Used by the
    /// `SchemaValidator` / `SchemaSerializer` constructors, which build a core with
    /// a single part.
    pub(crate) fn new_py(py: Python, data: SchemaCoreData) -> PyResult<Py<Self>> {
        Py::new(py, Self { data })
    }
}

#[pymethods]
impl SchemaCore {
    #[new]
    #[pyo3(signature = (schema, config=None, _use_prebuilt=true))]
    pub fn py_new(
        py: Python,
        schema: &Bound<'_, PyAny>,
        config: Option<&Bound<'_, PyDict>>,
        _use_prebuilt: bool,
    ) -> PyResult<Self> {
        let data = SchemaCoreData::build(py, schema, config, _use_prebuilt, true, true)?;
        Ok(Self { data })
    }

    #[getter]
    pub fn validator(slf: &Bound<'_, Self>) -> PyResult<SchemaValidator> {
        slf.get().data.validator_part(); // assert the part exists
        Ok(SchemaValidator::from_core(slf.clone().unbind()))
    }

    #[getter]
    pub fn serializer(slf: &Bound<'_, Self>) -> PyResult<SchemaSerializer> {
        slf.get().data.serializer_part(); // assert the part exists
        Ok(SchemaSerializer::from_core(slf.clone().unbind()))
    }

    pub fn __reduce__<'py>(slf: &Bound<'py, Self>) -> PyResult<(Bound<'py, PyType>, Bound<'py, PyTuple>)> {
        // Passing _use_prebuilt=false avoids reusing prebuilt validators/serializers when unpickling
        let data = &slf.get().data;
        let init_args = (&data.py_schema, &data.py_config, false).into_pyobject(slf.py())?;
        Ok((slf.get_type(), init_args))
    }

    pub fn __repr__(&self, py: Python) -> String {
        format!(
            "SchemaCore(title={:?})",
            self.data.validator_part().title.extract::<&str>(py).unwrap_or("...")
        )
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        self.data.py_gc_traverse(&visit)
    }
}
