use std::borrow::Cow;
use std::sync::Arc;

use pyo3::PyTraverseError;
use pyo3::exceptions::{PyAttributeError, PyRecursionError, PyRuntimeError};
use pyo3::gc::PyVisit;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use pyo3::types::PyString;

use crate::definitions::DefinitionsBuilder;
use crate::py_gc::PyGcTraverse;
use crate::serializers::SerializationState;
use crate::serializers::extra::IncludeExclude;
use crate::tools::SchemaDict;
use crate::tools::{function_name, py_err, py_error_type};
use crate::{PydanticOmit, PydanticSerializationUnexpectedValue};

use super::format::WhenUsed;

use super::any::AnySerializer;
use super::{
    AnyFilter, BuildSerializer, CombinedSerializer, ExtraOwned, PydanticSerializationError, SerMode, TypeSerializer,
    infer_json_key, infer_serialize, infer_to_python, py_err_se_err,
};

pub struct FunctionBeforeSerializerBuilder;

impl BuildSerializer for FunctionBeforeSerializerBuilder {
    const EXPECTED_TYPE: &'static str = "function-before";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        let py = schema.py();
        // `before` schemas will obviously have type from `schema` since the validator is called second
        let schema = schema.get_as_req(intern!(py, "schema"))?;
        CombinedSerializer::build(&schema, config, definitions)
    }
}

pub struct FunctionAfterSerializerBuilder;

impl BuildSerializer for FunctionAfterSerializerBuilder {
    const EXPECTED_TYPE: &'static str = "function-after";
    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        let py = schema.py();
        // While `before` function schemas do not modify the output type (and therefore affect the
        // serialization), for `after` schemas, there's no way to directly infer what schema should
        // be used for serialization. For convenience, the default is to assume the wrapped schema
        // should be used; the user/lib can override the serializer if necessary.
        let schema = schema.get_as_req(intern!(py, "schema"))?;
        CombinedSerializer::build(&schema, config, definitions)
    }
}

pub struct FunctionPlainSerializerBuilder;

impl BuildSerializer for FunctionPlainSerializerBuilder {
    const EXPECTED_TYPE: &'static str = "function-plain";
    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        super::any::AnySerializer::build(schema, config, definitions)
    }
}

#[derive(Debug)]
pub struct FunctionPlainSerializer {
    func: Py<PyAny>,
    name: String,
    function_name: String,
    return_serializer: Arc<CombinedSerializer>,
    // fallback serializer - used when when_used decides that this serializer should not be used
    fallback_serializer: Option<Arc<CombinedSerializer>>,
    when_used: WhenUsed,
    pub(crate) is_field_serializer: bool,
    info_arg: bool,
}

fn destructure_function_schema<'py>(schema: &Bound<'py, PyDict>) -> PyResult<(bool, bool, Bound<'py, PyAny>)> {
    let function = schema.get_as_req(intern!(schema.py(), "function"))?;
    let is_field_serializer: bool = schema
        .get_as(intern!(schema.py(), "is_field_serializer"))?
        .unwrap_or(false);
    let info_arg: bool = schema.get_as(intern!(schema.py(), "info_arg"))?.unwrap_or(false);
    Ok((is_field_serializer, info_arg, function))
}

impl BuildSerializer for FunctionPlainSerializer {
    const EXPECTED_TYPE: &'static str = "function-plain";

    /// NOTE! `schema` here is the actual `CoreSchema`, not `schema.serialization` as in the other builders
    /// (done this way to match `FunctionWrapSerializer` which requires the full schema)
    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        let py = schema.py();

        let ser_schema = schema.get_as_req(intern!(py, "serialization"))?;

        let (is_field_serializer, info_arg, function) = destructure_function_schema(&ser_schema)?;
        let function_name = function_name(&function)?;

        let return_serializer = match ser_schema.get_as(intern!(py, "return_schema"))? {
            Some(s) => CombinedSerializer::build(&s, config, definitions)?,
            None => AnySerializer::build(schema, config, definitions)?,
        };

        let when_used = WhenUsed::new(&ser_schema, WhenUsed::Always)?;
        let fallback_serializer = match when_used {
            WhenUsed::Always => None,
            _ => {
                let new_schema = copy_outer_schema(schema)?;
                Some(CombinedSerializer::build(&new_schema, config, definitions)?)
            }
        };

