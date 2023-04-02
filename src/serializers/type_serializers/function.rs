use std::borrow::Cow;
use std::str::FromStr;

use pyo3::exceptions::{PyAttributeError, PyRuntimeError};
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use pyo3::types::PyString;
use serde::ser::Error;

use crate::build_context::BuildContext;
use crate::build_tools::{destructure_function_schema, function_name, py_error_type, SchemaDict};
use crate::serializers::extra::{ExtraOwned, SerMode};
use crate::serializers::filter::AnyFilter;
use crate::{PydanticOmit, PydanticSerializationUnexpectedValue};

use super::format::WhenUsed;

use super::{
    infer_json_key, infer_json_key_known, infer_serialize, infer_serialize_known, infer_to_python,
    infer_to_python_known, py_err_se_err, BuildSerializer, CombinedSerializer, Extra, ObType,
    PydanticSerializationError, TypeSerializer,
};

pub struct FunctionBeforeSerializerBuilder;

impl BuildSerializer for FunctionBeforeSerializerBuilder {
    const EXPECTED_TYPE: &'static str = "function-before";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let py = schema.py();
        // `before` schemas will obviously have type from `schema` since the validator is called second
        let schema = schema.get_as_req(intern!(py, "schema"))?;
        CombinedSerializer::build(schema, config, build_context)
    }
}

pub struct FunctionAfterSerializerBuilder;

impl BuildSerializer for FunctionAfterSerializerBuilder {
    const EXPECTED_TYPE: &'static str = "function-after";
    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let py = schema.py();
        // while `before` schemas have an obvious type, for
        // `after` schemas it's less, clear but the default will be the same type, and the user/lib can always
        // override the serializer
        let schema = schema.get_as_req(intern!(py, "schema"))?;
        CombinedSerializer::build(schema, config, build_context)
    }
}

pub struct FunctionPlainSerializerBuilder;

impl BuildSerializer for FunctionPlainSerializerBuilder {
    const EXPECTED_TYPE: &'static str = "function-plain";
    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        super::any::AnySerializer::build(schema, config, build_context)
    }
}

#[derive(Debug, Clone)]
pub struct FunctionPlainSerializer {
    func: PyObject,
    name: String,
    function_name: String,
    json_return_ob_type: Option<ObType>,
    when_used: WhenUsed,
    is_field_serializer: bool,
}

impl BuildSerializer for FunctionPlainSerializer {
    const EXPECTED_TYPE: &'static str = "function-plain";

    /// NOTE! `schema` here is the actual `CoreSchema`, not `schema.serialization` as in the other builders
    /// (done this way to match `FunctionWrapSerializer` which requires the full schema)
    fn build(
        schema: &PyDict,
        _config: Option<&PyDict>,
        _build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let py = schema.py();

        let ser_schema: &PyDict = schema.get_as_req(intern!(py, "serialization"))?;

        let (is_field_serializer, function) = destructure_function_schema(ser_schema)?;
        let function_name = function_name(function)?;

        let name = format!("plain_function[{function_name}]");
        Ok(Self {
            func: function.into_py(py),
            function_name,
            name,
            json_return_ob_type: get_json_return_type(ser_schema)?,
            when_used: WhenUsed::new(ser_schema, WhenUsed::Always)?,
            is_field_serializer,
        }
        .into())
    }
}

impl FunctionPlainSerializer {
    fn call(
        &self,
        value: &PyAny,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        let py = value.py();
        if self.when_used.should_use(value, extra) {
            let info = SerializationInfo::new(py, include, exclude, extra, self.is_field_serializer)?;
            if self.is_field_serializer {
                match extra.model {
                    Some(model) => self.func.call1(py, (model, value, info)),
                    _ => Err(PyRuntimeError::new_err("This serializer expected to be run inside the context of a model field but no model field was found")),
                }
            } else {
                self.func.call1(py, (value, info))
            }
        } else {
            Ok(value.into_py(py))
        }
    }
}

