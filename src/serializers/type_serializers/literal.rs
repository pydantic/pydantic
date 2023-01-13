use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyString};

use crate::build_context::BuildContext;
use crate::build_tools::{py_err, SchemaDict};

use super::any::AnySerializer;
use super::simple::IntSerializer;
use super::string::StrSerializer;
use super::{BuildSerializer, CombinedSerializer};

#[derive(Debug, Clone)]
pub struct LiteralBuildSerializer;

impl BuildSerializer for LiteralBuildSerializer {
    const EXPECTED_TYPE: &'static str = "literal";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let expected: Vec<&PyAny> = schema
            .get_as_req::<&PyList>(intern!(schema.py(), "expected"))?
            .iter()
            .collect();

        if expected.is_empty() {
            py_err!(r#""expected" should have length > 0"#)
        } else if expected.iter().all(|item| item.extract::<i64>().is_ok()) {
            IntSerializer::build(schema, config, build_context)
        } else if expected.iter().all(|item| item.cast_as::<PyString>().is_ok()) {
            StrSerializer::build(schema, config, build_context)
        } else {
            AnySerializer::build(schema, config, build_context)
        }
    }
}
