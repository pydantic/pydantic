use std::fmt::Debug;

use enum_dispatch::enum_dispatch;
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict};
use serde_json::from_str as parse_json;

use crate::build_tools::{py_error, SchemaDict};
use crate::errors::{as_validation_err, val_line_error, ErrorKind, InputValue, ValError, ValResult};
use crate::input::{Input, JsonInput};
use crate::SchemaError;

mod any;
mod bool;
mod dict;
mod float;
mod function;
mod int;
mod list;
mod literal;
mod model;
mod model_class;
mod none;
mod optional;
mod recursive;
mod set;
mod string;
mod union;

use self::recursive::ValidatorArc;

#[pyclass]
#[derive(Debug, Clone)]
pub struct SchemaValidator {
    validator: ValidateEnum,
}

#[pymethods]
impl SchemaValidator {
    #[new]
    pub fn py_new(py: Python, schema: &PyAny) -> PyResult<Self> {
        let validator = match build_validator(schema, None) {
            Ok((v, _)) => v,
            Err(err) => {
                return Err(match err.is_instance_of::<SchemaError>(py) {
                    true => err,
                    false => SchemaError::new_err(format!("Schema build error:\n  {}", err)),
                });
            }
        };

        Ok(Self { validator })
    }

    fn validate_python(&self, py: Python, input: &PyAny) -> PyResult<PyObject> {
        let extra = Extra {
            data: None,
            field: None,
        };
        let r = self.validator.validate(py, input, &extra);
        r.map_err(|e| as_validation_err(py, &self.validator.get_name(py), e))
    }

    fn validate_json(&self, py: Python, input: String) -> PyResult<PyObject> {
        match parse_json::<JsonInput>(input.as_str()) {
            Ok(input) => {
                let extra = Extra {
                    data: None,
                    field: None,
                };
                let r = self.validator.validate(py, &input, &extra);
                r.map_err(|e| as_validation_err(py, &self.validator.get_name(py), e))
            }
            Err(e) => {
                let line_err = val_line_error!(
                    input_value = InputValue::InputRef(&input),
                    message = Some(e.to_string()),
                    kind = ErrorKind::InvalidJson
                );
                let err = ValError::LineErrors(vec![line_err]);
                Err(as_validation_err(py, &self.validator.get_name(py), err))
            }
        }
    }

    fn validate_assignment(&self, py: Python, field: String, input: &PyAny, data: &PyDict) -> PyResult<PyObject> {
        let extra = Extra {
            data: Some(data),
            field: Some(field.as_str()),
        };
        let r = self.validator.validate(py, input, &extra);
        r.map_err(|e| as_validation_err(py, &self.validator.get_name(py), e))
    }

    fn __repr__(&self, py: Python) -> String {
        format!(
            "SchemaValidator(name={:?}, validator={:#?})",
            self.validator.get_name(py),
            self.validator
        )
    }
}

pub trait BuildValidator: Sized {
    const EXPECTED_TYPE: &'static str;

    /// Build a new validator from the schema, the return type is a trait to provide a way for validators
    /// to return other validators, see `string.rs`, `int.rs`, `float.rs` and `function.rs` for examples
    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<ValidateEnum>;
}

// macro to build the match statement for validator selection
macro_rules! validator_match {
    ($type:ident, $dict:ident, $config:ident, $($validator:path,)+) => {
        match $type {
            $(
                <$validator>::EXPECTED_TYPE => {
                    let val = <$validator>::build($dict, $config).map_err(|err| {
                        crate::SchemaError::new_err(format!("Error building \"{}\" validator:\n  {}", $type, err))
                    })?;
                    Ok((val, $dict))
                },
            )+
            _ => {
                return py_error!(r#"Unknown schema type: "{}""#, $type)
            },
        }
    };
}

pub fn build_validator<'a>(schema: &'a PyAny, config: Option<&'a PyDict>) -> PyResult<(ValidateEnum, &'a PyDict)> {
    let dict: &PyDict = match schema.cast_as() {
        Ok(s) => s,
        Err(_) => {
            let dict = PyDict::new(schema.py());
            dict.set_item("type", schema)?;
            dict
        }
    };
    let type_: &str = dict.get_as_req("type")?;
    validator_match!(
        type_,
        dict,
        config,
        // models e.g. heterogeneous dicts
        self::model::ModelValidator,
        // unions
        self::union::UnionValidator,
        // optional e.g. nullable
        self::optional::OptionalValidator,
        // model classes
        self::model_class::ModelClassValidator,
        // strings
        self::string::StrValidator,
        // integers
        self::int::IntValidator,
        // boolean
        self::bool::BoolValidator,
        // floats
        self::float::FloatValidator,
        // list/arrays
        self::list::ListValidator,
        // sets - unique lists
        self::set::SetValidator,
        // dicts/objects (recursive)
        self::dict::DictValidator,
        // None/null
        self::none::NoneValidator,
        // functions - before, after, plain & wrap
        self::function::FunctionBuilder,
        // recursive (self-referencing) models
        self::recursive::RecursiveValidator,
        self::recursive::RecursiveRefValidator,
        // literals
        self::literal::LiteralBuilder,
        // any
        self::any::AnyValidator,
    )
}

