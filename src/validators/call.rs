use pyo3::exceptions::PyTypeError;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyString;
use pyo3::types::{PyDict, PyTuple};

use crate::errors::ValResult;
use crate::input::Input;

use crate::tools::SchemaDict;

use super::validation_state::ValidationState;
use super::{build_validator, BuildValidator, CombinedValidator, DefinitionsBuilder, Validator};

#[derive(Debug)]
pub struct CallValidator {
    function: PyObject,
    arguments_validator: Box<CombinedValidator>,
    return_validator: Option<Box<CombinedValidator>>,
    name: String,
}

impl BuildValidator for CallValidator {
    const EXPECTED_TYPE: &'static str = "call";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();

        let arguments_schema = schema.get_as_req(intern!(py, "arguments_schema"))?;
        let arguments_validator = Box::new(build_validator(&arguments_schema, config, definitions)?);

        let return_schema = schema.get_item(intern!(py, "return_schema"))?;
        let return_validator = match return_schema {
            Some(return_schema) => Some(Box::new(build_validator(&return_schema, config, definitions)?)),
            None => None,
        };
        let function: Bound<'_, PyAny> = schema.get_as_req(intern!(py, "function"))?;
        let function_name: Py<PyString> = match schema.get_as(intern!(py, "function_name"))? {
            Some(name) => name,
            None => {
                match function.getattr(intern!(py, "__name__")) {
                    Ok(name) => name.extract()?,
                    Err(_) => {
                        // partials we use `function.func.__name__`
                        if let Ok(func) = function.getattr(intern!(py, "func")) {
                            func.getattr(intern!(py, "__name__"))?.extract()?
                        } else {
                            intern!(py, "<unknown>").clone().into()
                        }
                    }
                }
            }
        };
        let function_name = function_name.bind(py);
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

impl_py_gc_traverse!(CallValidator {
    function,
    arguments_validator,
    return_validator
});

impl Validator for CallValidator {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &impl Input<'py>,
        state: &mut ValidationState,
    ) -> ValResult<PyObject> {
        let args = self.arguments_validator.validate(py, input, state)?.into_bound(py);

        let return_value = if let Ok((args, kwargs)) = args.extract::<(Bound<PyTuple>, Bound<PyDict>)>() {
            self.function.call_bound(py, args, Some(&kwargs))?
        } else if let Ok(kwargs) = args.downcast::<PyDict>() {
            self.function.call_bound(py, (), Some(kwargs))?
        } else {
            let msg = "Arguments validator should return a tuple of (args, kwargs) or a dict of kwargs";
            return Err(PyTypeError::new_err(msg).into());
        };

        if let Some(return_validator) = &self.return_validator {
            return_validator
                .validate(py, return_value.bind(py), state)
                .map_err(|e| e.with_outer_location("return"))
        } else {
            Ok(return_value.to_object(py))
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}
