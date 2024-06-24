use std::fmt::Debug;

use enum_dispatch::enum_dispatch;
use jiter::StringCacheMode;

use pyo3::exceptions::PyTypeError;
use pyo3::prelude::*;
use pyo3::sync::GILOnceCell;
use pyo3::types::{PyAny, PyDict, PyString, PyTuple, PyType};
use pyo3::{intern, PyTraverseError, PyVisit};

use crate::build_tools::{py_schema_err, py_schema_error_type, SchemaError};
use crate::definitions::{Definitions, DefinitionsBuilder};
use crate::errors::{LocItem, ValError, ValResult, ValidationError};
use crate::input::{Input, InputType, StringMapping};
use crate::py_gc::PyGcTraverse;
use crate::recursion_guard::RecursionState;
use crate::tools::SchemaDict;

mod any;
mod arguments;
mod bool;
mod bytes;
mod call;
mod callable;
mod chain;
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
mod model;
mod model_fields;
mod none;
mod nullable;
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
    fn __match_args__(py: Python) -> Bound<'_, PyTuple> {
        PyTuple::new_bound(py, vec![intern!(py, "value")])
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

        let validator = build_validator(schema, config, &mut definitions_builder)?;
        let definitions = definitions_builder.finish()?;
        let py_schema = schema.into_py(py);
        let py_config = match config {
            Some(c) if !c.is_empty() => Some(c.clone().into()),
            _ => None,
        };
        let config_title = match config {
            Some(c) => c.get_item("title")?,
            None => None,
        };
        let title = match config_title {
            Some(t) => t.into_py(py),
            None => validator.get_name().into_py(py),
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

    pub fn __reduce__(slf: &Bound<Self>) -> PyResult<(PyObject, (PyObject, PyObject))> {
        // Enables support for `pickle` serialization.
        let py = slf.py();
        let cls = slf.get_type().into();
        let init_args = (slf.get().py_schema.to_object(py), slf.get().py_config.to_object(py));
        Ok((cls, init_args))
    }

    #[pyo3(signature = (input, *, strict=None, from_attributes=None, context=None, self_instance=None))]
    pub fn validate_python(
        &self,
        py: Python,
        input: &Bound<'_, PyAny>,
        strict: Option<bool>,
        from_attributes: Option<bool>,
        context: Option<&Bound<'_, PyAny>>,
        self_instance: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<PyObject> {
        self._validate(
            py,
            input,
            InputType::Python,
            strict,
            from_attributes,
            context,
            self_instance,
        )
        .map_err(|e| self.prepare_validation_err(py, e, InputType::Python))
    }

    #[pyo3(signature = (input, *, strict=None, from_attributes=None, context=None, self_instance=None))]
    pub fn isinstance_python(
        &self,
        py: Python,
        input: &Bound<'_, PyAny>,
        strict: Option<bool>,
        from_attributes: Option<bool>,
        context: Option<&Bound<'_, PyAny>>,
        self_instance: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<bool> {
        match self._validate(
            py,
            input,
            InputType::Python,
            strict,
            from_attributes,
            context,
            self_instance,
        ) {
            Ok(_) => Ok(true),
            Err(ValError::InternalErr(err)) => Err(err),
            Err(ValError::Omit) => Err(ValidationError::omit_error()),
            Err(ValError::UseDefault) => Err(ValidationError::use_default_error()),
            Err(ValError::LineErrors(_)) => Ok(false),
        }
    }

    #[pyo3(signature = (input, *, strict=None, context=None, self_instance=None))]
    pub fn validate_json(
        &self,
        py: Python,
        input: &Bound<'_, PyAny>,
        strict: Option<bool>,
        context: Option<&Bound<'_, PyAny>>,
        self_instance: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<PyObject> {
        let r = match json::validate_json_bytes(input) {
            Ok(v_match) => self._validate_json(
                py,
                input,
                v_match.into_inner().as_slice(),
                strict,
                context,
                self_instance,
            ),
            Err(err) => Err(err),
        };
        r.map_err(|e| self.prepare_validation_err(py, e, InputType::Json))
    }

    #[pyo3(signature = (input, *, strict=None, context=None))]
    pub fn validate_strings(
        &self,
        py: Python,
        input: Bound<'_, PyAny>,
        strict: Option<bool>,
        context: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<PyObject> {
        let t = InputType::String;
        let string_mapping = StringMapping::new_value(input).map_err(|e| self.prepare_validation_err(py, e, t))?;

        match self._validate(py, &string_mapping, t, strict, None, context, None) {
            Ok(r) => Ok(r),
            Err(e) => Err(self.prepare_validation_err(py, e, t)),
        }
    }

    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (obj, field_name, field_value, *, strict=None, from_attributes=None, context=None))]
    pub fn validate_assignment(
        &self,
        py: Python,
        obj: Bound<'_, PyAny>,
        field_name: &str,
        field_value: Bound<'_, PyAny>,
        strict: Option<bool>,
        from_attributes: Option<bool>,
        context: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<PyObject> {
        let extra = Extra {
            input_type: InputType::Python,
            data: None,
            strict,
            from_attributes,
            context,
            self_instance: None,
            cache_str: self.cache_str,
        };

        let guard = &mut RecursionState::default();
        let mut state = ValidationState::new(extra, guard);
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
            context,
            self_instance: None,
            cache_str: self.cache_str,
        };
        let recursion_guard = &mut RecursionState::default();
        let mut state = ValidationState::new(extra, recursion_guard);
        let r = self.validator.default_value(py, None::<i64>, &mut state);
        match r {
            Ok(maybe_default) => match maybe_default {
                Some(v) => Ok(PySome::new(v).into_py(py)),
                None => Ok(py.None().into_py(py)),
            },
            Err(e) => Err(self.prepare_validation_err(py, e, InputType::Python)),
        }
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
            ),
            &mut recursion_guard,
        );
        self.validator.validate(py, input, &mut state)
    }

    fn _validate_json(
        &self,
        py: Python,
        input: &Bound<'_, PyAny>,
        json_data: &[u8],
        strict: Option<bool>,
        context: Option<&Bound<'_, PyAny>>,
        self_instance: Option<&Bound<'_, PyAny>>,
    ) -> ValResult<PyObject> {
        let json_value =
            jiter::JsonValue::parse(json_data, true).map_err(|e| json::map_json_err(input, e, json_data))?;
        self._validate(py, &json_value, InputType::Json, strict, None, context, self_instance)
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

static SCHEMA_DEFINITION: GILOnceCell<SchemaValidator> = GILOnceCell::new();

#[derive(Debug, Clone)]
pub struct SelfValidator<'py> {
    validator: &'py SchemaValidator,
}

impl<'py> SelfValidator<'py> {
    pub fn new(py: Python<'py>) -> PyResult<Self> {
        let validator = SCHEMA_DEFINITION.get_or_init(py, || match Self::build(py) {
            Ok(schema) => schema,
            Err(e) => panic!("Error building schema validator:\n  {e}"),
        });
        Ok(Self { validator })
    }

    pub fn validate_schema(&self, schema: &Bound<'py, PyAny>, strict: Option<bool>) -> PyResult<Bound<'py, PyAny>> {
        let py = schema.py();
        let mut recursion_guard = RecursionState::default();
        let mut state = ValidationState::new(
            Extra::new(strict, None, None, None, InputType::Python, true.into()),
            &mut recursion_guard,
        );
        match self.validator.validator.validate(py, schema, &mut state) {
            Ok(schema_obj) => Ok(schema_obj.into_bound(py)),
            Err(e) => Err(SchemaError::from_val_error(py, e)),
        }
    }

    fn build(py: Python) -> PyResult<SchemaValidator> {
        let code = include_str!("../self_schema.py");
        let locals = PyDict::new_bound(py);
        py.run_bound(code, None, Some(&locals))?;
        let self_schema = locals.get_as_req(intern!(py, "self_schema"))?;

        let mut definitions_builder = DefinitionsBuilder::new();

        let validator = match build_validator(&self_schema, None, &mut definitions_builder) {
            Ok(v) => v,
            Err(err) => return py_schema_err!("Error building self-schema:\n  {}", err),
        };
        let definitions = definitions_builder.finish()?;
        Ok(SchemaValidator {
            validator,
            definitions,
            py_schema: py.None(),
            py_config: None,
            title: "Self Schema".into_py(py),
            hide_input_in_errors: false,
            validation_error_cause: false,
            cache_str: true.into(),
        })
    }
}

#[pyfunction(signature = (schema, *, strict = None))]
pub fn validate_core_schema<'py>(schema: &Bound<'py, PyAny>, strict: Option<bool>) -> PyResult<Bound<'py, PyAny>> {
    let self_validator = SelfValidator::new(schema.py())?;
    self_validator.validate_schema(schema, strict)
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
            _ => return py_schema_err!(r#"Unknown schema type: "{}""#, $type),
        }
    };
}

