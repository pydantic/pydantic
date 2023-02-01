use std::borrow::Cow;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};

use serde::ser::Error;

use crate::build_context::BuildContext;
use crate::build_tools::{py_err, SchemaDict};

use super::simple::none_json_key;
use super::string::serialize_py_str;
use super::{py_err_se_err, BuildSerializer, CombinedSerializer, Extra, PydanticSerializationError, TypeSerializer};

#[derive(Debug, Clone, Eq, PartialEq)]
pub(super) enum WhenUsed {
    Always,
    UnlessNone,
    Json,
    JsonUnlessNone,
}

impl WhenUsed {
    pub fn new(schema: &PyDict, default: Self) -> PyResult<Self> {
        let when_used = schema.get_as(intern!(schema.py(), "when_used"))?;
        match when_used {
            Some("always") => Ok(Self::Always),
            Some("unless-none") => Ok(Self::UnlessNone),
            Some("json") => Ok(Self::Json),
            Some("json-unless-none") => Ok(Self::JsonUnlessNone),
            Some(s) => py_err!("Invalid value for `when_used`: {:?}", s),
            None => Ok(default),
        }
    }

    pub fn should_use(&self, value: &PyAny, extra: &Extra) -> bool {
        match self {
            Self::Always => true,
            Self::UnlessNone => !value.is_none(),
            Self::Json => extra.mode.is_json(),
            Self::JsonUnlessNone => extra.mode.is_json() && !value.is_none(),
        }
    }

    /// Equivalent to `self.should_use` when we already know we're in JSON mode
    pub fn should_use_json(&self, value: &PyAny) -> bool {
        match self {
            Self::Always | Self::Json => true,
            _ => !value.is_none(),
        }
    }
}

#[derive(Debug, Clone)]
pub struct FormatSerializer {
    format_func: PyObject,
    formatting_string: Py<PyString>,
    when_used: WhenUsed,
}

impl BuildSerializer for FormatSerializer {
    const EXPECTED_TYPE: &'static str = "format";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let py = schema.py();
        let formatting_string: &str = schema.get_as_req(intern!(py, "formatting_string"))?;
        if formatting_string.is_empty() {
            ToStringSerializer::build(schema, config, build_context)
        } else {
            Ok(Self {
                format_func: py
                    .import(intern!(py, "builtins"))?
                    .getattr(intern!(py, "format"))?
                    .into_py(py),
                formatting_string: PyString::new(py, formatting_string).into_py(py),
                when_used: WhenUsed::new(schema, WhenUsed::JsonUnlessNone)?,
            }
            .into())
        }
    }
}
impl FormatSerializer {
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

impl TypeSerializer for FormatSerializer {
    fn to_python(
        &self,
        value: &PyAny,
        _include: Option<&PyAny>,
        _exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        if self.when_used.should_use(value, extra) {
            self.call(value).map_err(PydanticSerializationError::new_err)
        } else {
            Ok(value.into_py(value.py()))
        }
    }

    fn json_key<'py>(&self, key: &'py PyAny, _extra: &Extra) -> PyResult<Cow<'py, str>> {
        if self.when_used.should_use_json(key) {
            let v = self.call(key).map_err(PydanticSerializationError::new_err)?;
            let py_str: &PyString = v.into_ref(key.py()).downcast()?;
            Ok(Cow::Borrowed(py_str.to_str()?))
        } else {
            none_json_key()
        }
    }

    fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        value: &PyAny,
        serializer: S,
        _include: Option<&PyAny>,
        _exclude: Option<&PyAny>,
        _extra: &Extra,
    ) -> Result<S::Ok, S::Error> {
        if self.when_used.should_use_json(value) {
            match self.call(value) {
                Ok(v) => {
                    let py_str: &PyString = v.downcast(value.py()).map_err(py_err_se_err)?;
                    serialize_py_str(py_str, serializer)
                }
                Err(e) => Err(S::Error::custom(e)),
            }
        } else {
            serializer.serialize_none()
        }
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}

#[derive(Debug, Clone)]
pub struct ToStringSerializer {
    when_used: WhenUsed,
}

impl BuildSerializer for ToStringSerializer {
    const EXPECTED_TYPE: &'static str = "to-string";

    fn build(
        schema: &PyDict,
        _config: Option<&PyDict>,
        _build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        Ok(Self {
            when_used: WhenUsed::new(schema, WhenUsed::JsonUnlessNone)?,
        }
        .into())
    }
}

impl TypeSerializer for ToStringSerializer {
    fn to_python(
        &self,
        value: &PyAny,
        _include: Option<&PyAny>,
        _exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        if self.when_used.should_use(value, extra) {
            value.str().map(|s| s.into_py(value.py()))
        } else {
            Ok(value.into_py(value.py()))
        }
    }

    fn json_key<'py>(&self, key: &'py PyAny, _extra: &Extra) -> PyResult<Cow<'py, str>> {
        if self.when_used.should_use_json(key) {
            Ok(key.str()?.to_string_lossy())
        } else {
            none_json_key()
        }
    }

    fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        value: &PyAny,
        serializer: S,
        _include: Option<&PyAny>,
        _exclude: Option<&PyAny>,
        _extra: &Extra,
    ) -> Result<S::Ok, S::Error> {
        if self.when_used.should_use_json(value) {
            let s = value.str().map_err(py_err_se_err)?;
            serialize_py_str(s, serializer)
        } else {
            serializer.serialize_none()
        }
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}
