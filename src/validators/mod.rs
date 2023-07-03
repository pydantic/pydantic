use std::fmt::Debug;

use enum_dispatch::enum_dispatch;

use pyo3::exceptions::PyTypeError;
use pyo3::once_cell::GILOnceCell;
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict, PyTuple, PyType};
use pyo3::{intern, PyTraverseError, PyVisit};

use crate::build_tools::{py_schema_err, py_schema_error_type, SchemaError};
use crate::definitions::{Definitions, DefinitionsBuilder};
use crate::errors::{ErrorMode, LocItem, ValError, ValResult, ValidationError};
use crate::input::{Input, InputType};
use crate::recursion_guard::RecursionGuard;
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
mod definitions;
mod dict;
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
mod with_default;

pub use with_default::DefaultType;

use self::definitions::DefinitionRefValidator;

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
        Ok(format!("Some({})", self.value.as_ref(py).repr()?,))
    }

    #[new]
    pub fn py_new(value: PyObject) -> Self {
        Self { value }
    }

    #[classmethod]
    #[pyo3(signature = (_item, /))]
    pub fn __class_getitem__(cls: &PyType, _item: &PyAny) -> Py<PyType> {
        cls.into_py(cls.py())
    }

    #[classattr]
    fn __match_args__(py: Python) -> &PyTuple {
        PyTuple::new(py, vec![intern!(py, "value")])
    }
}

#[pyclass(module = "pydantic_core._pydantic_core")]
#[derive(Debug, Clone)]
pub struct SchemaValidator {
    validator: CombinedValidator,
    definitions: Vec<CombinedValidator>,
    schema: PyObject,
    #[pyo3(get)]
    title: PyObject,
    hide_input_in_errors: bool,
}

#[pymethods]
impl SchemaValidator {
    #[new]
    pub fn py_new(py: Python, schema: &PyAny, config: Option<&PyDict>) -> PyResult<Self> {
        let self_validator = SelfValidator::new(py)?;
        let schema = self_validator.validate_schema(py, schema)?;

        let mut definitions_builder = DefinitionsBuilder::new();

        let mut validator = build_validator(schema, config, &mut definitions_builder)?;
        validator.complete(&definitions_builder)?;
        let mut definitions = definitions_builder.clone().finish()?;
        for val in &mut definitions {
            val.complete(&definitions_builder)?;
        }
        let config_title = match config {
            Some(c) => c.get_item("title"),
            None => None,
        };
        let title = match config_title {
            Some(t) => t.into_py(py),
            None => validator.get_name().into_py(py),
        };
        let hide_input_in_errors: bool = config.get_as(intern!(py, "hide_input_in_errors"))?.unwrap_or(false);
        Ok(Self {
            validator,
            definitions,
            schema: schema.into_py(py),
            title,
            hide_input_in_errors,
        })
    }

    pub fn __reduce__(&self, py: Python) -> PyResult<PyObject> {
        let args = (self.schema.as_ref(py),);
        let cls = Py::new(py, self.clone())?.getattr(py, "__class__")?;
        Ok((cls, args).into_py(py))
    }

    #[pyo3(signature = (input, *, strict=None, from_attributes=None, context=None, self_instance=None))]
    pub fn validate_python(
        &self,
        py: Python,
        input: &PyAny,
        strict: Option<bool>,
        from_attributes: Option<bool>,
        context: Option<&PyAny>,
        self_instance: Option<&PyAny>,
    ) -> PyResult<PyObject> {
        let r = self._validate(
            py,
            input,
            InputType::Python,
            strict,
            from_attributes,
            context,
            self_instance,
        );
        r.map_err(|e| self.prepare_validation_err(py, e, ErrorMode::Python))
    }

