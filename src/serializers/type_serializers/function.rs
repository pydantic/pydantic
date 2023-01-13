use std::borrow::Cow;
use std::str::FromStr;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use serde::ser::Error;

use crate::build_context::BuildContext;
use crate::build_tools::{function_name, kwargs, py_error_type, SchemaDict};
use crate::errors::PydanticSerializationError;

use super::any::{
    fallback_json_key, fallback_serialize, fallback_serialize_known, fallback_to_python, fallback_to_python_known,
};
use super::{BuildSerializer, CombinedSerializer, Extra, ObType, SerMode, TypeSerializer};

#[derive(Debug, Clone)]
pub struct FunctionSerializer {
    func: PyObject,
    function_name: String,
    return_ob_type: Option<ObType>,
}

impl BuildSerializer for FunctionSerializer {
    // this value is never used, it's just here to satisfy the trait
    const EXPECTED_TYPE: &'static str = "";

    fn build(
        schema: &PyDict,
        _config: Option<&PyDict>,
        _build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let py = schema.py();
        let function = schema.get_as_req::<&PyAny>(intern!(py, "function"))?;
        let function_name = function_name(function)?;
        Ok(Self {
            func: function.into_py(py),
            function_name,
            return_ob_type: match schema.get_as::<&str>(intern!(py, "return_type"))? {
                Some(t) => Some(ObType::from_str(t).map_err(|_| py_error_type!("Unknown return type {:?}", t))?),
                None => None,
            },
        }
        .into())
    }
}

impl FunctionSerializer {
    fn call(
        &self,
        value: &PyAny,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        mode: &SerMode,
    ) -> Result<PyObject, String> {
        let py = value.py();
        let kwargs = kwargs!(py, mode: mode.to_object(py), include: include, exclude: exclude);
        self.func
            .call(py, (value,), kwargs)
            .map_err(|e| format!("Error calling `{}`: {}", self.function_name, e))
    }
}

impl TypeSerializer for FunctionSerializer {
    fn to_python(
        &self,
        value: &PyAny,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        let py = value.py();
        let v = self
            .call(value, include, exclude, extra.mode)
            .map_err(PydanticSerializationError::new_err)?;

        if let Some(ref ob_type) = self.return_ob_type {
            fallback_to_python_known(ob_type, v.as_ref(py), include, exclude, extra)
        } else {
            fallback_to_python(v.as_ref(py), include, exclude, extra)
        }
    }

    fn json_key<'py>(&self, key: &'py PyAny, extra: &Extra) -> PyResult<Cow<'py, str>> {
        let v = self
            .call(key, None, None, extra.mode)
            .map_err(PydanticSerializationError::new_err)?;

        fallback_json_key(v.into_ref(key.py()), extra)
    }

    fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        value: &PyAny,
        serializer: S,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> Result<S::Ok, S::Error> {
        let py = value.py();
        let return_value = self.call(value, include, exclude, extra.mode).map_err(Error::custom)?;

        if let Some(ref ob_type) = self.return_ob_type {
            fallback_serialize_known(ob_type, return_value.as_ref(py), serializer, include, exclude, extra)
        } else {
            fallback_serialize(return_value.as_ref(py), serializer, include, exclude, extra)
        }
    }
}