        let name = format!("plain_function[{function_name}]");
        Ok(CombinedSerializer::Function(Self {
            func: function.unbind(),
            function_name,
            name,
            return_serializer,
            fallback_serializer,
            when_used,
            is_field_serializer,
            info_arg,
        })
        .into())
    }
}

impl FunctionPlainSerializer {
    fn call<'py>(&self, value: &Bound<'py, PyAny>, state: &mut SerializationState<'py>) -> PyResult<(bool, Py<PyAny>)> {
        let py = value.py();
        if self.when_used.should_use(value, &state.extra) {
            let v = if self.is_field_serializer {
                if let Some(model) = state.model.as_ref() {
                    if self.info_arg {
                        let info = SerializationInfo::new(state, self.is_field_serializer)?;
                        self.func.call1(py, (model, value, info))?
                    } else {
                        self.func.call1(py, (model, value))?
                    }
                } else {
                    return Err(PyRuntimeError::new_err(
                        "Function plain serializer expected to be run inside the context of a model field but no model was found",
                    ));
                }
            } else if self.info_arg {
                let info = SerializationInfo::new(state, self.is_field_serializer)?;
                self.func.call1(py, (value, info))?
            } else {
                self.func.call1(py, (value,))?
            };
            Ok((true, v))
        } else {
            Ok((false, value.clone().unbind()))
        }
    }

    fn get_fallback_serializer(&self) -> &CombinedSerializer {
        self.fallback_serializer
            .as_ref()
            .expect("fallback_serializer unexpectedly none")
            .as_ref()
    }

    fn retry_with_lax_check(&self) -> bool {
        self.fallback_serializer
            .as_ref()
            .is_some_and(|f| f.retry_with_lax_check())
            || self.return_serializer.retry_with_lax_check()
    }
}

fn on_error(py: Python, err: PyErr, function_name: &str, state: &mut SerializationState<'_>) -> PyResult<()> {
    let exception = err.value(py);
    if let Ok(ser_err) = exception.cast::<PydanticSerializationUnexpectedValue>() {
        if state.check.enabled() {
            Err(err)
        } else {
            state.warnings.register_warning(ser_err.get().clone());
            Ok(())
        }
    } else if let Ok(err) = exception.cast::<PydanticSerializationError>() {
        let err = err.get();
        py_err!(PydanticSerializationError; "{err}")
    } else if exception.is_instance_of::<PyRecursionError>() {
        py_err!(PydanticSerializationError; "Error calling function `{function_name}`: RecursionError")
    } else {
        let new_err = py_error_type!(PydanticSerializationError; "Error calling function `{function_name}`: {err}");
        new_err.set_cause(py, Some(err));
        Err(new_err)
    }
}

macro_rules! function_type_serializer {
    ($name:ident) => {
        impl TypeSerializer for $name {
            fn to_python<'py>(
                &self,
                value: &Bound<'py, PyAny>,
                state: &mut SerializationState<'py>,
            ) -> PyResult<Py<PyAny>> {
                let py = value.py();
                let (ret_serializer, v) = match self.call(value, state) {
                    Ok((true, v)) => (&*self.return_serializer, v),
                    Ok((false, v)) => (self.get_fallback_serializer(), v),
                    Err(err) => {
                        on_error(py, err, &self.function_name, state)?;
                        return infer_to_python(value, state);
                    }
                };
                // None for include/exclude here, as filtering should be done
                let state = &mut state.scoped_include_exclude(IncludeExclude::empty());
                ret_serializer.to_python(v.bind(py), state)
            }

            fn json_key<'a, 'py>(
                &self,
                key: &'a Bound<'py, PyAny>,
                state: &mut SerializationState<'py>,
            ) -> PyResult<Cow<'a, str>> {
                let py = key.py();
                let (ret_serializer, v) = match self.call(key, state) {
                    Ok((true, v)) => (&*self.return_serializer, v),
                    Ok((false, v)) => (self.get_fallback_serializer(), v),
                    Err(err) => {
                        on_error(py, err, &self.function_name, state)?;
                        return infer_json_key(key, state);
                    }
                };
                // None for include/exclude here, as filtering should be done
                let state = &mut state.scoped_include_exclude(IncludeExclude::empty());
                ret_serializer
                    .json_key(v.bind(py), state)
                    .map(|cow| Cow::Owned(cow.into_owned()))
            }

            fn serde_serialize<'py, S: serde::ser::Serializer>(
                &self,
                value: &Bound<'py, PyAny>,
                serializer: S,
                state: &mut SerializationState<'py>,
            ) -> Result<S::Ok, S::Error> {
                let py = value.py();
                let (ret_serializer, v) = match self.call(value, state) {
                    Ok((true, v)) => (&*self.return_serializer, v),
                    Ok((false, v)) => (self.get_fallback_serializer(), v),
                    Err(err) => {
                        on_error(py, err, &self.function_name, state).map_err(py_err_se_err)?;
                        return infer_serialize(value, serializer, state);
                    }
                };
                // None for include/exclude here, as filtering should be done
                let mut state = state.scoped_include_exclude(IncludeExclude::empty());
                ret_serializer.serde_serialize(v.bind(py), serializer, &mut state)
            }

            fn get_name(&self) -> &str {
                &self.name
            }

            fn retry_with_lax_check(&self) -> bool {
                self.retry_with_lax_check()
            }
        }
    };
}