/// More (mostly immutable) data to pass between validators, should probably be class `Context`,
/// but that would confuse it with context as per samuelcolvin/pydantic#1549
#[derive(Debug)]
pub struct Extra<'a> {
    /// This is used as the `data` kwargs to validator functions, it's also represents the current model
    /// data when validating assignment
    pub data: Option<&'a PyDict>,
    /// The field being assigned to when validating assignment
    pub field: Option<&'a str>,
}

#[derive(Debug, Clone)]
#[enum_dispatch]
pub enum ValidateEnum {
    // models e.g. heterogeneous dicts
    Model(self::model::ModelValidator),
    // unions
    Union(self::union::UnionValidator),
    // optional e.g. nullable
    Optional(self::optional::OptionalValidator),
    // model classes
    ModelClass(self::model_class::ModelClassValidator),
    // strings
    Str(self::string::StrValidator),
    StrictStr(self::string::StrictStrValidator),
    StrConstrained(self::string::StrConstrainedValidator),
    // integers
    Int(self::int::IntValidator),
    StrictInt(self::int::StrictIntValidator),
    ConstrainedInt(self::int::ConstrainedIntValidator),
    // booleans
    Bool(self::bool::BoolValidator),
    StrictBool(self::bool::StrictBoolValidator),
    // floats
    Float(self::float::FloatValidator),
    StrictFloat(self::float::StrictFloatValidator),
    ConstrainedFloat(self::float::ConstrainedFloatValidator),
    // lists
    List(self::list::ListValidator),
    // sets - unique lists
    Set(self::set::SetValidator),
    // dicts/objects (recursive)
    Dict(self::dict::DictValidator),
    // None/null
    None(self::none::NoneValidator),
    // functions
    FunctionBefore(self::function::FunctionBeforeValidator),
    FunctionAfter(self::function::FunctionAfterValidator),
    FunctionPlain(self::function::FunctionPlainValidator),
    FunctionWrap(self::function::FunctionWrapValidator),
    // recursive (self-referencing) models
    Recursive(self::recursive::RecursiveValidator),
    RecursiveRef(self::recursive::RecursiveRefValidator),
    // literals
    LiteralSingleString(self::literal::LiteralSingleStringValidator),
    LiteralSingleInt(self::literal::LiteralSingleIntValidator),
    LiteralMultipleStrings(self::literal::LiteralMultipleStringsValidator),
    LiteralMultipleInts(self::literal::LiteralMultipleIntsValidator),
    LiteralGeneral(self::literal::LiteralGeneralValidator),
    // any
    Any(self::any::AnyValidator),
}

/// This trait must be implemented by all validators, it allows various validators to be accessed consistently,
/// validators defined in `build_validator` also need `EXPECTED_TYPE` as a const, but that can't be part of the trait
#[enum_dispatch(ValidateEnum)]
pub trait Validator: Send + Sync + Clone + Debug {
    /// Do the actual validation for this schema/type
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
    ) -> ValResult<'data, PyObject>;

    /// This is used in unions for the first pass to see if we have an "exact match",
    /// implementations should generally use the same logic as with `config.strict = true`
    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        self.validate(py, input, extra)
    }

    /// `set_ref` is used in recursive models to set the weak reference in the `RecursiveRefValidator`,
    /// I can't imagine any other use, but then maybe I'm not very imaginative...
    fn set_ref(&mut self, _name: &str, _validator_arc: &ValidatorArc) -> PyResult<()> {
        Ok(())
    }

    /// `get_name` generally returns `Self::EXPECTED_TYPE` or some other clear identifier of the validator
    /// this is used in the error location in unions, and in the top level message in `ValidationError`
    fn get_name(&self, py: Python) -> String;
}
