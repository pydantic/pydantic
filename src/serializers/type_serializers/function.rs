use std::borrow::Cow;
use std::str::FromStr;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use serde::ser::Error;

use crate::build_context::BuildContext;
use crate::build_tools::{function_name, kwargs, py_error_type, SchemaDict};
use crate::PydanticSerializationUnexpectedValue;

use super::{
    infer_json_key, infer_json_key_known, infer_serialize, infer_serialize_known, infer_to_python,
    infer_to_python_known, py_err_se_err, BuildSerializer, CombinedSerializer, Extra, ObType,
    PydanticSerializationError, TypeSerializer,
};

#[derive(Debug, Clone)]
pub struct FunctionSerializer {
    func: PyObject,
    name: String,
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
        let name = format!("function[{function_name}]");
        Ok(Self {
            func: function.into_py(py),
            function_name,
            name,
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
        extra: &Extra,
    ) -> PyResult<PyObject> {
        let py = value.py();
        let kwargs = kwargs!(py, mode: extra.mode.to_object(py), include: include, exclude: exclude);
        self.func.call(py, (value,), kwargs)
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
        match self.call(value, include, exclude, extra) {
            Ok(v) => {
                let next_value = v.as_ref(py);
                match self.return_ob_type {
                    Some(ref ob_type) => infer_to_python_known(ob_type, next_value, include, exclude, extra),
                    None => infer_to_python(next_value, include, exclude, extra),
                }
            }
            Err(err) => match err.value(py).extract::<PydanticSerializationUnexpectedValue>() {
                Ok(ser_err) => {
                    if extra.check.enabled() {
                        Err(err)
                    } else {
                        extra.warnings.custom_warning(ser_err.__repr__());
                        infer_to_python(value, include, exclude, extra)
                    }
                }
                Err(_) => {
                    let new_err = py_error_type!(PydanticSerializationError; "Error calling function `{}`: {}", self.function_name, err);
                    new_err.set_cause(py, Some(err));
                    Err(new_err)
                }
            },
        }
    }

    fn json_key<'py>(&self, key: &'py PyAny, extra: &Extra) -> PyResult<Cow<'py, str>> {
        let py = key.py();
        match self.call(key, None, None, extra) {
            Ok(v) => {
                let next_key = v.into_ref(py);
                match self.return_ob_type {
                    Some(ref ob_type) => infer_json_key_known(ob_type, next_key, extra),
                    None => infer_json_key(next_key, extra),
                }
            }
            Err(err) => match err.value(py).extract::<PydanticSerializationUnexpectedValue>() {
                Ok(ser_err) => {
                    if extra.check.enabled() {
                        Err(err)
                    } else {
                        extra.warnings.custom_warning(ser_err.__repr__());
                        infer_json_key(key, extra)
                    }
                }
                Err(_) => {
                    let new_err = py_error_type!(PydanticSerializationError; "Error calling function `{}`: {}", self.function_name, err);
                    new_err.set_cause(py, Some(err));
                    Err(new_err)
                }
            },
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
        let py = value.py();
        match self.call(value, include, exclude, extra) {
            Ok(v) => {
                let next_value = v.as_ref(py);
                match self.return_ob_type {
                    Some(ref ob_type) => {
                        infer_serialize_known(ob_type, next_value, serializer, include, exclude, extra)
                    }
                    None => infer_serialize(next_value, serializer, include, exclude, extra),
                }
            }
            Err(err) => match err.value(py).extract::<PydanticSerializationUnexpectedValue>() {
                Ok(ser_err) => {
                    if extra.check.enabled() {
                        Err(py_err_se_err(err))
                    } else {
                        extra.warnings.custom_warning(ser_err.__repr__());
                        infer_serialize(value, serializer, include, exclude, extra)
                    }
                }
                Err(_) => Err(Error::custom(format!(
                    "Error calling function `{}`: {}",
                    self.function_name, err
                ))),
            },
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}
