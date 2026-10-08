use std::fmt::Debug;
use std::str::FromStr;
use std::sync::Arc;

use enum_dispatch::enum_dispatch;
use jiter::{PartialMode, StringCacheMode};

use pyo3::exceptions::{PyTypeError, PyValueError};
use pyo3::pybacked::PyBackedStr;
use pyo3::types::{PyAny, PyDict, PyString, PyTuple, PyType};
use pyo3::{IntoPyObjectExt, prelude::*};
use pyo3::{PyTraverseError, PyVisit, intern};

use crate::build_tools::{ExtraBehavior, py_schema_error_type};
use crate::definitions::{Definitions, DefinitionsBuilder};
use crate::errors::{LocItem, ValError, ValResult, ValidationError};
use crate::input::{Input, InputType, StringMapping};
use crate::py_gc::PyGcTraverse;
use crate::recursion_guard::RecursionState;
use crate::tools::SchemaDict;
pub(crate) use config::{TemporalUnitMode, ValBytesMode};

mod any;
mod arguments;
mod arguments_v3;
mod bool;
mod bytes;
mod call;
mod callable;
mod chain;
pub(crate) mod complex;
mod config;
mod counter;
mod custom_error;
mod dataclass;
mod date;
mod datetime;
pub(crate) mod decimal;
mod definitions;
mod deque;
mod dict;
mod ellipsis;
mod enum_;
mod float;
pub(crate) mod fraction;
mod frozendict;
mod frozenset;
mod function;
mod generator;
mod int;
mod is_instance;
mod is_subclass;
mod json;
mod json_or_python;
mod lax_or_strict;
mod list;
mod literal;
mod missing_sentinel;
mod model;
mod model_fields;
mod named_tuple;
mod none;
mod nullable;
mod ordered_dict;
mod prebuilt;
mod set;
mod shared;
mod string;
mod time;
mod timedelta;
mod tuple;
mod typed_dict;
mod union;
pub(crate) mod url;
mod uuid;
mod validation_state;
mod with_default;

pub use self::validation_state::{Exactness, ValidationState};
pub use with_default::DefaultType;

#[pyclass(module = "pydantic_core._pydantic_core", name = "Some")]
pub struct PySome {
    #[pyo3(get)]
    value: Py<PyAny>,
}

impl PySome {
    fn new(value: Py<PyAny>) -> Self {
        Self { value }
    }
}

#[pymethods]
impl PySome {
    pub fn __repr__(&self, py: Python) -> PyResult<String> {
        Ok(format!("Some({})", self.value.bind(py).repr()?))
    }

    #[new]
    pub fn py_new(value: Py<PyAny>) -> Self {
        Self { value }
    }

    #[classmethod]
    #[pyo3(signature = (_item, /))]
    pub fn __class_getitem__(cls: Py<PyType>, _item: &Bound<'_, PyAny>) -> Py<PyType> {
        cls
    }

    #[classattr]
    fn __match_args__(py: Python<'_>) -> PyResult<Bound<'_, PyTuple>> {
        (intern!(py, "value"),).into_pyobject(py)
    }
}

#[pyclass(module = "pydantic_core._pydantic_core", frozen)]
#[derive(Debug)]
pub struct SchemaValidator {
    validator: Arc<CombinedValidator>,
    definitions: Definitions<Arc<CombinedValidator>>,
    // References to the Python schema and config objects are saved to enable
    // reconstructing the object for cloudpickle support (see `__reduce__`).
    py_schema: Py<PyAny>,
    py_config: Option<Py<PyDict>>,
    #[pyo3(get)]
    title: Py<PyAny>,
    hide_input_in_errors: bool,
    validation_error_cause: bool,
    cache_str: StringCacheMode,
}

impl_py_gc_traverse!(SchemaValidator {
    validator,
    definitions,
    py_schema,
    py_config,
});

#[pymethods]
impl SchemaValidator {
    /// Whether `validate_json` can read this schema straight off the json cursor, rather than
    /// building a `JsonValue` tree first. Answers "is my model on the fast path", and lets a
    /// differential test tell "both paths agree" apart from "only one path ran".
    #[getter]
    fn _stream_plan_accepted(&self) -> bool {
        let root = model_fields::unwrap_prebuilt(&self.validator);
        stream_array_of_models(root).is_some() || model_fields::root_plan(root).is_some()
    }