pub fn build_validator(
    schema: &Bound<'_, PyAny>,
    config: Option<&Bound<'_, PyDict>>,
    definitions: &mut DefinitionsBuilder<CombinedValidator>,
) -> PyResult<CombinedValidator> {
    let dict = schema.downcast::<PyDict>()?;
    let type_: Bound<'_, PyString> = dict.get_as_req(intern!(schema.py(), "type"))?;
    let type_ = type_.to_str()?;
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
    /// This is an instance of the model or dataclass being validated, when validation is performed from `__init__`
    self_instance: Option<&'a Bound<'py, PyAny>>,
    /// Whether to use a cache of short strings to accelerate python string construction
    cache_str: StringCacheMode,
}

impl<'a, 'py> Extra<'a, 'py> {
    pub fn new(
        strict: Option<bool>,
        from_attributes: Option<bool>,
        context: Option<&'a Bound<'py, PyAny>>,
        self_instance: Option<&'a Bound<'py, PyAny>>,
        input_type: InputType,
        cache_str: StringCacheMode,
    ) -> Self {
        Extra {
            input_type,
            data: None,
            strict,
            from_attributes,
            context,
            self_instance,
            cache_str,
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
            context: self.context,
            self_instance: self.self_instance,
            cache_str: self.cache_str,
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
