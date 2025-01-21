use std::borrow::Cow;

use pyo3::types::{PyComplex, PyDict};
use pyo3::{prelude::*, IntoPyObjectExt};

use crate::definitions::DefinitionsBuilder;

use super::{infer_serialize, infer_to_python, BuildSerializer, CombinedSerializer, Extra, SerMode, TypeSerializer};

#[derive(Debug, Clone)]
pub struct ComplexSerializer {}

impl BuildSerializer for ComplexSerializer {
    const EXPECTED_TYPE: &'static str = "complex";
    fn build(
        _schema: &Bound<'_, PyDict>,
        _config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        Ok(Self {}.into())
    }
}

impl_py_gc_traverse!(ComplexSerializer {});

impl TypeSerializer for ComplexSerializer {
    fn to_python(
        &self,
        value: &Bound<'_, PyAny>,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        let py = value.py();
        match value.downcast::<PyComplex>() {
            Ok(py_complex) => match extra.mode {
                SerMode::Json => complex_to_str(py_complex).into_py_any(py),
                _ => Ok(value.clone().unbind()),
            },
            Err(_) => {
                extra.warnings.on_fallback_py(self.get_name(), value, extra)?;
                infer_to_python(value, include, exclude, extra)
            }
        }
    }

    fn json_key<'a>(&self, key: &'a Bound<'_, PyAny>, extra: &Extra) -> PyResult<Cow<'a, str>> {
        self.invalid_as_json_key(key, extra, "complex")
    }

    fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        value: &Bound<'_, PyAny>,
        serializer: S,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> Result<S::Ok, S::Error> {
        match value.downcast::<PyComplex>() {
            Ok(py_complex) => {
                let s = complex_to_str(py_complex);
                Ok(serializer.collect_str::<String>(&s)?)
            }
            Err(_) => {
                extra.warnings.on_fallback_ser::<S>(self.get_name(), value, extra)?;
                infer_serialize(value, serializer, include, exclude, extra)
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