    #[new]
    #[pyo3(signature = (schema, config=None, _use_prebuilt=true))]
    pub fn py_new(
        py: Python,
        schema: &Bound<'_, PyAny>,
        config: Option<&Bound<'_, PyDict>>,
        _use_prebuilt: bool,
    ) -> PyResult<Self> {
        // _use_prebuilt=true by default, but false during rebuilds to avoid stale references
        // to old validators (see pydantic-core issue #1894)
        let mut definitions_builder = DefinitionsBuilder::new(_use_prebuilt);

        let validator = build_validator(schema, config, &mut definitions_builder)?;
        let definitions = definitions_builder.finish()?;
        let py_schema = schema.clone().unbind();
        let py_config = match config {
            Some(c) if !c.is_empty() => Some(c.clone().into()),
            _ => None,
        };
        let config_title = match config {
            Some(c) => c.get_item("title")?,
            None => None,
        };
        let title = match config_title {
            Some(t) => t.unbind(),
            None => validator.get_name().into_py_any(py)?,
        };
        let hide_input_in_errors: bool = config.get_as(intern!(py, "hide_input_in_errors"))?.unwrap_or(false);
        let validation_error_cause: bool = config.get_as(intern!(py, "validation_error_cause"))?.unwrap_or(false);
        let cache_str: StringCacheMode = config
            .get_as(intern!(py, "cache_strings"))?
            .unwrap_or(StringCacheMode::All);
        Ok(Self {
            validator,
            definitions,
            py_schema,
            py_config,
            title,
            hide_input_in_errors,
            validation_error_cause,
            cache_str,
        })
    }

    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (input, *, strict=None, extra=None, from_attributes=None, context=None, self_instance=None, allow_partial=PartialMode::Off, by_alias=None, by_name=None))]
    pub fn validate_python(
        &self,
        py: Python,
        input: &Bound<'_, PyAny>,
        strict: Option<bool>,
        extra: Option<&Bound<'_, PyString>>,
        from_attributes: Option<bool>,
        context: Option<&Bound<'_, PyAny>>,
        self_instance: Option<&Bound<'_, PyAny>>,
        allow_partial: PartialMode,
        by_alias: Option<bool>,
        by_name: Option<bool>,
    ) -> PyResult<Py<PyAny>> {
        let extra_behavior = extra
            .map(|e| ExtraBehavior::from_str(e.to_str()?).map_err(|err| PyValueError::new_err(err.to_string())))
            .transpose()?;

        #[allow(clippy::used_underscore_items)]
        self._validate(
            py,
            input,
            InputType::Python,
            strict,
            extra_behavior,
            from_attributes,
            context,
            self_instance,
            allow_partial,
            by_alias,
            by_name,
        )
        .map_err(|e| self.prepare_validation_err(py, e, InputType::Python))
    }

    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (input, *, strict=None, extra=None, from_attributes=None, context=None, self_instance=None, by_alias=None, by_name=None))]
    pub fn isinstance_python(
        &self,
        py: Python,
        input: &Bound<'_, PyAny>,
        strict: Option<bool>,
        extra: Option<&Bound<'_, PyString>>,
        from_attributes: Option<bool>,
        context: Option<&Bound<'_, PyAny>>,
        self_instance: Option<&Bound<'_, PyAny>>,
        by_alias: Option<bool>,
        by_name: Option<bool>,
    ) -> PyResult<bool> {
        let extra_behavior = extra
            .map(|e| ExtraBehavior::from_str(e.to_str()?).map_err(|err| PyValueError::new_err(err.to_string())))
            .transpose()?;

        #[allow(clippy::used_underscore_items)]
        match self._validate(
            py,
            input,
            InputType::Python,
            strict,
            extra_behavior,
            from_attributes,
            context,
            self_instance,
            false.into(),
            by_alias,
            by_name,
        ) {
            Ok(_) => Ok(true),
            Err(ValError::InternalErr(err)) => Err(err),
            Err(ValError::Omit) => Err(ValidationError::omit_error()),
            Err(ValError::UseDefault) => Err(ValidationError::use_default_error()),
            Err(ValError::LineErrors(_)) => Ok(false),
        }
    }

    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (input, *, strict=None, extra=None, context=None, self_instance=None, allow_partial=PartialMode::Off, by_alias=None, by_name=None))]
    pub fn validate_json(
        &self,
        py: Python,
        input: &Bound<'_, PyAny>,
        strict: Option<bool>,
        extra: Option<&Bound<'_, PyString>>,
        context: Option<&Bound<'_, PyAny>>,
        self_instance: Option<&Bound<'_, PyAny>>,
        allow_partial: PartialMode,
        by_alias: Option<bool>,
        by_name: Option<bool>,
    ) -> PyResult<Py<PyAny>> {
        let extra_behavior = extra
            .map(|e| ExtraBehavior::from_str(e.to_str()?).map_err(|err| PyValueError::new_err(err.to_string())))
            .transpose()?;

        let r = match json::validate_json_bytes(input) {
            #[allow(clippy::used_underscore_items)]
            Ok(v_match) => self._validate_json(
                py,
                input,
                v_match.into_inner().as_slice(),
                strict,
                extra_behavior,
                context,
                self_instance,
                allow_partial,
                by_alias,
                by_name,
            ),
            Err(err) => Err(err),
        };
        r.map_err(|e| self.prepare_validation_err(py, e, InputType::Json))
    }

    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (input, *, strict=None, extra=None, context=None, allow_partial=PartialMode::Off, by_alias=None, by_name=None))]
    pub fn validate_strings(
        &self,
        py: Python,
        input: Bound<'_, PyAny>,
        strict: Option<bool>,
        extra: Option<&Bound<'_, PyString>>,
        context: Option<&Bound<'_, PyAny>>,
        allow_partial: PartialMode,
        by_alias: Option<bool>,
        by_name: Option<bool>,
    ) -> PyResult<Py<PyAny>> {
        let t = InputType::String;
        let string_mapping = StringMapping::new_value(input).map_err(|e| self.prepare_validation_err(py, e, t))?;
        let extra_behavior = extra
            .map(|e| ExtraBehavior::from_str(e.to_str()?).map_err(|err| PyValueError::new_err(err.to_string())))
            .transpose()?;

        #[allow(clippy::used_underscore_items)]
        match self._validate(
            py,
            &string_mapping,
            t,
            strict,
            extra_behavior,
            None,
            context,
            None,
            allow_partial,
            by_alias,
            by_name,
        ) {
            Ok(r) => Ok(r),
            Err(e) => Err(self.prepare_validation_err(py, e, t)),
        }
    }

    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (obj, field_name, field_value, *, strict=None, extra=None,from_attributes=None, context=None, by_alias=None, by_name=None))]
    pub fn validate_assignment(
        &self,
        py: Python,
        obj: Bound<'_, PyAny>,
        field_name: PyBackedStr,
        field_value: Bound<'_, PyAny>,
        strict: Option<bool>,
        extra: Option<&Bound<'_, PyString>>,
        from_attributes: Option<bool>,
        context: Option<&Bound<'_, PyAny>>,
        by_alias: Option<bool>,
        by_name: Option<bool>,
    ) -> PyResult<Py<PyAny>> {
        let extra_behavior = extra
            .map(|e| ExtraBehavior::from_str(e.to_str()?).map_err(|err| PyValueError::new_err(err.to_string())))
            .transpose()?;

        let extra = Extra {
            input_type: InputType::Python,
            strict,
            extra_behavior,
            from_attributes,
            context,
            cache_str: self.cache_str,
            by_alias,
            by_name,
        };

        let guard = &mut RecursionState::default();
        let mut state = ValidationState::new(
            extra,
            guard,
            false.into(),
            Some(field_name.as_py_str().bind(py).clone()),
            None,
        );
        self.validator
            .validate_assignment(py, &obj, &field_name, &field_value, &mut state)
            .map_err(|e| self.prepare_validation_err(py, e, InputType::Python))
    }

    #[pyo3(signature = (*, strict=None, context=None))]
    pub fn get_default_value(
        &self,
        py: Python,
        strict: Option<bool>,
        context: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<Py<PyAny>> {
        let extra = Extra {
            input_type: InputType::Python,
            strict,
            extra_behavior: None,
            from_attributes: None,
            context,
            cache_str: self.cache_str,
            by_alias: None,
            by_name: None,
        };
        let recursion_guard = &mut RecursionState::default();
        let mut state = ValidationState::new(extra, recursion_guard, false.into(), None, None);
        let r = self.validator.default_value(py, None::<i64>, &mut state);
        match r {
            Ok(maybe_default) => match maybe_default {
                Some(v) => PySome::new(v).into_py_any(py),
                None => Ok(py.None()),
            },
            Err(e) => Err(self.prepare_validation_err(py, e, InputType::Python)),
        }
    }

    pub fn __reduce__<'py>(slf: &Bound<'py, Self>) -> PyResult<(Bound<'py, PyType>, Bound<'py, PyTuple>)> {
        // Passing _use_prebuilt=false avoids reusing prebuilt serializers when unpickling
        let init_args = (&slf.get().py_schema, &slf.get().py_config, false).into_pyobject(slf.py())?;
        Ok((slf.get_type(), init_args))
    }

    pub fn __repr__(&self, py: Python) -> String {
        format!(
            "SchemaValidator(title={:?}, validator={:#?}, definitions={:#?}, cache_strings={})",
            self.title.extract::<&str>(py).unwrap(),
            self.validator,
            self.definitions,
            match self.cache_str {
                StringCacheMode::All => "True",
                StringCacheMode::Keys => "'keys'",
                StringCacheMode::None => "False",
            }
        )
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        self.py_gc_traverse(&visit)
    }
}

