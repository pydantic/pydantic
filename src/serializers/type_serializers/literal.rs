use std::borrow::Cow;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyBool, PyDict, PyList, PyString};

use ahash::AHashSet;
use serde::Serialize;

use crate::build_tools::py_schema_err;
use crate::definitions::DefinitionsBuilder;
use crate::tools::{extract_i64, SchemaDict};

use super::{
    infer_json_key, infer_serialize, infer_to_python, py_err_se_err, BuildSerializer, CombinedSerializer, Extra,
    SerMode, TypeSerializer,
};

#[derive(Debug, Clone)]
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
        _definitions: &mut DefinitionsBuilder<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let expected: Bound<'_, PyList> = schema.get_as_req(intern!(schema.py(), "expected"))?;

        if expected.is_empty() {
            return py_schema_err!("`expected` should have length > 0");
        }
        let mut expected_int = AHashSet::new();
        let mut expected_str = AHashSet::new();
        let py = expected.py();
        let expected_py = PyList::empty_bound(py);
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

        Ok(Self {
            expected_int,
            expected_str,
            expected_py: match expected_py.is_empty() {
                true => None,
                false => Some(expected_py.into()),
            },
            name: format!("{}[{}]", Self::EXPECTED_TYPE, repr_args.join(",")),
        }
        .into())
    }
}

enum OutputValue<'py> {
    OkInt(i64),
    OkStr(Bound<'py, PyString>),
    Ok,
    Fallback,
}

impl LiteralSerializer {
    fn check<'py>(&self, value: &Bound<'py, PyAny>, extra: &Extra) -> PyResult<OutputValue<'py>> {
        if extra.check.enabled() {
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
                        return Ok(OutputValue::OkStr(py_str.clone()));
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
    fn to_python(
        &self,
        value: &Bound<'_, PyAny>,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        let py = value.py();
        match self.check(value, extra)? {
            OutputValue::OkInt(int) => match extra.mode {
                SerMode::Json => Ok(int.to_object(py)),
                _ => Ok(value.to_object(py)),
            },
            OutputValue::OkStr(s) => match extra.mode {
                SerMode::Json => Ok(s.to_object(py)),
                _ => Ok(value.to_object(py)),
            },
            OutputValue::Ok => infer_to_python(value, include, exclude, extra),
            OutputValue::Fallback => {
                extra.warnings.on_fallback_py(self.get_name(), value, extra)?;
                infer_to_python(value, include, exclude, extra)
            }
        }
    }

    fn json_key<'a>(&self, key: &'a Bound<'_, PyAny>, extra: &Extra) -> PyResult<Cow<'a, str>> {
        match self.check(key, extra)? {
            OutputValue::OkInt(int) => Ok(Cow::Owned(int.to_string())),
            OutputValue::OkStr(s) => Ok(Cow::Owned(s.to_string_lossy().into_owned())),
            OutputValue::Ok => infer_json_key(key, extra),
            OutputValue::Fallback => {
                extra.warnings.on_fallback_py(self.get_name(), key, extra)?;
                infer_json_key(key, extra)
            }
        }
    }

    fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        value: &Bound<'_, PyAny>,
        serializer: S,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> Result<S::Ok, S::Error> {
        match self.check(value, extra).map_err(py_err_se_err)? {
            OutputValue::OkInt(int) => int.serialize(serializer),
            OutputValue::OkStr(s) => s.to_string_lossy().serialize(serializer),
            OutputValue::Ok => infer_serialize(value, serializer, include, exclude, extra),
            OutputValue::Fallback => {
                extra.warnings.on_fallback_ser::<S>(self.get_name(), value, extra)?;
                infer_serialize(value, serializer, include, exclude, extra)
            }
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}
