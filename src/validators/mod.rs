use std::fmt::Debug;

use enum_dispatch::enum_dispatch;
use jiter::{PartialMode, StringCacheMode};

use pyo3::exceptions::PyTypeError;
use pyo3::types::{PyAny, PyDict, PyString, PyTuple, PyType};
use pyo3::{intern, PyTraverseError, PyVisit};
use pyo3::{prelude::*, IntoPyObjectExt};

use crate::build_tools::{py_schema_err, py_schema_error_type};
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
mod custom_error;
mod dataclass;
mod date;
mod datetime;
pub(crate) mod decimal;
mod definitions;
mod dict;
mod enum_;
mod float;
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
mod none;
mod nullable;
mod prebuilt;
mod set;
mod string;
mod time;
mod timedelta;
mod tuple;
mod typed_dict;
mod union;
mod url;
mod uuid;
mod validation_state;
mod with_default;

pub use self::validation_state::{Exactness, ValidationState};
pub use with_default::DefaultType;

#[pyclass(module = "pydantic_core._pydantic_core", name = "Some")]
pub struct PySome {
    #[pyo3(get)]
    value: PyObject,
}

impl PySome {
    fn new(value: PyObject) -> Self {
        Self { value }
    }
}

#[pymethods]
impl PySome {
    pub fn __repr__(&self, py: Python) -> PyResult<String> {
        Ok(format!("Some({})", self.value.bind(py).repr()?,))
    }