impl SchemaValidator {
    #[allow(clippy::too_many_arguments)]
    fn _validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        input_type: InputType,
        strict: Option<bool>,
        extra_behavior: Option<ExtraBehavior>,
        from_attributes: Option<bool>,
        context: Option<&Bound<'py, PyAny>>,
        self_instance: Option<&Bound<'py, PyAny>>,
        allow_partial: PartialMode,
        by_alias: Option<bool>,
        by_name: Option<bool>,
    ) -> ValResult<Py<PyAny>> {
        let mut recursion_guard = RecursionState::default();
        let mut state = ValidationState::new(
            Extra::new(
                strict,
                extra_behavior,
                from_attributes,
                context,
                input_type,
                self.cache_str,
                by_alias,
                by_name,
            ),
            &mut recursion_guard,
            allow_partial,
            None,
            self_instance,
        );
        self.validator.validate(py, input, &mut state)
    }

    #[allow(clippy::too_many_arguments)]
    fn _validate_json(
        &self,
        py: Python,
        input: &Bound<'_, PyAny>,
        json_data: &[u8],
        strict: Option<bool>,
        extra_behavior: Option<ExtraBehavior>,
        context: Option<&Bound<'_, PyAny>>,
        self_instance: Option<&Bound<'_, PyAny>>,
        allow_partial: PartialMode,
        by_alias: Option<bool>,
        by_name: Option<bool>,
    ) -> ValResult<Py<PyAny>> {
        // On unless switched off. Every schema or document the fast path cannot finish falls
        // back to the tree path, so the switch is an escape hatch rather than a feature flag:
        static DISABLED: std::sync::OnceLock<bool> = std::sync::OnceLock::new();
        #[allow(clippy::used_underscore_items)]
        if !*DISABLED.get_or_init(|| std::env::var_os("PYDANTIC_DISABLE_JSON_STREAMING").is_some())
            && let Some(result) = self._validate_json_streaming(
                py,
                json_data,
                strict,
                extra_behavior,
                context,
                self_instance,
                allow_partial,
                by_alias,
                by_name,
            )
        {
            // Under `stream-verify` the same document is validated the ordinary way too and the
            // results compared, so a divergence fails loudly instead of being returned. Only a
            // streamed success is checked, which is the whole risk surface: the fast path has no
            // error-construction code, so it can only produce a value or decline.
            #[cfg(feature = "stream-verify")]
            if let Ok(streamed) = &result {
                let tree = jiter::JsonValue::parse_with_config(json_data, true, allow_partial)
                    .map_err(|e| json::map_json_err(input, e, json_data))
                    .and_then(|json_value| {
                        #[allow(clippy::used_underscore_items)]
                        self._validate(
                            py,
                            &json_value,
                            InputType::Json,
                            strict,
                            extra_behavior,
                            None,
                            context,
                            self_instance,
                            allow_partial,
                            by_alias,
                            by_name,
                        )
                    });
                crate::stream_verify::compare(py, streamed, tree)?;
            }
            return result;
        }
        let json_value = jiter::JsonValue::parse_with_config(json_data, true, allow_partial)
            .map_err(|e| json::map_json_err(input, e, json_data))?;
        #[allow(clippy::used_underscore_items)]
        self._validate(
            py,
            &json_value,
            InputType::Json,
            strict,
            extra_behavior,
            None,
            context,
            self_instance,
            allow_partial,
            by_alias,
            by_name,
        )
    }

    /// Validate models straight off a json cursor, so the document's objects are never built
    /// into a `JsonValue` tree. `None` means the schema or the document is not one this handles
    /// and the caller should take the tree path.
    ///
    /// Handles a model at the top level and an array of them. Any element the fast path cannot
    /// finish is re-read from its own bytes and validated the ordinary way, so errors and their
    /// locations come out exactly as they always did.
    #[allow(clippy::too_many_arguments)]
    fn _validate_json_streaming(
        &self,
        py: Python<'_>,
        json_data: &[u8],
        strict: Option<bool>,
        extra_behavior: Option<ExtraBehavior>,
        context: Option<&Bound<'_, PyAny>>,
        self_instance: Option<&Bound<'_, PyAny>>,
        allow_partial: PartialMode,
        by_alias: Option<bool>,
        by_name: Option<bool>,
    ) -> Option<ValResult<Py<PyAny>>> {
        if by_alias.is_some()
            || by_name.is_some()
            || allow_partial.is_active()
            || extra_behavior.is_some()
            || self_instance.is_some()
        {
            return None;
        }

        let root = model_fields::unwrap_prebuilt(&self.validator);

        let models = stream_array_of_models(root);

        // anything else the plan understands, taken as a single value
        let value_plan = match models {
            Some(_) => None,
            None => Some(model_fields::root_plan(root)?),
        };

        let mut recursion_guard = RecursionState::default();
        let mut state = ValidationState::new(
            Extra::new(
                strict,
                extra_behavior,
                None,
                context,
                InputType::Json,
                self.cache_str,
                by_alias,
                by_name,
            ),
            &mut recursion_guard,
            allow_partial,
            None,
            self_instance,
        );
        if let Some((class, item, mf, plan)) = models {
            return Streamer {
                py,
                json_data,
                class: class.bind(py),
                item,
                mf,
                plan: &plan,
            }
            .array(&mut state);
        }

        let plan = value_plan?;
        let mut jiter = jiter::Jiter::new(json_data);
        match model_fields::take_root(py, &mut jiter, &plan, &mut state) {
            // trailing content is an error the ordinary path reports
            Ok(Some(value)) if jiter.finish().is_ok() => Some(Ok(value.unbind())),
            Err(model_fields::StreamStop::Py(err)) => Some(Err(err.into())),
            _ => None,
        }
    }

    fn prepare_validation_err(&self, py: Python, error: ValError, input_type: InputType) -> PyErr {
        ValidationError::from_val_error(
            py,
            self.title.clone_ref(py),
            input_type,
            error,
            None,
            self.hide_input_in_errors,
            self.validation_error_cause,
        )
    }
}