    #[pyo3(signature = (input, *, strict=None, from_attributes=None, context=None, self_instance=None))]
    pub fn isinstance_python(
        &self,
        py: Python,
        input: &PyAny,
        strict: Option<bool>,
        from_attributes: Option<bool>,
        context: Option<&PyAny>,
        self_instance: Option<&PyAny>,
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
        input: &PyAny,
        strict: Option<bool>,
        context: Option<&PyAny>,
        self_instance: Option<&PyAny>,
    ) -> PyResult<PyObject> {
        match input.parse_json() {
            Ok(input) => {
                let r = self._validate(py, &input, InputType::Json, strict, None, context, self_instance);
                r.map_err(|e| self.prepare_validation_err(py, e, ErrorMode::Json))
            }
            Err(err) => Err(self.prepare_validation_err(py, err, ErrorMode::Json)),
        }
    }

    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (obj, field_name, field_value, *, strict=None, from_attributes=None, context=None))]
    pub fn validate_assignment(
        &self,
        py: Python,
        obj: &PyAny,
        field_name: &str,
        field_value: &PyAny,
        strict: Option<bool>,
        from_attributes: Option<bool>,
        context: Option<&PyAny>,
    ) -> PyResult<PyObject> {
        let extra = Extra {
            mode: InputType::Python,
            data: None,
            strict,
            from_attributes,
            ultra_strict: false,
            context,
            self_instance: None,
        };

        let guard = &mut RecursionGuard::default();
        self.validator
            .validate_assignment(py, obj, field_name, field_value, &extra, &self.definitions, guard)
            .map_err(|e| self.prepare_validation_err(py, e, ErrorMode::Python))
    }

    #[pyo3(signature = (*, strict=None, context=None))]
    pub fn get_default_value(&self, py: Python, strict: Option<bool>, context: Option<&PyAny>) -> PyResult<PyObject> {
        let extra = Extra {
            mode: InputType::Python,
            data: None,
            strict,
            from_attributes: None,
            ultra_strict: false,
            context,
            self_instance: None,
        };
        let recursion_guard = &mut RecursionGuard::default();
        let r = self
            .validator
            .default_value(py, None::<i64>, &extra, &self.definitions, recursion_guard);
        match r {
            Ok(maybe_default) => match maybe_default {
                Some(v) => Ok(PySome::new(v).into_py(py)),
                None => Ok(py.None().into_py(py)),
            },
            Err(e) => Err(self.prepare_validation_err(py, e, ErrorMode::Python)),
        }
    }

    pub fn __repr__(&self, py: Python) -> String {
        format!(
            "SchemaValidator(title={:?}, validator={:#?}, definitions={:#?})",
            self.title.extract::<&str>(py).unwrap(),
            self.validator,
            self.definitions,
        )
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        self.validator.py_gc_traverse(&visit)?;
        visit.call(&self.schema)?;
        for slot in &self.definitions {
            slot.py_gc_traverse(&visit)?;
        }
        Ok(())
    }

    fn __clear__(&mut self) {
        self.validator.py_gc_clear();
        for slot in &mut self.definitions {
            slot.py_gc_clear();
        }
    }
}

impl SchemaValidator {
    #[allow(clippy::too_many_arguments)]
    fn _validate<'s, 'data>(
        &'data self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        mode: InputType,
        strict: Option<bool>,
        from_attributes: Option<bool>,
        context: Option<&'data PyAny>,
        self_instance: Option<&PyAny>,
    ) -> ValResult<'data, PyObject>
    where
        's: 'data,
    {
        self.validator.validate(
            py,
            input,
            &Extra::new(strict, from_attributes, context, self_instance, mode),
            &self.definitions,
            &mut RecursionGuard::default(),
        )
    }

    fn prepare_validation_err(&self, py: Python, error: ValError, error_mode: ErrorMode) -> PyErr {
        ValidationError::from_val_error(
            py,
            self.title.clone_ref(py),
            error_mode,
            error,
            None,
            self.hide_input_in_errors,
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

    pub fn validate_schema(&self, py: Python<'py>, schema: &'py PyAny) -> PyResult<&'py PyAny> {
        let extra = Extra::new(None, None, None, None, InputType::Python);
        match self.validator.validator.validate(
            py,
            schema,
            &extra,
            &self.validator.definitions,
            &mut RecursionGuard::default(),
        ) {
            Ok(schema_obj) => Ok(schema_obj.into_ref(py)),
            Err(e) => Err(SchemaError::from_val_error(py, e)),
        }
    }

    fn build(py: Python) -> PyResult<SchemaValidator> {
        let code = include_str!("../self_schema.py");
        let locals = PyDict::new(py);
        py.run(code, None, Some(locals))?;
        let self_schema: &PyDict = locals.get_as_req(intern!(py, "self_schema"))?;

        let mut definitions_builder = DefinitionsBuilder::new();

        let mut validator = match build_validator(self_schema, None, &mut definitions_builder) {
            Ok(v) => v,
            Err(err) => return py_schema_err!("Error building self-schema:\n  {}", err),
        };
        validator.complete(&definitions_builder)?;
        let mut definitions = definitions_builder.clone().finish()?;
        for val in &mut definitions {
            val.complete(&definitions_builder)?;
        }
        Ok(SchemaValidator {
            validator,
            definitions,
            schema: py.None(),
            title: "Self Schema".into_py(py),
            hide_input_in_errors: false,
        })
    }
}

pub trait BuildValidator: Sized {
    const EXPECTED_TYPE: &'static str;

    /// Build a new validator from the schema, the return type is a trait to provide a way for validators
    /// to return other validators, see `string.rs`, `int.rs`, `float.rs` and `function.rs` for examples
    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator>;
}

/// Logic to create a particular validator, called in the `validator_match` macro, then in turn by `build_validator`
fn build_specific_validator<'a, T: BuildValidator>(
    val_type: &str,
    schema_dict: &'a PyDict,
    config: Option<&'a PyDict>,
    definitions: &mut DefinitionsBuilder<CombinedValidator>,
) -> PyResult<CombinedValidator> {
    let py = schema_dict.py();
    if let Some(schema_ref) = schema_dict.get_as::<String>(intern!(py, "ref"))? {
        let inner_val = T::build(schema_dict, config, definitions)?;
        let validator_id = definitions.add_definition(schema_ref, inner_val)?;
        return Ok(DefinitionRefValidator::new(validator_id).into());
    }

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

pub fn build_validator<'a>(
    schema: &'a PyAny,
    config: Option<&'a PyDict>,
    definitions: &mut DefinitionsBuilder<CombinedValidator>,
) -> PyResult<CombinedValidator> {
    let dict: &PyDict = schema.downcast()?;
    let type_: &str = dict.get_as_req(intern!(schema.py(), "type"))?;
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
        // tuples
        tuple::TuplePositionalValidator,
        tuple::TupleVariableValidator,
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
        // recursive (self-referencing) models
        definitions::DefinitionRefValidator,
        definitions::DefinitionsValidatorBuilder,
    )
}

