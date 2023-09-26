use std::fmt;

use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::errors::{ErrorType, LocItem, ValError, ValResult};
use crate::input::{GenericIterator, Input};
use crate::recursion_guard::RecursionGuard;
use crate::tools::SchemaDict;
use crate::ValidationError;

use super::list::get_items_schema;
use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, Extra, InputType, ValidationState, Validator};

#[derive(Debug, Clone)]
pub struct GeneratorValidator {
    item_validator: Option<Box<CombinedValidator>>,
    min_length: Option<usize>,
    max_length: Option<usize>,
    name: String,
    hide_input_in_errors: bool,
    validation_error_cause: bool,
}

impl BuildValidator for GeneratorValidator {
    const EXPECTED_TYPE: &'static str = "generator";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let item_validator = get_items_schema(schema, config, definitions)?;
        let name = match item_validator {
            Some(ref v) => format!("{}[{}]", Self::EXPECTED_TYPE, v.get_name()),
            None => format!("{}[any]", Self::EXPECTED_TYPE),
        };
        let hide_input_in_errors: bool = config
            .get_as(pyo3::intern!(schema.py(), "hide_input_in_errors"))?
            .unwrap_or(false);
        let validation_error_cause: bool = config
            .get_as(pyo3::intern!(schema.py(), "validation_error_cause"))?
            .unwrap_or(false);
        Ok(Self {
            item_validator,
            name,
            min_length: schema.get_as(pyo3::intern!(schema.py(), "min_length"))?,
            max_length: schema.get_as(pyo3::intern!(schema.py(), "max_length"))?,
            hide_input_in_errors,
            validation_error_cause,
        }
        .into())
    }
}

impl_py_gc_traverse!(GeneratorValidator { item_validator });

impl Validator for GeneratorValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        let iterator = input.validate_iter()?;
        let validator = self.item_validator.as_ref().map(|v| {
            InternalValidator::new(
                py,
                "ValidatorIterator",
                v,
                state,
                self.hide_input_in_errors,
                self.validation_error_cause,
            )
        });

        let v_iterator = ValidatorIterator {
            iterator,
            validator,
            min_length: self.min_length,
            max_length: self.max_length,
            hide_input_in_errors: self.hide_input_in_errors,
            validation_error_cause: self.validation_error_cause,
        };
        Ok(v_iterator.into_py(py))
    }

    fn different_strict_behavior(
        &self,
        definitions: Option<&DefinitionsBuilder<CombinedValidator>>,
        ultra_strict: bool,
    ) -> bool {
        if let Some(ref v) = self.item_validator {
            v.different_strict_behavior(definitions, ultra_strict)
        } else {
            false
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, definitions: &DefinitionsBuilder<CombinedValidator>) -> PyResult<()> {
        match self.item_validator {
            Some(ref mut v) => v.complete(definitions),
            None => Ok(()),
        }
    }
}

#[pyclass(module = "pydantic_core._pydantic_core")]
#[derive(Debug, Clone)]
struct ValidatorIterator {
    iterator: GenericIterator,
    validator: Option<InternalValidator>,
    min_length: Option<usize>,
    max_length: Option<usize>,
    hide_input_in_errors: bool,
    validation_error_cause: bool,
}

#[pymethods]
impl ValidatorIterator {
    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__(mut slf: PyRefMut<'_, Self>, py: Python) -> PyResult<Option<PyObject>> {
        let min_length = slf.min_length;
        let max_length = slf.max_length;
        let hide_input_in_errors = slf.hide_input_in_errors;
        let validation_error_cause = slf.validation_error_cause;
        let Self {
            validator, iterator, ..
        } = &mut *slf;
        macro_rules! next {
            ($iter:ident) => {
                match $iter.next(py)? {
                    Some((next, index)) => match validator {
                        Some(validator) => {
                            if let Some(max_length) = max_length {
                                if index >= max_length {
                                    let val_error = ValError::new_custom_input(
                                        ErrorType::TooLong {
                                            field_type: "Generator".to_string(),
                                            max_length,
                                            actual_length: None,
                                            context: None,
                                        },
                                        $iter.input_as_error_value(py),
                                    );
                                    return Err(ValidationError::from_val_error(
                                        py,
                                        "ValidatorIterator".to_object(py),
                                        InputType::Python,
                                        val_error,
                                        None,
                                        hide_input_in_errors,
                                        validation_error_cause,
                                    ));
                                }
                            }
                            validator.validate(py, next, Some(index.into())).map(Some)
                        }
                        None => Ok(Some(next.to_object(py))),
                    },
                    None => {
                        if let Some(min_length) = min_length {
                            if $iter.index() < min_length {
                                let val_error = ValError::new_custom_input(
                                    ErrorType::TooShort {
                                        field_type: "Generator".to_string(),
                                        min_length,
                                        actual_length: $iter.index(),
                                        context: None,
                                    },
                                    $iter.input_as_error_value(py),
                                );
                                return Err(ValidationError::from_val_error(
                                    py,
                                    "ValidatorIterator".to_object(py),
                                    InputType::Python,
                                    val_error,
                                    None,
                                    hide_input_in_errors,
                                    validation_error_cause,
                                ));
                            }
                        }
                        Ok(None)
                    }
                }
            };
        }

        match iterator {
            GenericIterator::PyIterator(ref mut iter) => next!(iter),
            GenericIterator::JsonArray(ref mut iter) => next!(iter),
        }
    }