/// An array of models, the one shape that replays a failed element on its own rather than
/// replaying the whole document. Every other shape, a single model included, goes through the
/// plan like any other value.
type StreamArrayOfModels<'a> = (
    &'a Py<PyType>,
    &'a CombinedValidator,
    &'a model_fields::ModelFieldsValidator,
    model_fields::ModelPlan<'a>,
);

fn stream_array_of_models(root: &CombinedValidator) -> Option<StreamArrayOfModels<'_>> {
    let CombinedValidator::List(list) = root else {
        return None;
    };
    let list = list.stream_list()?;
    // this path builds the list itself, so it cannot honour a bound or `fail_fast`; such a list
    // is left to the ordinary plan, whose reader does check the length
    if list.min_length.is_some() || list.max_length.is_some() || list.fail_fast {
        return None;
    }
    let item = model_fields::unwrap_prebuilt(list.items);
    let CombinedValidator::Model(model_v) = item else {
        return None;
    };
    let (class, inner) = model_v.stream_parts()?;
    let CombinedValidator::ModelFields(mf) = &**inner else {
        return None;
    };
    Some((class, item, mf, mf.stream_plan()?))
}

pub trait BuildValidator: Sized {
    const EXPECTED_TYPE: &'static str;

    /// Build a new validator from the schema, the return type is a trait to provide a way for validators
    /// to return other validators, see `string.rs`, `int.rs`, `float.rs` and `function.rs` for examples
    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedValidator>>,
    ) -> PyResult<Arc<CombinedValidator>>;
}

