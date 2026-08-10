use std::borrow::Cow;
use std::sync::Arc;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyBool, PyDict, PyInt, PyList, PyString};

use pyo3::IntoPyObjectExt;
use serde::Serialize;

use crate::build_tools::{composed_name, py_schema_err};
use crate::definitions::DefinitionsBuilder;
use crate::serializers::SerializationState;
use crate::tools::{BuildHashSet, SchemaDict};

use super::{
    BuildSerializer, CombinedSerializer, SerMode, TypeSerializer, infer_json_key, infer_serialize, infer_to_python,
    py_err_se_err,
};

#[derive(Debug)]
pub struct LiteralSerializer {
    expected_int: Box<BuildHashSet<i64>>,
    expected_str: Box<BuildHashSet<String>>,
    expected_py: Option<Py<PyList>>,
    name: String,
}

impl BuildSerializer for LiteralSerializer {
    const EXPECTED_TYPE: &'static str = "literal";

    fn build(
        schema: &Bound<'_, PyDict>,
        _config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        let expected: Bound<'_, PyList> = schema.get_as_req(intern!(schema.py(), "expected"))?;

        if expected.is_empty() {
            return py_schema_err!("`expected` should have length > 0");
        }
        let mut expected_int = BuildHashSet::default();
        let mut expected_str = BuildHashSet::default();
        let py = expected.py();
        // only created if needed (bools and non int/str values)
        let mut expected_py: Option<Bound<'_, PyList>> = None;
        let mut repr_args: Vec<String> = Vec::with_capacity(expected.len());
        for item in expected {
            repr_args.push(item.repr()?.to_cow()?.into_owned());
            if let Ok(bool) = item.cast::<PyBool>() {
                expected_py.get_or_insert_with(|| PyList::empty(py)).append(bool)?;
            } else if let Some(int) = extract_int(&item) {
                expected_int.insert(int);
            } else if let Ok(py_str) = item.cast::<PyString>() {
                expected_str.insert(py_str.to_str()?.to_string());
            } else {
                expected_py.get_or_insert_with(|| PyList::empty(py)).append(item)?;
            }
        }

        Ok(Arc::new(
            Self {
                expected_int: Box::new(expected_int),
                expected_str: Box::new(expected_str),
                expected_py: expected_py.map(Into::into),
                name: composed_name(
                    Self::EXPECTED_TYPE,
                    &repr_args.iter().map(String::as_str).collect::<Vec<_>>(),
                    ",",
                ),
            }
            .into(),
        ))
    }
}

/// `item.extract::<i64>().ok()`, without creating (and discarding) a Python `TypeError` for the very
/// common case of objects that cannot be interpreted as an integer at all (e.g. `str` literals).
fn extract_int(item: &Bound<'_, PyAny>) -> Option<i64> {
    // SAFETY: PyIndex_Check only inspects the type's slots
    if item.is_instance_of::<PyInt>() || unsafe { pyo3::ffi::PyIndex_Check(item.as_ptr()) } != 0 {
        item.extract().ok()
    } else {
        None
    }
}

enum OutputValue<'py> {
    OkInt(i64),
    OkStr(Bound<'py, PyString>),
    Ok,
    Fallback,
}

impl LiteralSerializer {
    fn check<'py>(&self, value: &Bound<'py, PyAny>, state: &SerializationState<'py>) -> PyResult<OutputValue<'py>> {
        if state.check.enabled() {
            if !self.expected_int.is_empty()
                && !value.is_instance_of::<PyBool>()
                && let Ok(int) = value.extract()
                && self.expected_int.contains(&int)
            {
                return Ok(OutputValue::OkInt(int));
            }
            if !self.expected_str.is_empty()
                && let Ok(py_str) = value.cast::<PyString>()
            {
                let s = py_str.to_str()?;
                if self.expected_str.contains(s) {
                    return Ok(OutputValue::OkStr(PyString::new(value.py(), s)));
                }
            }

            if let Some(ref expected_py) = self.expected_py
                && expected_py.bind(value.py()).contains(value)?
            {
                return Ok(OutputValue::Ok);
            }
            Ok(OutputValue::Fallback)
        } else {
            Ok(OutputValue::Ok)
        }
    }
}

impl_py_gc_traverse!(LiteralSerializer { expected_py });

impl TypeSerializer for LiteralSerializer {
    fn to_python<'py>(&self, value: &Bound<'py, PyAny>, state: &mut SerializationState<'py>) -> PyResult<Py<PyAny>> {
        let py = value.py();
        match self.check(value, state)? {
            OutputValue::OkInt(int) => match state.extra.mode {
                SerMode::Json => int.into_py_any(py),
                _ => Ok(value.clone().unbind()),
            },
            OutputValue::OkStr(s) => match state.extra.mode {
                SerMode::Json => Ok(s.into()),
                _ => Ok(value.clone().unbind()),
            },
            OutputValue::Ok => infer_to_python(value, state),
            OutputValue::Fallback => {
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
        match self.check(key, state)? {
            OutputValue::OkInt(int) => Ok(Cow::Owned(int.to_string())),
            OutputValue::OkStr(s) => Ok(Cow::Owned(s.to_string_lossy().into_owned())),
            OutputValue::Ok => infer_json_key(key, state),
            OutputValue::Fallback => {
                state.warn_fallback_py(self.get_name(), key)?;
                infer_json_key(key, state)
            }
        }
    }

    fn serde_serialize<'py, S: serde::ser::Serializer>(
        &self,
        value: &Bound<'py, PyAny>,
        serializer: S,
        state: &mut SerializationState<'py>,
    ) -> Result<S::Ok, S::Error> {
        match self.check(value, state).map_err(py_err_se_err)? {
            OutputValue::OkInt(int) => int.serialize(serializer),
            OutputValue::OkStr(s) => s.to_string_lossy().serialize(serializer),
            OutputValue::Ok => infer_serialize(value, serializer, state),
            OutputValue::Fallback => {
                state.warn_fallback_ser::<S>(self.get_name(), value)?;
                infer_serialize(value, serializer, state)
            }
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}
