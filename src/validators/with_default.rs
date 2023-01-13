use std::borrow::Cow;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::{py_err, SchemaDict};
use crate::errors::{ValError, ValResult};
use crate::input::Input;
use crate::questions::Question;
use crate::recursion_guard::RecursionGuard;

use super::{build_validator, BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub enum DefaultType {
    None,
    Default(PyObject),
    DefaultFactory(PyObject),
}

impl DefaultType {
    pub fn new(schema: &PyDict) -> PyResult<Self> {
        let py = schema.py();
        match (
            schema.get_as(intern!(py, "default"))?,
            schema.get_as(intern!(py, "default_factory"))?,
        ) {
            (Some(_), Some(_)) => py_err!("'default' and 'default_factory' cannot be used together"),
            (Some(default), None) => Ok(Self::Default(default)),
            (None, Some(default_factory)) => Ok(Self::DefaultFactory(default_factory)),
            (None, None) => Ok(Self::None),
        }
    }

    pub fn default_value(&self, py: Python) -> PyResult<Option<Cow<PyObject>>> {
        match self {
            Self::Default(ref default) => Ok(Some(Cow::Borrowed(default))),
            Self::DefaultFactory(ref default_factory) => Ok(Some(Cow::Owned(default_factory.call0(py)?))),
            Self::None => Ok(None),
        }
    }
}

#[derive(Debug, Clone)]
enum OnError {
    Raise,
    Omit,
    Default,
}

#[derive(Debug, Clone)]
pub struct WithDefaultValidator {
    default: DefaultType,
    on_error: OnError,
    validator: Box<CombinedValidator>,
    name: String,
}

impl BuildValidator for WithDefaultValidator {
    const EXPECTED_TYPE: &'static str = "default";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let default = DefaultType::new(schema)?;
        let on_error = match schema.get_as::<&str>(intern!(py, "on_error"))? {
            Some("raise") => OnError::Raise,
            Some("omit") => OnError::Omit,
            Some("default") => {
                if matches!(default, DefaultType::None) {
                    return py_err!("'on_error = default' requires a `default` or `default_factory`");
                }
                OnError::Default
            }
            None => OnError::Raise,
            // schema validation means other values are impossible
            _ => unreachable!(),
        };

        let sub_schema: &PyAny = schema.get_as_req(intern!(schema.py(), "schema"))?;
        let validator = Box::new(build_validator(sub_schema, config, build_context)?);
        let name = format!("{}[{}]", Self::EXPECTED_TYPE, validator.get_name());

        Ok(Self {
            default,
            on_error,
            validator,
            name,
        }
        .into())
    }
}

impl Validator for WithDefaultValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        match self.validator.validate(py, input, extra, slots, recursion_guard) {
            Ok(v) => Ok(v),
            Err(e) => match self.on_error {
                OnError::Raise => Err(e),
                OnError::Default => Ok(self.default.default_value(py)?.unwrap().as_ref().clone()),
                OnError::Omit => Err(ValError::Omit),
            },
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn ask(&self, question: &Question) -> bool {
        self.validator.ask(question)
    }

    fn complete(&mut self, build_context: &BuildContext<CombinedValidator>) -> PyResult<()> {
        self.validator.complete(build_context)
    }
}

impl WithDefaultValidator {
    pub fn has_default(&self) -> bool {
        !matches!(self.default, DefaultType::None)
    }

    pub fn omit_on_error(&self) -> bool {
        matches!(self.on_error, OnError::Omit)
    }
}

pub fn get_default<'a>(py: Python<'a>, validator: &'a CombinedValidator) -> PyResult<Option<Cow<'a, PyObject>>> {
    if let CombinedValidator::WithDefault(validator) = validator {
        validator.default.default_value(py)
    } else {
        Ok(None)
    }
}