pub fn build_validator(
    schema: &Bound<'_, PyAny>,
    config: Option<&Bound<'_, PyDict>>,
    definitions: &mut DefinitionsBuilder<Arc<CombinedValidator>>,
) -> PyResult<Arc<CombinedValidator>> {
    // Read use_prebuilt from the definitions builder - this ensures all nested
    // validators respect the same setting as the top-level build
    let use_prebuilt = definitions.use_prebuilt();
    build_validator_inner(schema, config, definitions, use_prebuilt)
}

fn build_validator_inner(
    schema: &Bound<'_, PyAny>,
    config: Option<&Bound<'_, PyDict>>,
    definitions: &mut DefinitionsBuilder<Arc<CombinedValidator>>,
    use_prebuilt: bool,
) -> PyResult<Arc<CombinedValidator>> {
    let dict = schema.cast::<PyDict>()?;
    let py = schema.py();
    let type_: Bound<'_, PyString> = dict.get_as_req(intern!(py, "type"))?;
    let type_ = type_.to_str()?;

    // if we have a SchemaValidator on the type already, use it
    if use_prebuilt && let Ok(Some(prebuilt_validator)) = prebuilt::PrebuiltValidator::try_get_from_schema(type_, dict)
    {
        return Ok(Arc::new(prebuilt_validator));
    }

    // macro to build the match statement for validator selection
    macro_rules! validator_match {
        ($type:ident, $dict:ident, $config:ident, $definitions:ident, $($validator:path,)+) => {
            match $type {
                $(
                    <$validator>::EXPECTED_TYPE => <$validator>::build($dict, $config, $definitions),
                )+
                "invalid" => return Err(invalid_schema_type()),
                _ => return Err(unknown_schema_type($type)),
            }
        };
    }

    let result = validator_match!(
        type_,
        dict,
        config,
        definitions,
        // typed dict e.g. heterogeneous dicts or simply a model
        typed_dict::TypedDictValidator,
        // unions
        union::UnionValidator,
        union::TaggedUnionValidator,
        // nullables
        nullable::NullableValidator,
        // model classes
        model::ModelValidator,
        model_fields::ModelFieldsValidator,
        // dataclasses
        dataclass::DataclassArgsValidator,
        dataclass::DataclassValidator,
        // named tuples
        named_tuple::NamedTupleValidator,
        // strings
        string::StrValidator,
        // integers
        int::IntValidator,
        // boolean
        bool::BoolValidator,
        // floats
        float::FloatBuilder,
        // decimals
        decimal::DecimalValidator,
        // fractions
        fraction::FractionValidator,
        // tuples
        tuple::TupleValidator,
        // list/arrays
        list::ListValidator,
        // deques
        deque::DequeValidator,
        // sets - unique lists
        set::SetValidator,
        // dicts/objects (recursive)
        dict::DictValidator,
        // frozendicts
        frozendict::FrozenDictValidator,
        // ordered dicts
        ordered_dict::OrderedDictValidator,
        // counters
        counter::CounterValidator,
        // None/null
        none::NoneValidator,
        // functions - before, after, plain & wrap
        function::FunctionAfterValidator,
        function::FunctionBeforeValidator,
        function::FunctionPlainValidator,
        function::FunctionWrapValidator,
        // function call - validation around a function call
        call::CallValidator,
        // literals
        literal::LiteralValidator,
        // missing sentinel
        missing_sentinel::MissingSentinelValidator,
        // ellipsis
        ellipsis::EllipsisValidator,
        // enums
        enum_::BuildEnumValidator,
        // any
        any::AnyValidator,
        // bytes
        bytes::BytesValidator,
        // dates
        date::DateValidator,
        // times
        time::TimeValidator,
        // datetimes
        datetime::DateTimeValidator,
        // frozensets
        frozenset::FrozenSetValidator,
        // timedelta
        timedelta::TimeDeltaValidator,
        // introspection types
        is_instance::IsInstanceValidator,
        is_subclass::IsSubclassValidator,
        callable::CallableValidator,
        // arguments
        arguments::ArgumentsValidator,
        arguments_v3::ArgumentsV3Validator,
        // default value
        with_default::WithDefaultValidator,
        // chain validators
        chain::ChainValidator,
        // lax or strict
        lax_or_strict::LaxOrStrictValidator,
        // json or python
        json_or_python::JsonOrPython,
        // generator validators
        generator::GeneratorValidator,
        // custom error
        custom_error::CustomErrorValidator,
        // json data
        json::JsonValidator,
        // url types
        url::UrlValidator,
        url::MultiHostUrlValidator,
        // uuid types
        uuid::UuidValidator,
        // recursive (self-referencing) models
        definitions::DefinitionRefValidator,
        definitions::DefinitionsValidatorBuilder,
        complex::ComplexValidator,
    );

    result.map_err(|e| failed_to_build_validator(type_, e))
}