impl_py_gc_traverse!(FunctionPlainSerializer {
    func,
    return_serializer,
    fallback_serializer
});

function_type_serializer!(FunctionPlainSerializer);

fn copy_outer_schema<'py>(schema: &Bound<'py, PyDict>) -> PyResult<Bound<'py, PyDict>> {
    let py = schema.py();
    // we copy the schema so we can modify it without affecting the original
    let schema_copy = schema.copy()?;
    // remove the serialization key from the schema so we don't recurse
    schema_copy.del_item(intern!(py, "serialization"))?;
    // remove ref if it exists - the point is that `schema` here has already run through
    // `CombinedSerializer::build` so "ref" here will have already been added to `Definitions::used_ref`
    // we don't want to error by "finding" it now
    schema_copy.del_item(intern!(py, "ref")).ok();
    Ok(schema_copy)
}

pub struct FunctionWrapSerializerBuilder;

impl BuildSerializer for FunctionWrapSerializerBuilder {
    const EXPECTED_TYPE: &'static str = "function-wrap";
    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        let py = schema.py();
        // While `before` function schemas do not modify the output type (and therefore affect the
        // serialization), for `wrap` schemas (like `after`), there's no way to directly infer what
        // schema should be used for serialization. For convenience, the default is to assume the
        // wrapped schema should be used; the user/lib can override the serializer if necessary.
        let schema = schema.get_as_req(intern!(py, "schema"))?;
        CombinedSerializer::build(&schema, config, definitions)
    }
}

#[derive(Debug)]
pub struct FunctionWrapSerializer {
    serializer: Arc<CombinedSerializer>,
    func: Py<PyAny>,
    name: String,
    function_name: String,
    return_serializer: Arc<CombinedSerializer>,
    when_used: WhenUsed,
    pub(crate) is_field_serializer: bool,
    info_arg: bool,
}

impl BuildSerializer for FunctionWrapSerializer {
    const EXPECTED_TYPE: &'static str = "function-wrap";

    /// NOTE! `schema` here is the actual `CoreSchema`, not `schema.serialization` as in the other builders
    /// (done this way since we need the `CoreSchema`)
    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        let py = schema.py();
        let ser_schema = schema.get_as_req(intern!(py, "serialization"))?;

        let (is_field_serializer, info_arg, function) = destructure_function_schema(&ser_schema)?;
        let function_name = function_name(&function)?;

        // try to get `schema.serialization.schema`, otherwise use `schema` with `serialization` key removed
        let inner_schema = if let Some(s) = ser_schema.get_as(intern!(py, "schema"))? {
            s
        } else {
            copy_outer_schema(schema)?
        };

        let serializer = CombinedSerializer::build(&inner_schema, config, definitions)?;

        let return_serializer = match ser_schema.get_as(intern!(py, "return_schema"))? {
            Some(s) => CombinedSerializer::build(&s, config, definitions)?,
            None => AnySerializer::build(schema, config, definitions)?,
        };

        let name = format!("wrap_function[{function_name}, {}]", serializer.get_name());
        Ok(CombinedSerializer::FunctionWrap(Self {
            serializer,
            func: function.into(),
            function_name,
            name,
            return_serializer,
            when_used: WhenUsed::new(&ser_schema, WhenUsed::Always)?,
            is_field_serializer,
            info_arg,
        })
        .into())
    }
}

