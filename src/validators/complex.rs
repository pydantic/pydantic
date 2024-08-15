use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::sync::GILOnceCell;
use pyo3::types::{PyComplex, PyDict, PyString, PyType};

use crate::build_tools::is_strict;
use crate::errors::{ErrorTypeDefaults, ToErrorValue, ValError, ValResult};
use crate::input::Input;

use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

static COMPLEX_TYPE: GILOnceCell<Py<PyType>> = GILOnceCell::new();

pub fn get_complex_type(py: Python) -> &Bound<'_, PyType> {
    COMPLEX_TYPE
        .get_or_init(py, || py.get_type_bound::<PyComplex>().into())
        .bind(py)
}

#[derive(Debug)]
pub struct ComplexValidator {
    strict: bool,
}

impl BuildValidator for ComplexValidator {
    const EXPECTED_TYPE: &'static str = "complex";
    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        Ok(Self {
            strict: is_strict(schema, config)?,
        }
        .into())
    }
}

impl_py_gc_traverse!(ComplexValidator {});

impl Validator for ComplexValidator {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<PyObject> {
        let res = input.validate_complex(self.strict, py)?.unpack(state);
        Ok(res.into_py(py))
    }

    fn get_name(&self) -> &str {
        "complex"
    }
}

pub(crate) fn string_to_complex<'py>(
    arg: &Bound<'py, PyString>,
    input: impl ToErrorValue,
) -> ValResult<Bound<'py, PyComplex>> {
    let py = arg.py();
    Ok(get_complex_type(py)
        .call1((arg,))
        .map_err(|err| {
            // Since arg is a string, the only possible error here is ValueError
            // triggered by invalid complex strings and thus only this case is handled.
            if err.is_instance_of::<PyValueError>(py) {
                ValError::new(ErrorTypeDefaults::ComplexStrParsing, input)
            } else {
                ValError::InternalErr(err)
            }
        })?
        .downcast::<PyComplex>()?
        .to_owned())
}