#[cold]
fn failed_to_build_validator(val_type: &str, err: PyErr) -> PyErr {
    py_schema_error_type!("Error building \"{val_type}\" validator:\n  {err}")
}

#[cold]
fn invalid_schema_type() -> PyErr {
    py_schema_error_type!("Cannot construct schema with `InvalidSchema` member.")
}

#[cold]
fn unknown_schema_type(val_type: &str) -> PyErr {
    py_schema_error_type!("Unknown schema type: \"{val_type}\"")
}

/// Constants for a validation process
#[derive(Debug, Clone)]
pub struct Extra<'a, 'py> {
    /// Validation mode
    pub input_type: InputType,
    /// whether we're in strict or lax mode
    pub strict: Option<bool>,
    /// Whether to ignore, allow, or forbid extra data during model validation
    #[allow(clippy::struct_field_names)]
    pub extra_behavior: Option<ExtraBehavior>,
    /// Validation time setting of `from_attributes`
    pub from_attributes: Option<bool>,
    /// context used in validator functions
    pub context: Option<&'a Bound<'py, PyAny>>,
    /// Whether to use a cache of short strings to accelerate python string construction
    cache_str: StringCacheMode,
    /// Whether to use the field's alias to match the input data to an attribute.
    by_alias: Option<bool>,
    /// Whether to use the field's name to match the input data to an attribute.
    by_name: Option<bool>,
}

impl<'a, 'py> Extra<'a, 'py> {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        strict: Option<bool>,
        extra_behavior: Option<ExtraBehavior>,
        from_attributes: Option<bool>,
        context: Option<&'a Bound<'py, PyAny>>,
        input_type: InputType,
        cache_str: StringCacheMode,
        by_alias: Option<bool>,
        by_name: Option<bool>,
    ) -> Self {
        Extra {
            input_type,
            strict,
            extra_behavior,
            from_attributes,
            context,
            cache_str,
            by_alias,
            by_name,
        }
    }
}

