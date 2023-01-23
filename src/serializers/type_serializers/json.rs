use std::borrow::Cow;
use std::str::from_utf8;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use serde::ser::Error;

use crate::build_context::BuildContext;
use crate::build_tools::SchemaDict;

use super::any::AnySerializer;
use super::{
    infer_json_key, py_err_se_err, to_json_bytes, utf8_py_error, BuildSerializer, CombinedSerializer, Extra,
    TypeSerializer,
};

#[derive(Debug, Clone)]
pub struct JsonSerializer {
    serializer: Box<CombinedSerializer>,
}

impl BuildSerializer for JsonSerializer {
    const EXPECTED_TYPE: &'static str = "json";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let py = schema.py();

        let serializer = match schema.get_as::<&PyDict>(intern!(py, "schema"))? {
            Some(items_schema) => CombinedSerializer::build(items_schema, config, build_context)?,
            None => AnySerializer::build(schema, config, build_context)?,
        };
        Ok(Self {
            serializer: Box::new(serializer),
        }
        .into())
    }
}

impl TypeSerializer for JsonSerializer {
    fn to_python(
        &self,
        value: &PyAny,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        if extra.round_trip {
            let bytes = to_json_bytes(value, &self.serializer, include, exclude, extra, None, 0)?;
            let py = value.py();
            let s = from_utf8(&bytes).map_err(|e| utf8_py_error(py, e, &bytes))?;
            Ok(s.to_object(py))
        } else {
            self.serializer.to_python(value, include, exclude, extra)
        }
    }

    fn json_key<'py>(&self, key: &'py PyAny, extra: &Extra) -> PyResult<Cow<'py, str>> {
        if extra.round_trip {
            let bytes = to_json_bytes(key, &self.serializer, None, None, extra, None, 0)?;
            let py = key.py();
            let s = from_utf8(&bytes).map_err(|e| utf8_py_error(py, e, &bytes))?;
            Ok(Cow::Owned(s.to_string()))
        } else {
            infer_json_key(key, extra)
        }
    }

    fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        value: &PyAny,
        serializer: S,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> Result<S::Ok, S::Error> {
        if extra.round_trip {
            let bytes =
                to_json_bytes(value, &self.serializer, include, exclude, extra, None, 0).map_err(py_err_se_err)?;
            match from_utf8(&bytes) {
                Ok(s) => serializer.serialize_str(s),
                Err(e) => Err(Error::custom(e.to_string())),
            }
        } else {
            self.serializer
                .serde_serialize(value, serializer, include, exclude, extra)
        }
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}
