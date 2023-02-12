use std::fmt;

use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_tools::SchemaDict;
use crate::errors::{ErrorType, LocItem, ValError, ValResult};
use crate::input::{GenericIterator, Input};
use crate::questions::Question;
use crate::recursion_guard::RecursionGuard;
use crate::ValidationError;

use super::list::get_items_schema;
use super::{BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct GeneratorValidator {
    item_validator: Option<Box<CombinedValidator>>,
    min_length: Option<usize>,
    max_length: Option<usize>,
    name: String,
}

impl BuildValidator for GeneratorValidator {
    const EXPECTED_TYPE: &'static str = "generator";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let item_validator = get_items_schema(schema, config, build_context)?;
        let name = match item_validator {
            Some(ref v) => format!("{}[{}]", Self::EXPECTED_TYPE, v.get_name()),
            None => format!("{}[any]", Self::EXPECTED_TYPE),
        };
        Ok(Self {
            item_validator,
            name,
            min_length: schema.get_as(pyo3::intern!(schema.py(), "min_length"))?,
            max_length: schema.get_as(pyo3::intern!(schema.py(), "max_length"))?,
        }
        .into())
    }
}

impl Validator for GeneratorValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let iterator = input.validate_iter()?;
        let validator = self
            .item_validator
            .as_ref()
            .map(|v| InternalValidator::new(py, "ValidatorIterator", v, slots, extra, recursion_guard));

        let v_iterator = ValidatorIterator {
            iterator,
            validator,
            min_length: self.min_length,
            max_length: self.max_length,
        };
        Ok(v_iterator.into_py(py))
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn ask(&self, question: &Question) -> bool {
        match self.item_validator {
            Some(ref v) => v.ask(question),
            None => false,
        }
    }

    fn complete(&mut self, build_context: &BuildContext<CombinedValidator>) -> PyResult<()> {
        match self.item_validator {
            Some(ref mut v) => v.complete(build_context),
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
}

#[pymethods]
impl ValidatorIterator {
    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__(mut slf: PyRefMut<'_, Self>, py: Python) -> PyResult<Option<PyObject>> {
        let min_length = slf.min_length;
        let max_length = slf.max_length;
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
                                    let val_error = ValError::new(
                                        ErrorType::TooLong {
                                            field_type: "Generator".to_string(),
                                            max_length,
                                            actual_length: index + 1,
                                        },
                                        $iter.input(py),
                                    );
                                    return Err(ValidationError::from_val_error(
                                        py,
                                        "ValidatorIterator".to_object(py),
                                        val_error,
                                        None,
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
                                let val_error = ValError::new(
                                    ErrorType::TooShort {
                                        field_type: "Generator".to_string(),
                                        min_length,
                                        actual_length: $iter.index(),
                                    },
                                    $iter.input(py),
                                );
                                return Err(ValidationError::from_val_error(
                                    py,
                                    "ValidatorIterator".to_object(py),
                                    val_error,
                                    None,
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
    slots: Vec<CombinedValidator>,
    // TODO, do we need data?
    data: Option<Py<PyDict>>,
    field: Option<String>,
    strict: Option<bool>,
    context: Option<PyObject>,
    recursion_guard: RecursionGuard,
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
        slots: &[CombinedValidator],
        extra: &Extra,
        recursion_guard: &RecursionGuard,
    ) -> Self {
        Self {
            name: name.to_string(),
            validator: validator.clone(),
            slots: slots.to_vec(),
            data: extra.data.map(|d| d.into_py(py)),
            field: extra.field.map(|f| f.to_string()),
            strict: extra.strict,
            context: extra.context.map(|d| d.into_py(py)),
            recursion_guard: recursion_guard.clone(),
        }
    }

    pub fn validate<'s, 'data>(
        &'s mut self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        outer_location: Option<LocItem>,
    ) -> PyResult<PyObject>
    where
        's: 'data,
    {
        let extra = Extra {
            data: self.data.as_ref().map(|data| data.as_ref(py)),
            field: self.field.as_deref(),
            strict: self.strict,
            context: self.context.as_ref().map(|data| data.as_ref(py)),
        };
        self.validator
            .validate(py, input, &extra, &self.slots, &mut self.recursion_guard)
            .map_err(|e| ValidationError::from_val_error(py, self.name.to_object(py), e, outer_location))
    }
}