#[derive(Debug)]
#[enum_dispatch(PyGcTraverse)]
pub enum CombinedValidator {
    // typed dict e.g. heterogeneous dicts or simply a model
    TypedDict(typed_dict::TypedDictValidator),
    // unions
    Union(union::UnionValidator),
    TaggedUnion(Box<union::TaggedUnionValidator>),
    // nullables
    Nullable(nullable::NullableValidator),
    // create new model classes
    Model(model::ModelValidator),
    ModelFields(model_fields::ModelFieldsValidator),
    // dataclasses
    DataclassArgs(dataclass::DataclassArgsValidator),
    Dataclass(dataclass::DataclassValidator),
    // named tuples
    NamedTuple(named_tuple::NamedTupleValidator),
    // strings
    Str(string::StrValidator),
    StrConstrained(string::StrConstrainedValidator),
    // integers
    Int(int::IntValidator),
    ConstrainedInt(Box<int::ConstrainedIntValidator>),
    // booleans
    Bool(bool::BoolValidator),
    // floats
    Float(float::FloatValidator),
    ConstrainedFloat(float::ConstrainedFloatValidator),
    // decimals
    Decimal(decimal::DecimalValidator),
    // fractions
    Fraction(fraction::FractionValidator),
    // lists
    List(list::ListValidator),
    // deques
    Deque(deque::DequeValidator),
    // sets - unique lists
    Set(set::SetValidator),
    // tuples
    Tuple(tuple::TupleValidator),
    // dicts/objects (recursive)
    Dict(dict::DictValidator),
    // frozendicts
    FrozenDict(frozendict::FrozenDictValidator),
    // ordered dicts
    OrderedDict(ordered_dict::OrderedDictValidator),
    // counters
    Counter(counter::CounterValidator),
    // None/null
    None(none::NoneValidator),
    // functions
    FunctionBefore(function::FunctionBeforeValidator),
    FunctionAfter(function::FunctionAfterValidator),
    FunctionPlain(function::FunctionPlainValidator),
    FunctionWrap(function::FunctionWrapValidator),
    // function call - validation around a function call
    FunctionCall(call::CallValidator),
    // literals
    Literal(literal::LiteralValidator),
    // Missing sentinel
    MissingSentinel(missing_sentinel::MissingSentinelValidator),
    // Ellipsis
    Ellipsis(ellipsis::EllipsisValidator),
    // enums
    IntEnum(enum_::EnumValidator<enum_::IntEnumValidator>),
    StrEnum(enum_::EnumValidator<enum_::StrEnumValidator>),
    FloatEnum(enum_::EnumValidator<enum_::FloatEnumValidator>),
    PlainEnum(enum_::EnumValidator<enum_::PlainEnumValidator>),
    // any
    Any(any::AnyValidator),
    // bytes
    Bytes(bytes::BytesValidator),
    ConstrainedBytes(bytes::BytesConstrainedValidator),
    // dates
    Date(date::DateValidator),
    // times
    Time(time::TimeValidator),
    // datetimes
    Datetime(datetime::DateTimeValidator),
    // frozensets
    FrozenSet(frozenset::FrozenSetValidator),
    // timedelta
    Timedelta(timedelta::TimeDeltaValidator),
    // introspection types
    IsInstance(is_instance::IsInstanceValidator),
    IsSubclass(is_subclass::IsSubclassValidator),
    Callable(callable::CallableValidator),
    // arguments
    Arguments(arguments::ArgumentsValidator),
    ArgumentsV3(arguments_v3::ArgumentsV3Validator),
    // default value
    WithDefault(with_default::WithDefaultValidator),
    // chain validators
    Chain(chain::ChainValidator),
    // lax or strict
    LaxOrStrict(lax_or_strict::LaxOrStrictValidator),
    // generator validators
    Generator(generator::GeneratorValidator),
    // custom error
    CustomError(custom_error::CustomErrorValidator),
    // json data
    Json(json::JsonValidator),
    // url types
    Url(Box<url::UrlValidator>),
    MultiHostUrl(Box<url::MultiHostUrlValidator>),
    // uuid types
    Uuid(uuid::UuidValidator),
    // reference to definition, useful for recursive (self-referencing) models
    DefinitionRef(definitions::DefinitionRefValidator),
    // input dependent
    JsonOrPython(json_or_python::JsonOrPython),
    Complex(complex::ComplexValidator),
    // uses a reference to an existing SchemaValidator to reduce memory usage
    Prebuilt(prebuilt::PrebuiltValidator),
}

/// This trait must be implemented by all validators, it allows various validators to be accessed consistently,
/// validators defined in `build_validator` also need `EXPECTED_TYPE` as a const, but that can't be part of the trait
#[enum_dispatch(CombinedValidator)]
pub trait Validator: Send + Sync + Debug {
    /// Do the actual validation for this schema/type
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Py<PyAny>>;

    /// Get a default value, currently only used by `WithDefaultValidator`
    fn default_value<'py>(
        &self,
        _py: Python<'py>,
        _outer_loc: Option<impl Into<LocItem>>,
        _state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Option<Py<PyAny>>> {
        Ok(None)
    }

    /// Validate assignment to a field of a model
    #[allow(clippy::too_many_arguments)]
    fn validate_assignment<'py>(
        &self,
        _py: Python<'py>,
        _obj: &Bound<'py, PyAny>,
        _field_name: &PyBackedStr,
        _field_value: &Bound<'py, PyAny>,
        _state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Py<PyAny>> {
        let py_err = PyTypeError::new_err(format!("validate_assignment is not supported for {}", self.get_name()));
        Err(py_err.into())
    }

    /// `get_name` generally returns `Self::EXPECTED_TYPE` or some other clear identifier of the validator
    /// this is used in the error location in unions, and in the top level message in `ValidationError`
    fn get_name(&self) -> &str;
}

