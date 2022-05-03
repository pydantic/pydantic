use std::sync::{Arc, RwLock, Weak};

use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::{py_error, SchemaDict};
use crate::errors::{as_internal, ValResult};
use crate::input::Input;

use super::{build_validator, BuildValidator, Extra, ValidateEnum, Validator};

pub type ValidatorArc = Arc<RwLock<ValidateEnum>>;

#[derive(Debug, Clone)]
pub struct RecursiveValidator {
    validator_arc: ValidatorArc,
    name: String,
}

impl BuildValidator for RecursiveValidator {
    const EXPECTED_TYPE: &'static str = "recursive-container";

    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<ValidateEnum> {
        let sub_schema: &PyAny = schema.get_as_req("schema")?;
        let validator = build_validator(sub_schema, config)?.0;
        let name: String = schema.get_as_req("name")?;
        let validator_arc = Arc::new(RwLock::new(validator));
        match validator_arc.write() {
            Ok(mut validator_guard) => validator_guard.set_ref(&name, &validator_arc),
            Err(err) => py_error!("Recursive container build error: {}", err),
        }?;
        Ok(Self { validator_arc, name }.into())
    }
}

impl Validator for RecursiveValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        match self.validator_arc.read() {
            Ok(validator) => validator.validate(py, input, extra),
            Err(err) => py_error!(PyRuntimeError; "Recursive container error: {}", err).map_err(as_internal),
        }
    }

    fn set_ref(&mut self, name: &str, validator_arc: &ValidatorArc) -> PyResult<()> {
        match self.validator_arc.write() {
            Ok(mut validator_guard) => validator_guard.set_ref(name, validator_arc),
            Err(err) => py_error!("Recursive container set_ref error: {}", err),
        }
    }

    fn get_name(&self, _py: Python) -> String {
        self.name.clone()
    }
}

#[derive(Debug, Clone)]
pub struct RecursiveRefValidator {
    validator_ref: Option<Weak<RwLock<ValidateEnum>>>,
    name: String,
}

impl BuildValidator for RecursiveRefValidator {
    const EXPECTED_TYPE: &'static str = "recursive-ref";

    fn build(schema: &PyDict, _config: Option<&PyDict>) -> PyResult<ValidateEnum> {
        Ok(Self {
            validator_ref: None,
            name: schema.get_as_req("name")?,
        }
        .into())
    }
}

impl Validator for RecursiveRefValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        match self.validator_ref {
            Some(ref validator_ref) => match validator_ref.upgrade() {
                Some(validator_arc) => match validator_arc.read() {
                    Ok(validator) => validator.validate(py, input, extra),
                    Err(err) => py_error!(PyRuntimeError; "Recursive reference error: PoisonError: {}", err)
                        .map_err(as_internal),
                },
                None => py_error!(PyRuntimeError; "Recursive reference error: unable to upgrade weak reference")
                    .map_err(as_internal),
            },
            None => py_error!(PyRuntimeError; "Recursive reference error: ref not yet set").map_err(as_internal),
        }
    }

    fn set_ref(&mut self, name: &str, validator_arc: &ValidatorArc) -> PyResult<()> {
        if self.validator_ref.is_none() && name == self.name {
            self.validator_ref = Some(Arc::downgrade(validator_arc));
        }
        Ok(())
    }

    fn get_name(&self, _py: Python) -> String {
        self.name.clone()
    }
}