    #[getter]
    fn index(&self) -> usize {
        match self.iterator {
            GenericIterator::PyIterator(ref iter) => iter.index(),
            GenericIterator::JsonArray(ref iter) => iter.index(),
        }
    }

    fn __repr__(&self) -> String {
        format!("ValidatorIterator(index={}, schema={:?})", self.index(), self.validator)
    }

    fn __str__(&self) -> String {
        self.__repr__()
    }
}

/// Cloneable validator wrapper for use in generators in functions, this can be passed back to python
/// mid-validation
#[derive(Clone)]
pub struct InternalValidator {
    name: String,
    validator: CombinedValidator,
    definitions: Vec<CombinedValidator>,
    // TODO, do we need data?
    data: Option<Py<PyDict>>,
    strict: Option<bool>,
    from_attributes: Option<bool>,
    context: Option<PyObject>,
    self_instance: Option<PyObject>,
    recursion_guard: RecursionGuard,
    validation_mode: InputType,
    hide_input_in_errors: bool,
    validation_error_cause: bool,
}

impl fmt::Debug for InternalValidator {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{:?}", self.validator)
    }
}

impl InternalValidator {
    pub fn new(
        py: Python,
        name: &str,
        validator: &CombinedValidator,
        state: &ValidationState,
        hide_input_in_errors: bool,
        validation_error_cause: bool,
    ) -> Self {
        let extra = state.extra();
        Self {
            name: name.to_string(),
            validator: validator.clone(),
            definitions: state.definitions.to_vec(),
            data: extra.data.map(|d| d.into_py(py)),
            strict: extra.strict,
            from_attributes: extra.from_attributes,
            context: extra.context.map(|d| d.into_py(py)),
            self_instance: extra.self_instance.map(|d| d.into_py(py)),
            recursion_guard: state.recursion_guard.clone(),
            validation_mode: extra.input_type,
            hide_input_in_errors,
            validation_error_cause,
        }
    }

    pub fn validate_assignment<'data>(
        &mut self,
        py: Python<'data>,
        model: &'data PyAny,
        field_name: &'data str,
        field_value: &'data PyAny,
        outer_location: Option<LocItem>,
    ) -> PyResult<PyObject> {
        let extra = Extra {
            input_type: self.validation_mode,
            data: self.data.as_ref().map(|data| data.as_ref(py)),
            strict: self.strict,
            ultra_strict: false,
            from_attributes: self.from_attributes,
            context: self.context.as_ref().map(|data| data.as_ref(py)),
            self_instance: self.self_instance.as_ref().map(|data| data.as_ref(py)),
        };
        let mut state = ValidationState::new(extra, &self.definitions, &mut self.recursion_guard);
        self.validator
            .validate_assignment(py, model, field_name, field_value, &mut state)
            .map_err(|e| {
                ValidationError::from_val_error(
                    py,
                    self.name.to_object(py),
                    InputType::Python,
                    e,
                    outer_location,
                    self.hide_input_in_errors,
                    self.validation_error_cause,
                )
            })
    }

    pub fn validate<'data>(
        &mut self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        outer_location: Option<LocItem>,
    ) -> PyResult<PyObject> {
        let extra = Extra {
            input_type: self.validation_mode,
            data: self.data.as_ref().map(|data| data.as_ref(py)),
            strict: self.strict,
            ultra_strict: false,
            from_attributes: self.from_attributes,
            context: self.context.as_ref().map(|data| data.as_ref(py)),
            self_instance: self.self_instance.as_ref().map(|data| data.as_ref(py)),
        };
        let mut state = ValidationState::new(extra, &self.definitions, &mut self.recursion_guard);
        self.validator.validate(py, input, &mut state).map_err(|e| {
            ValidationError::from_val_error(
                py,
                self.name.to_object(py),
                InputType::Python,
                e,
                outer_location,
                self.hide_input_in_errors,
                self.validation_error_cause,
            )
        })
    }
}

impl_py_gc_traverse!(InternalValidator {
    validator,
    definitions,
    data,
    context,
    self_instance
});