/// More (mostly immutable) data to pass between validators, should probably be class `Context`,
/// but that would confuse it with context as per pydantic/pydantic#1549
#[derive(Debug)]
pub struct Extra<'a> {
    /// Validation mode
    pub mode: InputType,
    /// This is used as the `data` kwargs to validator functions
    pub data: Option<&'a PyDict>,
    /// whether we're in strict or lax mode
    pub strict: Option<bool>,
    /// whether we're in ultra-strict mode, only used occasionally in unions
    pub ultra_strict: bool,
    /// Validation time setting of `from_attributes`
    pub from_attributes: Option<bool>,
    /// context used in validator functions
    pub context: Option<&'a PyAny>,
    /// This is an instance of the model or dataclass being validated, when validation is performed from `__init__`
    self_instance: Option<&'a PyAny>,
}

impl<'a> Extra<'a> {
    pub fn new(
        strict: Option<bool>,
        from_attributes: Option<bool>,
        context: Option<&'a PyAny>,
        self_instance: Option<&'a PyAny>,
        mode: InputType,
    ) -> Self {
        Extra {
            mode,
            data: None,
            strict,
            ultra_strict: false,
            from_attributes,
            context,
            self_instance,
        }
    }
}

impl<'a> Extra<'a> {
    pub fn as_strict(&self, ultra_strict: bool) -> Self {
        Self {
            mode: self.mode,
            data: self.data,
            strict: Some(true),
            ultra_strict,
            from_attributes: self.from_attributes,
            context: self.context,
            self_instance: self.self_instance,
        }
    }
}

#[derive(Debug, Clone)]
#[enum_dispatch]
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
    // lists
    List(list::ListValidator),
    // sets - unique lists
    Set(set::SetValidator),
    // tuples
    TuplePositional(tuple::TuplePositionalValidator),
    TupleVariable(tuple::TupleVariableValidator),
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
    // reference to definition, useful for recursive (self-referencing) models
    DefinitionRef(definitions::DefinitionRefValidator),
    // input dependent
    JsonOrPython(json_or_python::JsonOrPython),
}

/// This trait must be implemented by all validators, it allows various validators to be accessed consistently,
/// validators defined in `build_validator` also need `EXPECTED_TYPE` as a const, but that can't be part of the trait
#[enum_dispatch(CombinedValidator)]
pub trait Validator: Send + Sync + Clone + Debug {
    fn py_gc_traverse(&self, _visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        Ok(())
    }
    fn py_gc_clear(&mut self) {}

    /// Do the actual validation for this schema/type
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        definitions: &'data Definitions<CombinedValidator>,
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject>;

    /// Get a default value, currently only used by `WithDefaultValidator`
    fn default_value<'s, 'data>(
        &'s self,
        _py: Python<'data>,
        _outer_loc: Option<impl Into<LocItem>>,
        _extra: &Extra,
        _definitions: &'data Definitions<CombinedValidator>,
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, Option<PyObject>> {
        Ok(None)
    }

    /// Validate assignment to a field of a model
    #[allow(clippy::too_many_arguments)]
    fn validate_assignment<'s, 'data: 's>(
        &'s self,
        _py: Python<'data>,
        _obj: &'data PyAny,
        _field_name: &'data str,
        _field_value: &'data PyAny,
        _extra: &Extra,
        _definitions: &'data Definitions<CombinedValidator>,
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let py_err = PyTypeError::new_err(format!("validate_assignment is not supported for {}", self.get_name()));
        Err(py_err.into())
    }

    /// whether the validator behaves differently in strict mode, and in ultra strict mode
    /// implementations should return true if any of their sub-validators return true
    fn different_strict_behavior(
        &self,
        definitions: Option<&DefinitionsBuilder<CombinedValidator>>,
        ultra_strict: bool,
    ) -> bool;

    /// `get_name` generally returns `Self::EXPECTED_TYPE` or some other clear identifier of the validator
    /// this is used in the error location in unions, and in the top level message in `ValidationError`
    fn get_name(&self) -> &str;

    /// this method must be implemented for any validator which holds references to other validators,
    /// it is used by `DefinitionRefValidator` to set its name
    fn complete(&mut self, _definitions: &DefinitionsBuilder<CombinedValidator>) -> PyResult<()>;
}