    #[new]
    pub fn py_new(value: PyObject) -> Self {
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
    validator: CombinedValidator,
    definitions: Definitions<CombinedValidator>,
    // References to the Python schema and config objects are saved to enable
    // reconstructing the object for cloudpickle support (see `__reduce__`).
    py_schema: Py<PyAny>,
    py_config: Option<Py<PyDict>>,
    #[pyo3(get)]
    title: PyObject,
    hide_input_in_errors: bool,
    validation_error_cause: bool,
    cache_str: StringCacheMode,
}

#[pymethods]
impl SchemaValidator {
    #[new]
    #[pyo3(signature = (schema, config=None))]
    pub fn py_new(py: Python, schema: &Bound<'_, PyAny>, config: Option<&Bound<'_, PyDict>>) -> PyResult<Self> {
        let mut definitions_builder = DefinitionsBuilder::new();

        let validator = build_validator_base(schema, config, &mut definitions_builder)?;
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
    #[pyo3(signature = (input, *, strict=None, from_attributes=None, context=None, self_instance=None, allow_partial=PartialMode::Off, by_alias=None, by_name=None))]
    pub fn validate_python(
        &self,
        py: Python,
        input: &Bound<'_, PyAny>,
        strict: Option<bool>,
        from_attributes: Option<bool>,
        context: Option<&Bound<'_, PyAny>>,
        self_instance: Option<&Bound<'_, PyAny>>,
        allow_partial: PartialMode,
        by_alias: Option<bool>,
        by_name: Option<bool>,
    ) -> PyResult<PyObject> {
        #[allow(clippy::used_underscore_items)]
        self._validate(
            py,
            input,
            InputType::Python,
            strict,
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
    #[pyo3(signature = (input, *, strict=None, from_attributes=None, context=None, self_instance=None, by_alias=None, by_name=None))]
    pub fn isinstance_python(
        &self,
        py: Python,
        input: &Bound<'_, PyAny>,
        strict: Option<bool>,
        from_attributes: Option<bool>,
        context: Option<&Bound<'_, PyAny>>,
        self_instance: Option<&Bound<'_, PyAny>>,
        by_alias: Option<bool>,
        by_name: Option<bool>,
    ) -> PyResult<bool> {
        #[allow(clippy::used_underscore_items)]
        match self._validate(
            py,
            input,
            InputType::Python,
            strict,
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
    #[pyo3(signature = (input, *, strict=None, context=None, self_instance=None, allow_partial=PartialMode::Off, by_alias=None, by_name=None))]
    pub fn validate_json(
        &self,
        py: Python,
        input: &Bound<'_, PyAny>,
        strict: Option<bool>,
        context: Option<&Bound<'_, PyAny>>,
        self_instance: Option<&Bound<'_, PyAny>>,
        allow_partial: PartialMode,
        by_alias: Option<bool>,
        by_name: Option<bool>,
    ) -> PyResult<PyObject> {
        let r = match json::validate_json_bytes(input) {
            #[allow(clippy::used_underscore_items)]
            Ok(v_match) => self._validate_json(
                py,
                input,
                v_match.into_inner().as_slice(),
                strict,
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
    #[pyo3(signature = (input, *, strict=None, context=None, allow_partial=PartialMode::Off, by_alias=None, by_name=None))]
    pub fn validate_strings(
        &self,
        py: Python,
        input: Bound<'_, PyAny>,
        strict: Option<bool>,
        context: Option<&Bound<'_, PyAny>>,
        allow_partial: PartialMode,
        by_alias: Option<bool>,
        by_name: Option<bool>,
    ) -> PyResult<PyObject> {
        let t = InputType::String;
        let string_mapping = StringMapping::new_value(input).map_err(|e| self.prepare_validation_err(py, e, t))?;

        #[allow(clippy::used_underscore_items)]
        match self._validate(
            py,
            &string_mapping,
            t,
            strict,
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
    #[pyo3(signature = (obj, field_name, field_value, *, strict=None, from_attributes=None, context=None, by_alias=None, by_name=None))]
    pub fn validate_assignment(
        &self,
        py: Python,
        obj: Bound<'_, PyAny>,
        field_name: &str,
        field_value: Bound<'_, PyAny>,
        strict: Option<bool>,
        from_attributes: Option<bool>,
        context: Option<&Bound<'_, PyAny>>,
        by_alias: Option<bool>,
        by_name: Option<bool>,
    ) -> PyResult<PyObject> {
        let extra = Extra {
            input_type: InputType::Python,
            data: None,
            strict,
            from_attributes,
            field_name: Some(PyString::new(py, field_name)),
            context,
            self_instance: None,
            cache_str: self.cache_str,
            by_alias,
            by_name,
        };

        let guard = &mut RecursionState::default();
        let mut state = ValidationState::new(extra, guard, false.into());
        self.validator
            .validate_assignment(py, &obj, field_name, &field_value, &mut state)
            .map_err(|e| self.prepare_validation_err(py, e, InputType::Python))
    }

    #[pyo3(signature = (*, strict=None, context=None))]
    pub fn get_default_value(
        &self,
        py: Python,
        strict: Option<bool>,
        context: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<PyObject> {
        let extra = Extra {
            input_type: InputType::Python,
            data: None,
            strict,
            from_attributes: None,
            field_name: None,
            context,
            self_instance: None,
            cache_str: self.cache_str,
            by_alias: None,
            by_name: None,
        };
        let recursion_guard = &mut RecursionState::default();
        let mut state = ValidationState::new(extra, recursion_guard, false.into());
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
        let init_args = (&slf.get().py_schema, &slf.get().py_config).into_pyobject(slf.py())?;
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
        self.validator.py_gc_traverse(&visit)?;
        visit.call(&self.py_schema)?;
        if let Some(ref py_config) = self.py_config {
            visit.call(py_config)?;
        }
        Ok(())
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
        from_attributes: Option<bool>,
        context: Option<&Bound<'py, PyAny>>,
        self_instance: Option<&Bound<'py, PyAny>>,
        allow_partial: PartialMode,
        by_alias: Option<bool>,
        by_name: Option<bool>,
    ) -> ValResult<PyObject> {
        let mut recursion_guard = RecursionState::default();
        let mut state = ValidationState::new(
            Extra::new(
                strict,
                from_attributes,
                context,
                self_instance,
                input_type,
                self.cache_str,
                by_alias,
                by_name,
            ),
            &mut recursion_guard,
            allow_partial,
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
        context: Option<&Bound<'_, PyAny>>,
        self_instance: Option<&Bound<'_, PyAny>>,
        allow_partial: PartialMode,
        by_alias: Option<bool>,
        by_name: Option<bool>,
    ) -> ValResult<PyObject> {
        let json_value = jiter::JsonValue::parse_with_config(json_data, true, allow_partial)
            .map_err(|e| json::map_json_err(input, e, json_data))?;
        #[allow(clippy::used_underscore_items)]
        self._validate(
            py,
            &json_value,
            InputType::Json,
            strict,
            None,
            context,
            self_instance,
            allow_partial,
            by_alias,
            by_name,
        )
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

pub trait BuildValidator: Sized {
    const EXPECTED_TYPE: &'static str;

    /// Build a new validator from the schema, the return type is a trait to provide a way for validators
    /// to return other validators, see `string.rs`, `int.rs`, `float.rs` and `function.rs` for examples
    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator>;
}

/// Logic to create a particular validator, called in the `validator_match` macro, then in turn by `build_validator`
fn build_specific_validator<T: BuildValidator>(
    val_type: &str,
    schema_dict: &Bound<'_, PyDict>,
    config: Option<&Bound<'_, PyDict>>,
    definitions: &mut DefinitionsBuilder<CombinedValidator>,
) -> PyResult<CombinedValidator> {
    T::build(schema_dict, config, definitions)
        .map_err(|err| py_schema_error_type!("Error building \"{}\" validator:\n  {}", val_type, err))
}

// macro to build the match statement for validator selection
macro_rules! validator_match {
    ($type:ident, $dict:ident, $config:ident, $definitions:ident, $($validator:path,)+) => {
        match $type {
            $(
                <$validator>::EXPECTED_TYPE => build_specific_validator::<$validator>($type, $dict, $config, $definitions),
            )+
            "invalid" => return py_schema_err!("Cannot construct schema with `InvalidSchema` member."),
            _ => return py_schema_err!(r#"Unknown schema type: "{}""#, $type),
        }
    };
}

// Used when creating the base validator instance, to avoid reusing the instance
// when unpickling:
pub fn build_validator_base(
    schema: &Bound<'_, PyAny>,
    config: Option<&Bound<'_, PyDict>>,
    definitions: &mut DefinitionsBuilder<CombinedValidator>,
) -> PyResult<CombinedValidator> {
    build_validator_inner(schema, config, definitions, false)
}

pub fn build_validator(
    schema: &Bound<'_, PyAny>,
    config: Option<&Bound<'_, PyDict>>,
    definitions: &mut DefinitionsBuilder<CombinedValidator>,
) -> PyResult<CombinedValidator> {
    build_validator_inner(schema, config, definitions, true)
}

fn build_validator_inner(
    schema: &Bound<'_, PyAny>,
    config: Option<&Bound<'_, PyDict>>,
    definitions: &mut DefinitionsBuilder<CombinedValidator>,
    use_prebuilt: bool,
) -> PyResult<CombinedValidator> {
    let dict = schema.downcast::<PyDict>()?;
    let py = schema.py();
    let type_: Bound<'_, PyString> = dict.get_as_req(intern!(py, "type"))?;
    let type_ = type_.to_str()?;

    if use_prebuilt {
        // if we have a SchemaValidator on the type already, use it
        if let Ok(Some(prebuilt_validator)) = prebuilt::PrebuiltValidator::try_get_from_schema(type_, dict) {
            return Ok(prebuilt_validator);
        }
    }

    validator_match!(
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
        // tuples
        tuple::TupleValidator,
        // list/arrays
        list::ListValidator,
        // sets - unique lists
        set::SetValidator,
        // dicts/objects (recursive)
        dict::DictValidator,
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
    )
}

/// More (mostly immutable) data to pass between validators, should probably be class `Context`,
/// but that would confuse it with context as per pydantic/pydantic#1549
#[derive(Debug, Clone)]
pub struct Extra<'a, 'py> {
    /// Validation mode
    pub input_type: InputType,
    /// This is used as the `data` kwargs to validator functions
    pub data: Option<Bound<'py, PyDict>>,
    /// whether we're in strict or lax mode
    pub strict: Option<bool>,
    /// Validation time setting of `from_attributes`
    pub from_attributes: Option<bool>,
    /// context used in validator functions
    pub context: Option<&'a Bound<'py, PyAny>>,
    /// The name of the field being validated, if applicable
    pub field_name: Option<Bound<'py, PyString>>,
    /// This is an instance of the model or dataclass being validated, when validation is performed from `__init__`
    self_instance: Option<&'a Bound<'py, PyAny>>,
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
        from_attributes: Option<bool>,
        context: Option<&'a Bound<'py, PyAny>>,
        self_instance: Option<&'a Bound<'py, PyAny>>,
        input_type: InputType,
        cache_str: StringCacheMode,
        by_alias: Option<bool>,
        by_name: Option<bool>,
    ) -> Self {
        Extra {
            input_type,
            data: None,
            strict,
            from_attributes,
            field_name: None,
            context,
            self_instance,
            cache_str,
            by_alias,
            by_name,
        }
    }
}

impl Extra<'_, '_> {
    pub fn as_strict(&self) -> Self {
        Self {
            input_type: self.input_type,
            data: self.data.clone(),
            strict: Some(true),
            from_attributes: self.from_attributes,
            field_name: self.field_name.clone(),
            context: self.context,
            self_instance: self.self_instance,
            cache_str: self.cache_str,
            by_alias: self.by_alias,
            by_name: self.by_name,
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
    TaggedUnion(union::TaggedUnionValidator),
    // nullables
    Nullable(nullable::NullableValidator),
    // create new model classes
    Model(model::ModelValidator),
    ModelFields(model_fields::ModelFieldsValidator),
    // dataclasses
    DataclassArgs(dataclass::DataclassArgsValidator),
    Dataclass(dataclass::DataclassValidator),
    // strings
    Str(string::StrValidator),
    StrConstrained(string::StrConstrainedValidator),
    // integers
    Int(int::IntValidator),
    ConstrainedInt(int::ConstrainedIntValidator),
    // booleans
    Bool(bool::BoolValidator),
    // floats
    Float(float::FloatValidator),
    ConstrainedFloat(float::ConstrainedFloatValidator),
    // decimals
    Decimal(decimal::DecimalValidator),
    // lists
    List(list::ListValidator),
    // sets - unique lists
    Set(set::SetValidator),
    // tuples
    Tuple(tuple::TupleValidator),
    // dicts/objects (recursive)
    Dict(dict::DictValidator),
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
    Url(url::UrlValidator),
    MultiHostUrl(url::MultiHostUrlValidator),
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
    ) -> ValResult<PyObject>;

    /// Get a default value, currently only used by `WithDefaultValidator`
    fn default_value<'py>(
        &self,
        _py: Python<'py>,
        _outer_loc: Option<impl Into<LocItem>>,
        _state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Option<PyObject>> {
        Ok(None)
    }

    /// Validate assignment to a field of a model
    #[allow(clippy::too_many_arguments)]
    fn validate_assignment<'py>(
        &self,
        _py: Python<'py>,
        _obj: &Bound<'py, PyAny>,
        _field_name: &str,
        _field_value: &Bound<'py, PyAny>,
        _state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<PyObject> {
        let py_err = PyTypeError::new_err(format!("validate_assignment is not supported for {}", self.get_name()));
        Err(py_err.into())
    }

    /// `get_name` generally returns `Self::EXPECTED_TYPE` or some other clear identifier of the validator
    /// this is used in the error location in unions, and in the top level message in `ValidationError`
    fn get_name(&self) -> &str;
}