impl FunctionWrapSerializer {
    fn call<'py>(&self, value: &Bound<'py, PyAny>, state: &mut SerializationState<'py>) -> PyResult<(bool, Py<PyAny>)> {
        let py = value.py();
        if self.when_used.should_use(value, &state.extra) {
            let serialize = SerializationCallable::new(&self.serializer, state);
            let v = if self.is_field_serializer {
                if let Some(model) = state.model.as_ref() {
                    if self.info_arg {
                        let info = SerializationInfo::new(state, self.is_field_serializer)?;
                        self.func.call1(py, (model, value, serialize, info))?
                    } else {
                        self.func.call1(py, (model, value, serialize))?
                    }
                } else {
                    return Err(PyRuntimeError::new_err(
                        "Function wrap serializer expected to be run inside the context of a model field but no model was found",
                    ));
                }
            } else if self.info_arg {
                let info = SerializationInfo::new(state, self.is_field_serializer)?;
                self.func.call1(py, (value, serialize, info))?
            } else {
                self.func.call1(py, (value, serialize))?
            };
            Ok((true, v))
        } else {
            Ok((false, value.clone().unbind()))
        }
    }

    fn get_fallback_serializer(&self) -> &CombinedSerializer {
        self.serializer.as_ref()
    }

    fn retry_with_lax_check(&self) -> bool {
        self.serializer.retry_with_lax_check() || self.return_serializer.retry_with_lax_check()
    }
}

impl_py_gc_traverse!(FunctionWrapSerializer {
    serializer,
    func,
    return_serializer
});

function_type_serializer!(FunctionWrapSerializer);

#[pyclass(module = "pydantic_core._pydantic_core")]
pub(crate) struct SerializationCallable {
    serializer: Arc<CombinedSerializer>,
    extra_owned: ExtraOwned,
    filter: AnyFilter,
}

impl_py_gc_traverse!(SerializationCallable {
    serializer,
    extra_owned
});

impl SerializationCallable {
    pub fn new(serializer: &Arc<CombinedSerializer>, state: &SerializationState<'_>) -> Self {
        Self {
            serializer: serializer.clone(),
            extra_owned: ExtraOwned::new(state),
            filter: AnyFilter::new(),
        }
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        self.py_gc_traverse(&visit)
    }

    fn __clear__(&mut self) {
        self.extra_owned.model = None;
        self.extra_owned.fallback = None;
        self.extra_owned.context = None;
    }
}