/// Rarely-used validators which are much larger than the rest are stored boxed in `CombinedValidator`,
/// so that they don't inflate the size of *every* validator node. Delegate straight through to the inner
/// validator so that `enum_dispatch` can treat `Box<V>` as a variant type.
impl<T: Validator> Validator for Box<T> {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Py<PyAny>> {
        (**self).validate(py, input, state)
    }

    fn default_value<'py>(
        &self,
        py: Python<'py>,
        outer_loc: Option<impl Into<LocItem>>,
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Option<Py<PyAny>>> {
        (**self).default_value(py, outer_loc, state)
    }

    fn validate_assignment<'py>(
        &self,
        py: Python<'py>,
        obj: &Bound<'py, PyAny>,
        field_name: &PyBackedStr,
        field_value: &Bound<'py, PyAny>,
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Py<PyAny>> {
        (**self).validate_assignment(py, obj, field_name, field_value, state)
    }

    fn get_name(&self) -> &str {
        (**self).get_name()
    }
}

/// The pieces the streaming path above needs to read one document.
struct Streamer<'a, 'py> {
    py: Python<'py>,
    json_data: &'a [u8],
    class: &'a Bound<'py, PyType>,
    item: &'a CombinedValidator,
    mf: &'a model_fields::ModelFieldsValidator,
    plan: &'a model_fields::ModelPlan<'a>,
}

impl<'py> Streamer<'_, 'py> {
    /// One object from the cursor as a finished model instance, or `None` if the fast path could
    /// not finish it. Either way the object has been consumed.
    fn object(
        &self,
        jiter: &mut jiter::Jiter<'_>,
        state: &mut ValidationState<'_, 'py>,
    ) -> Option<ValResult<Bound<'py, PyAny>>> {
        let fields = match self.mf.validate_json_streaming(self.py, jiter, self.plan, state) {
            Ok(Some(fields)) => fields,
            // the object could not be finished, or the cursor hit something it will not read:
            // either way the caller takes the ordinary path
            Ok(None) | Err(model_fields::StreamStop::Cursor) => return None,
            Err(model_fields::StreamStop::Py(err)) => return Some(Err(err.into())),
        };
        let (model_dict, _extra, fields_set) = fields;
        let none = self.py.None();
        let built = model::create_class(self.class).and_then(|instance| {
            model::set_model_attrs(&instance, &model_dict, none.bind(self.py), &fields_set).map(|()| instance)
        });
        Some(built.map_err(Into::into))
    }

    /// The same object again, validated the ordinary way from its own bytes, so that errors and
    /// their locations are whatever the tree path would have produced.
    fn replay(&self, span: &[u8], state: &mut ValidationState<'_, 'py>) -> Option<ValResult<Py<PyAny>>> {
        let value = jiter::JsonValue::parse(span, true).ok()?;
        Some(self.item.validate(self.py, &value, state))
    }

    fn array(&self, state: &mut ValidationState<'_, 'py>) -> Option<ValResult<Py<PyAny>>> {
        let mut jiter = jiter::Jiter::new(self.json_data);
        if !matches!(jiter.peek().ok()?, jiter::Peek::Array) {
            return None;
        }
        let list = pyo3::types::PyList::empty(self.py);
        let mut errors: Vec<crate::errors::ValLineError> = Vec::new();
        let mut index = 0usize;

        let mut peek = jiter.known_array().ok()?;
        while let Some(p) = peek {
            let start = jiter.current_index();
            let built = if matches!(p, jiter::Peek::Object) {
                self.object(&mut jiter, state)
            } else {
                jiter.known_skip(p).ok()?;
                None
            };
            match built {
                Some(Ok(instance)) => list.append(instance).ok()?,
                Some(Err(err)) => return Some(Err(err)),
                None => match self.replay(&self.json_data[start..jiter.current_index()], state)? {
                    Ok(validated) => list.append(validated).ok()?,
                    Err(ValError::LineErrors(line_errors)) => {
                        errors.extend(line_errors.into_iter().map(|err| err.with_outer_location(index)));
                    }
                    Err(err) => return Some(Err(err)),
                },
            }
            index += 1;
            peek = jiter.array_step().ok()?;
        }
        if jiter.finish().is_err() {
            return None;
        }
        if !errors.is_empty() {
            return Some(Err(ValError::LineErrors(errors)));
        }
        Some(Ok(list.into_any().unbind()))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// `CombinedValidator` is instantiated once per node of every schema, so its size is multiplied
    /// across every model in an application. Rarely-used variants which are much larger than the rest
    /// are boxed to keep this down — if this assertion fails, box the offending variant rather than
    /// raising the limit.
    #[test]
    fn combined_validator_size() {
        assert!(
            std::mem::size_of::<CombinedValidator>() <= 144,
            "CombinedValidator grew to {} bytes",
            std::mem::size_of::<CombinedValidator>()
        );
    }
}
