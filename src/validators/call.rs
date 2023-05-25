use pyo3::exceptions::PyTypeError;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyTuple};

use crate::errors::ValResult;
use crate::input::Input;
use crate::recursion_guard::RecursionGuard;
use crate::tools::SchemaDict;

use super::{build_validator, BuildValidator, CombinedValidator, Definitions, DefinitionsBuilder, Extra, Validator};

#[derive(Debug, Clone)]
pub struct CallValidator {
    function: PyObject,
    arguments_validator: Box<CombinedValidator>,
    return_validator: Option<Box<CombinedValidator>>,
    name: String,
}

impl BuildValidator for CallValidator {
    const EXPECTED_TYPE: &'static str = "call";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();

        let arguments_schema: &PyAny = schema.get_as_req(intern!(py, "arguments_schema"))?;
        let arguments_validator = Box::new(build_validator(arguments_schema, config, definitions)?);

        let return_schema = schema.get_item(intern!(py, "return_schema"));
        let return_validator = match return_schema {
            Some(return_schema) => Some(Box::new(build_validator(return_schema, config, definitions)?)),
            None => None,
        };
        let function: &PyAny = schema.get_as_req(intern!(py, "function"))?;
        let function_name: &str = match schema.get_as(intern!(py, "function_name"))? {
            Some(name) => name,
            None => {
                match function.getattr(intern!(py, "__name__")) {
                    Ok(name) => name.extract()?,
                    Err(_) => {
                        // partials we use `function.func.__name__`
                        if let Ok(func) = function.getattr(intern!(py, "func")) {
                            func.getattr(intern!(py, "__name__"))?.extract()?
                        } else {
                            "<unknown>"
                        }
                    }
                }
            }
        };
        let name = format!("{}[{function_name}]", Self::EXPECTED_TYPE);

        Ok(Self {
            function: function.to_object(py),
            arguments_validator,
            return_validator,
            name,
        }
        .into())
    }
}

impl Validator for CallValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        definitions: &'data Definitions<CombinedValidator>,
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let args = self
            .arguments_validator
            .validate(py, input, extra, definitions, recursion_guard)?;

        let return_value = if let Ok((args, kwargs)) = args.extract::<(&PyTuple, &PyDict)>(py) {
            self.function.call(py, args, Some(kwargs))?
        } else if let Ok(kwargs) = args.downcast::<PyDict>(py) {
            self.function.call(py, (), Some(kwargs))?
        } else {
            let msg = "Arguments validator should return a tuple of (args, kwargs) or a dict of kwargs";
            return Err(PyTypeError::new_err(msg).into());
        };

        if let Some(return_validator) = &self.return_validator {
            return_validator
                .validate(py, return_value.into_ref(py), extra, definitions, recursion_guard)
                .map_err(|e| e.with_outer_location("return".into()))
        } else {
            Ok(return_value.to_object(py))
        }
    }

    fn different_strict_behavior(
        &self,
        definitions: Option<&DefinitionsBuilder<CombinedValidator>>,
        ultra_strict: bool,
    ) -> bool {
        if let Some(return_validator) = &self.return_validator {
            if return_validator.different_strict_behavior(definitions, ultra_strict) {
                return true;
            }
        }
        self.arguments_validator
            .different_strict_behavior(definitions, ultra_strict)
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, definitions: &DefinitionsBuilder<CombinedValidator>) -> PyResult<()> {
        self.arguments_validator.complete(definitions)?;
        match &mut self.return_validator {
            Some(v) => v.complete(definitions),
            None => Ok(()),
        }
    }
}