#[pymethods]
impl SerializationCallable {
    #[pyo3(signature = (value, index_key=None))]
    fn __call__(
        &mut self,
        py: Python,
        value: &Bound<'_, PyAny>,
        index_key: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<Option<Py<PyAny>>> {
        // NB wrap serializers have strong coupling to their inner type,
        // so use to_python_no_infer so that type inference can't apply
        // at this layer

        let state = &mut self.extra_owned.to_state(py);

        if let Some(index_key) = index_key {
            let filter = if let Ok(index) = index_key.extract::<usize>() {
                self.filter.index_filter(index, state, None)?
            } else {
                self.filter.key_filter(index_key, state)?
            };
            if let Some(next_include_exclude) = filter {
                let state = &mut state.scoped_include_exclude(next_include_exclude);
                let v = self.serializer.to_python_no_infer(value, state)?;
                state.warnings.final_check(py)?;
                Ok(Some(v))
            } else {
                Err(PydanticOmit::new_err())
            }
        } else {
            let v = self.serializer.to_python_no_infer(value, state)?;
            state.warnings.final_check(py)?;
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

#[pyclass(module = "pydantic_core._pydantic_core")]
#[cfg_attr(debug_assertions, derive(Debug))]
struct SerializationInfo {
    #[pyo3(get)]
    include: Option<Py<PyAny>>,
    #[pyo3(get)]
    exclude: Option<Py<PyAny>>,
    #[pyo3(get)]
    context: Option<Py<PyAny>>,
    #[pyo3(get, name = "mode")]
    _mode: SerMode,
    #[pyo3(get)]
    by_alias: Option<bool>,
    #[pyo3(get)]
    exclude_unset: bool,
    #[pyo3(get)]
    exclude_defaults: bool,
    #[pyo3(get)]
    exclude_none: bool,
    #[pyo3(get)]
    exclude_computed_fields: bool,
    #[pyo3(get)]
    round_trip: bool,
    field_name: Option<String>,
    #[pyo3(get)]
    serialize_as_any: bool,
    #[pyo3(get)]
    polymorphic_serialization: Option<bool>,
}

impl_py_gc_traverse!(SerializationInfo {
    include,
    exclude,
    context
});

impl SerializationInfo {
    fn new(state: &SerializationState<'_>, is_field_serializer: bool) -> PyResult<Self> {
        let extra = &state.extra;
        if is_field_serializer {
            match state.field_name() {
                Some(field_name) => Ok(Self {
                    include: state.include().map(|i| i.clone().unbind()),
                    exclude: state.exclude().map(|e| e.clone().unbind()),
                    context: extra.context.clone().map(Bound::unbind),
                    _mode: extra.mode.clone(),
                    by_alias: extra.by_alias,
                    exclude_unset: extra.exclude_unset,
                    exclude_defaults: extra.exclude_defaults,
                    exclude_none: extra.exclude_none,
                    exclude_computed_fields: extra.exclude_none,
                    round_trip: extra.round_trip,
                    field_name: Some(field_name.to_string()),
                    serialize_as_any: extra.serialize_as_any,
                    polymorphic_serialization: extra.polymorphic_serialization,
                }),
                _ => Err(PyRuntimeError::new_err(
                    "Model field context expected for field serialization info but no model field was found",
                )),
            }
        } else {
            Ok(Self {
                include: state.include().map(|i| i.clone().unbind()),
                exclude: state.exclude().map(|e| e.clone().unbind()),
                context: extra.context.clone().map(Bound::unbind),
                _mode: extra.mode.clone(),
                by_alias: extra.by_alias,
                exclude_unset: extra.exclude_unset,
                exclude_defaults: extra.exclude_defaults,
                exclude_none: extra.exclude_none,
                exclude_computed_fields: extra.exclude_computed_fields,
                round_trip: extra.round_trip,
                field_name: None,
                serialize_as_any: extra.serialize_as_any,
                polymorphic_serialization: extra.polymorphic_serialization,
            })
        }
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        self.py_gc_traverse(&visit)
    }

    fn __clear__(&mut self) {
        self.include = None;
        self.exclude = None;
        self.context = None;
    }
}

#[pymethods]
impl SerializationInfo {
    fn mode_is_json(&self) -> bool {
        self._mode.is_json()
    }

    #[getter]
    fn __dict__<'py>(&'py self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let d = PyDict::new(py);
        if let Some(ref include) = self.include {
            d.set_item("include", include)?;
        }
        if let Some(ref exclude) = self.exclude {
            d.set_item("exclude", exclude)?;
        }
        if let Some(ref context) = self.context {
            d.set_item("context", context)?;
        }
        d.set_item("mode", &self._mode)?;
        d.set_item("by_alias", self.by_alias)?;
        d.set_item("exclude_unset", self.exclude_unset)?;
        d.set_item("exclude_defaults", self.exclude_defaults)?;
        d.set_item("exclude_none", self.exclude_none)?;
        d.set_item("exclude_computed_fields", self.exclude_computed_fields)?;
        d.set_item("round_trip", self.round_trip)?;
        d.set_item("serialize_as_any", self.serialize_as_any)?;
        Ok(d)
    }

    fn __repr__(&self, py: Python) -> PyResult<String> {
        Ok(format!(
            "SerializationInfo(include={}, exclude={}, context={}, mode='{}', by_alias={}, exclude_unset={}, exclude_defaults={}, exclude_none={}, exclude_computed_fields={}, round_trip={}, serialize_as_any={})",
            match self.include {
                Some(ref include) => include.bind(py).repr()?.to_str()?.to_owned(),
                None => "None".to_owned(),
            },
            match self.exclude {
                Some(ref exclude) => exclude.bind(py).repr()?.to_str()?.to_owned(),
                None => "None".to_owned(),
            },
            match self.context {
                Some(ref context) => context.bind(py).repr()?.to_str()?.to_owned(),
                None => "None".to_owned(),
            },
            self._mode,
            py_bool(self.by_alias.unwrap_or(false)),
            py_bool(self.exclude_unset),
            py_bool(self.exclude_defaults),
            py_bool(self.exclude_none),
            py_bool(self.exclude_computed_fields),
            py_bool(self.round_trip),
            py_bool(self.serialize_as_any),
        ))
    }

    fn __str__(&self, py: Python) -> PyResult<String> {
        self.__repr__(py)
    }
    #[getter]
    fn get_field_name<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyString>> {
        match self.field_name {
            Some(ref field_name) => Ok(PyString::new(py, field_name)),
            None => Err(PyAttributeError::new_err("No attribute named 'field_name'")),
        }
    }
}

fn py_bool(value: bool) -> &'static str {
    if value { "True" } else { "False" }
}
