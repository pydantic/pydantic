use std::borrow::Cow;
use std::str::FromStr;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use serde::ser::Error;

use crate::build_context::BuildContext;
use crate::build_tools::{function_name, py_error_type, SchemaDict};
use crate::serializers::extra::SerMode;
use crate::PydanticSerializationUnexpectedValue;

use super::format::WhenUsed;

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
    json_return_ob_type: Option<ObType>,
    when_used: WhenUsed,
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
            json_return_ob_type: match schema.get_as::<&str>(intern!(py, "json_return_type"))? {
                Some(t) => Some(ObType::from_str(t).map_err(|_| py_error_type!("Unknown return type {:?}", t))?),
                None => None,
            },
            when_used: WhenUsed::new(schema, WhenUsed::Always)?,
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
        if self.when_used.should_use(value, extra) {
            let info = SerializationInfo {
                include: include.map(|i| i.into_py(py)),
                exclude: exclude.map(|e| e.into_py(py)),
                _mode: extra.mode.clone(),
                by_alias: extra.by_alias,
                exclude_unset: extra.exclude_unset,
                exclude_defaults: extra.exclude_defaults,
                exclude_none: extra.exclude_none,
                round_trip: extra.round_trip,
            };
            self.func.call1(py, (value, info))
        } else {
            Ok(value.into_py(py))
        }
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
                match extra.mode {
                    SerMode::Json => match self.json_return_ob_type {
                        Some(ref ob_type) => infer_to_python_known(ob_type, next_value, include, exclude, extra),
                        None => infer_to_python(next_value, include, exclude, extra),
                    },
                    _ => Ok(next_value.to_object(py)),
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
                match self.json_return_ob_type {
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
                match self.json_return_ob_type {
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

#[pyclass(module = "pydantic_core._pydantic_core")]
#[cfg_attr(debug_assertions, derive(Debug))]
struct SerializationInfo {
    #[pyo3(get)]
    include: Option<PyObject>,
    #[pyo3(get)]
    exclude: Option<PyObject>,
    _mode: SerMode,
    #[pyo3(get)]
    by_alias: bool,
    #[pyo3(get)]
    exclude_unset: bool,
    #[pyo3(get)]
    exclude_defaults: bool,
    #[pyo3(get)]
    exclude_none: bool,
    #[pyo3(get)]
    round_trip: bool,
}

#[pymethods]
impl SerializationInfo {
    #[getter]
    fn mode(&self, py: Python) -> PyObject {
        self._mode.to_object(py)
    }

    #[getter]
    fn __dict__<'py>(&'py self, py: Python<'py>) -> PyResult<&'py PyDict> {
        let d = PyDict::new(py);
        if let Some(ref include) = self.include {
            d.set_item("include", include)?;
        }
        if let Some(ref exclude) = self.exclude {
            d.set_item("exclude", exclude)?;
        }
        d.set_item("mode", self.mode(py))?;
        d.set_item("by_alias", self.by_alias)?;
        d.set_item("exclude_unset", self.exclude_unset)?;
        d.set_item("exclude_defaults", self.exclude_defaults)?;
        d.set_item("exclude_none", self.exclude_none)?;
        d.set_item("round_trip", self.round_trip)?;
        Ok(d)
    }

    fn __repr__(&self, py: Python) -> PyResult<String> {
        Ok(format!(
            "SerializationInfo(include={}, exclude={}, mode='{}', by_alias={}, exclude_unset={}, exclude_defaults={}, exclude_none={}, round_trip={})",
            match self.include {
                Some(ref include) => include.as_ref(py).repr()?.to_str()?,
                None => "None",
            },
            match self.exclude {
                Some(ref exclude) => exclude.as_ref(py).repr()?.to_str()?,
                None => "None",
            },
            self._mode,
            py_bool(self.by_alias),
            py_bool(self.exclude_unset),
            py_bool(self.exclude_defaults),
            py_bool(self.exclude_none),
            py_bool(self.round_trip),
        ))
    }

    fn __str__(&self, py: Python) -> PyResult<String> {
        self.__repr__(py)
    }
}

fn py_bool(value: bool) -> &'static str {
    if value {
        "True"
    } else {
        "False"
    }
}
