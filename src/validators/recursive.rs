use std::sync::{Arc, RwLock, Weak};

use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::{py_error, SchemaDict};
use crate::errors::{as_internal, ValResult};
use crate::input::Input;

use super::{build_validator, Extra, Validator};

pub type ValidatorArc = Arc<RwLock<Box<dyn Validator>>>;

#[derive(Debug, Clone)]
pub struct RecursiveValidator {
    validator_arc: ValidatorArc,
    name: String,
}

impl RecursiveValidator {
    pub const EXPECTED_TYPE: &'static str = "recursive-container";
}

impl Validator for RecursiveValidator {
    fn build(schema: &PyDict, config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        let sub_schema: &PyAny = schema.get_as_req("schema")?;
        let validator = build_validator(sub_schema, config)?.0;
        let name: String = schema.get_as_req("name")?;
        let validator_arc = Arc::new(RwLock::new(validator));
        match validator_arc.write() {
            Ok(mut validator_guard) => validator_guard.set_ref(name.as_str(), &validator_arc),
            Err(err) => py_error!("Recursive container build error: {}", err),
        }?;
        Ok(Box::new(Self { validator_arc, name }))
    }

    fn set_ref(&mut self, name: &str, validator_arc: &ValidatorArc) -> PyResult<()> {
        match self.validator_arc.write() {
            Ok(mut validator_guard) => validator_guard.set_ref(name, validator_arc),
            Err(err) => py_error!("Recursive container set_ref error: {}", err),
        }
    }

    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        match self.validator_arc.read() {
            Ok(validator) => validator.validate(py, input, extra),
            Err(err) => {
                py_error!(PyRuntimeError; "Recursive container error: {}", err.to_string()).map_err(as_internal)
            }
        }
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        self.validate(py, input, extra)
    }

    fn get_name(&self, _py: Python) -> String {
        self.name.clone()
    }

    #[no_coverage]
    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}

#[derive(Debug, Clone)]
pub struct RecursiveRefValidator {
    validator_ref: Option<Weak<RwLock<Box<dyn Validator>>>>,
    name: String,
}

impl RecursiveRefValidator {
    pub const EXPECTED_TYPE: &'static str = "recursive-ref";
}

impl Validator for RecursiveRefValidator {
    fn build(schema: &PyDict, _config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        Ok(Box::new(Self {
            validator_ref: None,
            name: schema.get_as_req("name")?,
        }))
    }

    fn set_ref(&mut self, name: &str, validator_arc: &ValidatorArc) -> PyResult<()> {
        if self.validator_ref.is_none() && name == self.name.as_str() {
            self.validator_ref = Some(Arc::downgrade(validator_arc));
        }
        Ok(())
    }

    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        let error_msg: String = match self.validator_ref {
            Some(ref validator_ref) => {
                if let Some(validator_arc) = validator_ref.upgrade() {
                    match validator_arc.read() {
                        Ok(validator) => return validator.validate(py, input, extra),
                        Err(err) => format!("PoisonError: {}", err),
                    }
                } else {
                    "unable to upgrade weak reference".to_string()
                }
            }
            None => "ref not yet set".to_string(),
        };
        py_error!(PyRuntimeError; "Recursive reference error: {}", error_msg).map_err(as_internal)
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        self.validate(py, input, extra)
    }

    fn get_name(&self, _py: Python) -> String {
        self.name.clone()
    }

    #[no_coverage]
    fn clone_dyn(&self) -> Box<dyn Validator> {
        Box::new(self.clone())
    }
}
