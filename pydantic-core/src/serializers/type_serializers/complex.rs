use std::borrow::Cow;
use std::sync::Arc;

use pyo3::types::{PyComplex, PyDict};
use pyo3::{IntoPyObjectExt, prelude::*};

use crate::build_tools::LazyLock;
use crate::definitions::DefinitionsBuilder;
use crate::serializers::SerializationState;

use super::{BuildSerializer, CombinedSerializer, SerMode, TypeSerializer, infer_serialize, infer_to_python};

#[derive(Debug, Clone)]
pub struct ComplexSerializer {}

static COMPLEX_SERIALIZER: LazyLock<Arc<CombinedSerializer>> = LazyLock::new(|| Arc::new(ComplexSerializer {}.into()));

impl BuildSerializer for ComplexSerializer {
    const EXPECTED_TYPE: &'static str = "complex";
    fn build(
        _schema: &Bound<'_, PyDict>,
        _config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        Ok(COMPLEX_SERIALIZER.clone())
    }
}

impl_py_gc_traverse!(ComplexSerializer {});

impl TypeSerializer for ComplexSerializer {
    fn to_python<'py>(
        &self,
        value: &Bound<'py, PyAny>,
        state: &mut SerializationState<'_, 'py>,
    ) -> PyResult<Py<PyAny>> {
        let py = value.py();
        match value.cast::<PyComplex>() {
            Ok(py_complex) => match state.extra.mode {
                SerMode::Json => complex_to_str(py_complex).into_py_any(py),
                _ => Ok(value.clone().unbind()),
            },
            Err(_) => {
                state.warn_fallback_py(self.get_name(), value)?;
                infer_to_python(value, state)
            }
        }
    }

    fn json_key<'a, 'py>(
        &self,
        key: &'a Bound<'py, PyAny>,
        state: &mut SerializationState<'_, 'py>,
    ) -> PyResult<Cow<'a, str>> {
        self.invalid_as_json_key(key, state, "complex")
    }

    fn serde_serialize<'py, S: serde::ser::Serializer>(
        &self,
        value: &Bound<'py, PyAny>,
        serializer: S,
        state: &mut SerializationState<'_, 'py>,
    ) -> Result<S::Ok, S::Error> {
        match value.cast::<PyComplex>() {
            Ok(py_complex) => {
                let s = complex_to_str(py_complex);
                Ok(serializer.collect_str::<String>(&s)?)
            }
            Err(_) => {
                state.warn_fallback_ser::<S>(self.get_name(), value)?;
                infer_serialize(value, serializer, state)
            }
        }
    }

    fn get_name(&self) -> &'static str {
        "complex"
    }
}

pub fn complex_to_str(py_complex: &Bound<'_, PyComplex>) -> String {
    let re = py_complex.real();
    let im = py_complex.imag();
    let mut s = format!("{im}j");
    if re != 0.0 {
        let mut sign = "";
        if im >= 0.0 {
            sign = "+";
        }
        s = format!("{re}{sign}{s}");
    }
    s
}
