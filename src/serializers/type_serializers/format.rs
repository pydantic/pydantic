use std::borrow::Cow;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};

use serde::ser::Error;

use crate::build_context::BuildContext;
use crate::build_tools::SchemaDict;
use crate::errors::PydanticSerializationError;

use super::any::fallback_json_key;
use super::string::serialize_py_str;
use super::{py_err_se_err, BuildSerializer, CombinedSerializer, Extra, TypeSerializer};

#[derive(Debug, Clone)]
pub struct FunctionSerializer {
    format_func: PyObject,
    formatting_string: Py<PyString>,
}

impl BuildSerializer for FunctionSerializer {
    const EXPECTED_TYPE: &'static str = "format";

    fn build(
        schema: &PyDict,
        _config: Option<&PyDict>,
        _build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let py = schema.py();
        Ok(Self {
            format_func: py
                .import(intern!(py, "builtins"))?
                .getattr(intern!(py, "format"))?
                .into_py(py),
            formatting_string: schema.get_as_req(intern!(py, "formatting_string"))?,
        }
        .into())
    }
}
impl FunctionSerializer {
    fn call(&self, value: &PyAny) -> Result<PyObject, String> {
        let py = value.py();
        self.format_func
            .call1(py, (value, self.formatting_string.as_ref(py)))
            .map_err(|e| {
                format!(
                    "Error calling `format(value, {})`: {}",
                    self.formatting_string
                        .as_ref(py)
                        .repr()
                        .unwrap_or_else(|_| intern!(py, "???")),
                    e
                )
            })
    }
}

impl TypeSerializer for FunctionSerializer {
    fn to_python(
        &self,
        value: &PyAny,
        _include: Option<&PyAny>,
        _exclude: Option<&PyAny>,
        _extra: &Extra,
    ) -> PyResult<PyObject> {
        self.call(value).map_err(PydanticSerializationError::new_err)
    }

    fn json_key<'py>(&self, key: &'py PyAny, extra: &Extra) -> PyResult<Cow<'py, str>> {
        let v = self.call(key).map_err(PydanticSerializationError::new_err)?;
        fallback_json_key(v.into_ref(key.py()), extra)
    }

    fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        value: &PyAny,
        serializer: S,
        _include: Option<&PyAny>,
        _exclude: Option<&PyAny>,
        _extra: &Extra,
    ) -> Result<S::Ok, S::Error> {
        match self.call(value) {
            Ok(v) => {
                let py_str: &PyString = v.downcast(value.py()).map_err(py_err_se_err)?;
                serialize_py_str(py_str, serializer)
            }
            Err(e) => Err(S::Error::custom(e)),
        }
    }
}
