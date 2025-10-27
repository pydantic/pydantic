use std::borrow::Cow;
use std::sync::Arc;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyBool, PyDict, PyList, PyString};

use ahash::AHashSet;
use pyo3::IntoPyObjectExt;
use serde::Serialize;

use crate::build_tools::py_schema_err;
use crate::definitions::DefinitionsBuilder;
use crate::serializers::SerializationState;
use crate::tools::{extract_i64, SchemaDict};

use super::{
    infer_json_key, infer_serialize, infer_to_python, py_err_se_err, BuildSerializer, CombinedSerializer, Extra,
    SerMode, TypeSerializer,
};

#[derive(Debug)]
pub struct LiteralSerializer {
    expected_int: AHashSet<i64>,
    expected_str: AHashSet<String>,
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
        let mut expected_int = AHashSet::new();
        let mut expected_str = AHashSet::new();
        let py = expected.py();
        let expected_py = PyList::empty(py);
        let mut repr_args: Vec<String> = Vec::new();
        for item in expected {
            repr_args.push(item.repr()?.extract()?);
            if let Ok(bool) = item.downcast::<PyBool>() {
                expected_py.append(bool)?;
            } else if let Some(int) = extract_i64(&item) {
                expected_int.insert(int);
            } else if let Ok(py_str) = item.downcast::<PyString>() {
                expected_str.insert(py_str.to_str()?.to_string());
            } else {
                expected_py.append(item)?;
            }
        }

        Ok(Arc::new(
            Self {
                expected_int,
                expected_str,
                expected_py: match expected_py.is_empty() {
                    true => None,
                    false => Some(expected_py.into()),
                },
                name: format!("{}[{}]", Self::EXPECTED_TYPE, repr_args.join(",")),
            }
            .into(),
        ))
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
            if !self.expected_int.is_empty() && !value.is_instance_of::<PyBool>() {
                if let Some(int) = extract_i64(value) {
                    if self.expected_int.contains(&int) {
                        return Ok(OutputValue::OkInt(int));
                    }
                }
            }
            if !self.expected_str.is_empty() {
                if let Ok(py_str) = value.downcast::<PyString>() {
                    let s = py_str.to_str()?;
                    if self.expected_str.contains(s) {
                        return Ok(OutputValue::OkStr(PyString::new(value.py(), s)));
                    }
                }
            }

            if let Some(ref expected_py) = self.expected_py {
                if expected_py.bind(value.py()).contains(value)? {
                    return Ok(OutputValue::Ok);
                }
            }
            Ok(OutputValue::Fallback)
        } else {
            Ok(OutputValue::Ok)
        }
    }
}

impl_py_gc_traverse!(LiteralSerializer { expected_py });

impl TypeSerializer for LiteralSerializer {
    fn to_python<'py>(
        &self,
        value: &Bound<'py, PyAny>,
        state: &mut SerializationState<'py>,
        extra: &Extra<'_, 'py>,
    ) -> PyResult<Py<PyAny>> {
        let py = value.py();
        match self.check(value, state)? {
            OutputValue::OkInt(int) => match extra.mode {
                SerMode::Json => int.into_py_any(py),
                _ => Ok(value.clone().unbind()),
            },
            OutputValue::OkStr(s) => match extra.mode {
                SerMode::Json => Ok(s.into()),
                _ => Ok(value.clone().unbind()),
            },
            OutputValue::Ok => infer_to_python(value, state, extra),
            OutputValue::Fallback => {
                state.warn_fallback_py(self.get_name(), value)?;
                infer_to_python(value, state, extra)
            }
        }
    }

    fn json_key<'a, 'py>(
        &self,
        key: &'a Bound<'py, PyAny>,
        state: &mut SerializationState<'py>,
        extra: &Extra<'_, 'py>,
    ) -> PyResult<Cow<'a, str>> {
        match self.check(key, state)? {
            OutputValue::OkInt(int) => Ok(Cow::Owned(int.to_string())),
            OutputValue::OkStr(s) => Ok(Cow::Owned(s.to_string_lossy().into_owned())),
            OutputValue::Ok => infer_json_key(key, state, extra),
            OutputValue::Fallback => {
                state.warn_fallback_py(self.get_name(), key)?;
                infer_json_key(key, state, extra)
            }
        }
    }

    fn serde_serialize<'py, S: serde::ser::Serializer>(
        &self,
        value: &Bound<'py, PyAny>,
        serializer: S,
        state: &mut SerializationState<'py>,
        extra: &Extra<'_, 'py>,
    ) -> Result<S::Ok, S::Error> {
        match self.check(value, state).map_err(py_err_se_err)? {
            OutputValue::OkInt(int) => int.serialize(serializer),
            OutputValue::OkStr(s) => s.to_string_lossy().serialize(serializer),
            OutputValue::Ok => infer_serialize(value, serializer, state, extra),
            OutputValue::Fallback => {
                state.warn_fallback_ser::<S>(self.get_name(), value)?;
                infer_serialize(value, serializer, state, extra)
            }
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}
