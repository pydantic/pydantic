use std::sync::{Arc, OnceLock};

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use crate::common::deque::get_deque_type;
use crate::errors::ValResult;
use crate::input::{Input, ValidatedList};
use crate::tools::SchemaDict;

use super::list::{ToVec, ValidateToVec, get_items_schema, min_length_check};
use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

#[derive(Debug)]
pub struct DequeValidator {
    strict: bool,
    item_validator: Option<Arc<CombinedValidator>>,
    min_length: Option<usize>,
    max_length: Option<usize>,
    name: OnceLock<String>,
    fail_fast: bool,
}

impl BuildValidator for DequeValidator {
    const EXPECTED_TYPE: &'static str = "deque";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedValidator>>,
    ) -> PyResult<Arc<CombinedValidator>> {
        let py = schema.py();
        let item_validator = get_items_schema(schema, config, definitions)?;
        Ok(CombinedValidator::Deque(Self {
            strict: crate::build_tools::is_strict(schema, config)?,
            item_validator,
            min_length: schema.get_as(intern!(py, "min_length"))?,
            max_length: schema.get_as(intern!(py, "max_length"))?,
            name: OnceLock::new(),
            fail_fast: schema.get_as(intern!(py, "fail_fast"))?.unwrap_or(false),
        })
        .into())
    }
}

impl_py_gc_traverse!(DequeValidator { item_validator });

impl Validator for DequeValidator {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Py<PyAny>> {
        let (seq, maxlen) = input.validate_deque(state.strict_or(self.strict))?.unpack(state);

        let actual_length = seq.len();
        let output = match self.item_validator {
            Some(ref v) => seq.iterate(ValidateToVec {
                py,
                input,
                actual_length,
                max_length: self.max_length,
                field_type: "Deque",
                item_validator: v,
                state,
                fail_fast: self.fail_fast,
            })??,
            None => seq.iterate(ToVec {
                py,
                input,
                actual_length,
                max_length: self.max_length,
                field_type: "Deque",
            })??,
        };
        min_length_check!(input, "Deque", self.min_length, output);

        let deque_type = get_deque_type(py)?;
        let items = PyList::new(py, output)?;
        let deque = match maxlen {
            // `maxlen` is preserved from the input deque (if any). The validated output can't have
            // more items than the input, so the deque constructor will never truncate `items` here.
            Some(maxlen) => {
                let kwargs = PyDict::new(py);
                kwargs.set_item(intern!(py, "maxlen"), maxlen)?;
                deque_type.call((items,), Some(&kwargs))?
            }
            None => deque_type.call1((items,))?,
        };
        Ok(deque.unbind())
    }

    fn get_name(&self) -> &str {
        // same logic as `ListValidator::get_name()`
        match self.name.get() {
            Some(s) => s.as_str(),
            None => {
                let name = self.item_validator.as_ref().map_or("any", |v| v.get_name());
                if name == "..." {
                    // when inner name is not initialized yet, don't cache it here
                    "deque[...]"
                } else {
                    self.name.get_or_init(|| format!("deque[{name}]")).as_str()
                }
            }
        }
    }
}