macro_rules! function_type_serializer {
    ($name:ident) => {
        impl TypeSerializer for $name {
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
                            // None for include/exclude here, as filtering should be done
                            SerMode::Json => match self.json_return_ob_type {
                                Some(ref ob_type) => infer_to_python_known(ob_type, next_value, None, None, extra),
                                None => infer_to_python(next_value, None, None, extra),
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
                            // None for include/exclude here, as filtering should be done
                        match self.json_return_ob_type {
                            Some(ref ob_type) => {
                                infer_serialize_known(ob_type, next_value, serializer, None, None, extra)
                            }
                            None => infer_serialize(next_value, serializer, None, None, extra),
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
    };
}

function_type_serializer!(FunctionPlainSerializer);

pub struct FunctionWrapSerializerBuilder;

impl BuildSerializer for FunctionWrapSerializerBuilder {
    const EXPECTED_TYPE: &'static str = "function-wrap";
    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        super::any::AnySerializer::build(schema, config, build_context)
    }
}

#[derive(Debug, Clone)]
pub struct FunctionWrapSerializer {
    serializer: Box<CombinedSerializer>,
    func: PyObject,
    name: String,
    function_name: String,
    json_return_ob_type: Option<ObType>,
    when_used: WhenUsed,
    is_field_serializer: bool,
}

impl BuildSerializer for FunctionWrapSerializer {
    const EXPECTED_TYPE: &'static str = "function-wrap";

    /// NOTE! `schema` here is the actual `CoreSchema`, not `schema.serialization` as in the other builders
    /// (done this way since we need the `CoreSchema`)
    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let py = schema.py();
        let ser_schema: &PyDict = schema.get_as_req(intern!(py, "serialization"))?;

        let (is_field_serializer, function) = destructure_function_schema(ser_schema)?;
        let function_name = function_name(function)?;

        // try to get `schema.serialization.schema`, otherwise use `schema` with `serialization` key removed
        let inner_schema: &PyDict = if let Some(s) = ser_schema.get_as(intern!(py, "schema"))? {
            s
        } else {
            // we copy the schema so we can modify it without affecting the original
            let schema_copy = schema.copy()?;
            // remove the serialization key from the schema so we don't recurse
            schema_copy.del_item(intern!(py, "serialization"))?;
            schema_copy
        };

        let serializer = CombinedSerializer::build(inner_schema, config, build_context)?;

        let name = format!("wrap_function[{function_name}, {}]", serializer.get_name());
        Ok(Self {
            serializer: Box::new(serializer),
            func: function.into_py(py),
            function_name,
            name,
            json_return_ob_type: get_json_return_type(ser_schema)?,
            when_used: WhenUsed::new(ser_schema, WhenUsed::Always)?,
            is_field_serializer,
        }
        .into())
    }
}

impl FunctionWrapSerializer {
    fn call(
        &self,
        value: &PyAny,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        let py = value.py();
        if self.when_used.should_use(value, extra) {
            let serialize = SerializationCallable::new(py, &self.serializer, include, exclude, extra);
            let info = SerializationInfo::new(py, include, exclude, extra, self.is_field_serializer)?;
            if self.is_field_serializer {
                match extra.model {
                    Some(model) => self.func.call1(py, (model, value, serialize, info)),
                    _ => Err(PyRuntimeError::new_err("This serializer expected to be run inside the context of a model field but no model field was found")),
                }
            } else {
                self.func.call1(py, (value, serialize, info))
            }
        } else {
            Ok(value.into_py(py))
        }
    }
}

function_type_serializer!(FunctionWrapSerializer);

#[pyclass(module = "pydantic_core._pydantic_core")]
#[derive(Clone)]
#[cfg_attr(debug_assertions, derive(Debug))]
pub(crate) struct SerializationCallable {
    serializer: CombinedSerializer,
    extra_owned: ExtraOwned,
    filter: AnyFilter,
    include: Option<PyObject>,
    exclude: Option<PyObject>,
}

impl SerializationCallable {
    pub fn new(
        py: Python,
        serializer: &CombinedSerializer,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> Self {
        Self {
            serializer: serializer.clone(),
            extra_owned: ExtraOwned::new(extra),
            filter: AnyFilter::new(),
            include: include.map(|v| v.into_py(py)),
            exclude: exclude.map(|v| v.into_py(py)),
        }
    }
}

#[pymethods]
impl SerializationCallable {
    fn __call__(&mut self, py: Python, value: &PyAny, index_key: Option<&PyAny>) -> PyResult<Option<PyObject>> {
        let include = self.include.as_ref().map(|o| o.as_ref(py));
        let exclude = self.exclude.as_ref().map(|o| o.as_ref(py));
        let extra = self.extra_owned.to_extra(py);

        if let Some(index_key) = index_key {
            let filter = if let Ok(index) = index_key.extract::<usize>() {
                self.filter.index_filter(index, include, exclude)?
            } else {
                self.filter.key_filter(index_key, include, exclude)?
            };
            if let Some((next_include, next_exclude)) = filter {
                let v = self.serializer.to_python(value, next_include, next_exclude, &extra)?;
                extra.warnings.final_check(py)?;
                Ok(Some(v))
            } else {
                Err(PydanticOmit::new_err())
            }
        } else {
            let v = self.serializer.to_python(value, include, exclude, &extra)?;
            extra.warnings.final_check(py)?;
            Ok(Some(v))
        }
    }

    fn __repr__(&self) -> PyResult<String> {
        Ok(format!(
            "SerializationCallable(serializer={})",
            self.serializer.get_name()
        ))
    }

    fn __str__(&self) -> PyResult<String> {
        self.__repr__()
    }
}

fn get_json_return_type(schema: &PyDict) -> PyResult<Option<ObType>> {
    match schema.get_as::<&str>(intern!(schema.py(), "json_return_type"))? {
        Some(t) => Ok(Some(
            ObType::from_str(t).map_err(|_| py_error_type!("Unknown return type {:?}", t))?,
        )),
        None => Ok(None),
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
    field_name: Option<String>,
}

impl SerializationInfo {
    fn new(
        py: Python,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
        is_field_serializer: bool,
    ) -> PyResult<Self> {
        if is_field_serializer {
            match extra.field_name {
                Some(field_name) => Ok(
                    Self {
                        include: include.map(|i| i.into_py(py)),
                        exclude: exclude.map(|e| e.into_py(py)),
                        _mode: extra.mode.clone(),
                        by_alias: extra.by_alias,
                        exclude_unset: extra.exclude_unset,
                        exclude_defaults: extra.exclude_defaults,
                        exclude_none: extra.exclude_none,
                        round_trip: extra.round_trip,
                        field_name: Some(field_name.to_string()),
                    }
                ),
                _ => Err(PyRuntimeError::new_err("This serializer expected to be run inside the context of a model field but no model field was found")),
            }
        } else {
            Ok(Self {
                include: include.map(|i| i.into_py(py)),
                exclude: exclude.map(|e| e.into_py(py)),
                _mode: extra.mode.clone(),
                by_alias: extra.by_alias,
                exclude_unset: extra.exclude_unset,
                exclude_defaults: extra.exclude_defaults,
                exclude_none: extra.exclude_none,
                round_trip: extra.round_trip,
                field_name: None,
            })
        }
    }
}

#[pymethods]
impl SerializationInfo {
    #[getter]
    fn mode(&self, py: Python) -> PyObject {
        self._mode.to_object(py)
    }

    fn mode_is_json(&self) -> bool {
        self._mode.is_json()
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
    #[getter]
    fn get_field_name<'py>(&self, py: Python<'py>) -> PyResult<&'py PyString> {
        match self.field_name {
            Some(ref field_name) => Ok(PyString::new(py, field_name)),
            None => Err(PyAttributeError::new_err("No attribute named 'field_name'")),
        }
    }
}

fn py_bool(value: bool) -> &'static str {
    if value {
        "True"
    } else {
        "False"
    }
}
