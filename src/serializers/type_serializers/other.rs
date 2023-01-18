use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use crate::build_context::BuildContext;
use crate::build_tools::SchemaDict;
use crate::serializers::shared::CombinedSerializer;

use super::any::AnySerializer;
use super::BuildSerializer;

pub struct ChainBuilder;

impl BuildSerializer for ChainBuilder {
    const EXPECTED_TYPE: &'static str = "chain";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let last_schema = schema
            .get_as_req::<&PyList>(intern!(schema.py(), "steps"))?
            .iter()
            .last()
            .unwrap()
            .downcast()?;
        CombinedSerializer::build(last_schema, config, build_context)
    }
}

pub struct FunctionBuilder;

impl BuildSerializer for FunctionBuilder {
    const EXPECTED_TYPE: &'static str = "function";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let py = schema.py();
        let mode: &str = schema.get_as_req(intern!(py, "mode"))?;
        // `before` schemas will obviously have type from `schema` since the validator is called second
        // `after` schemas it's less, clear but the default will be the same type, and the user/lib can always
        // override the serializer
        if mode == "before" || mode == "after" {
            let schema = schema.get_as_req(intern!(py, "schema"))?;
            CombinedSerializer::build(schema, config, build_context)
        } else {
            AnySerializer::build(schema, config, build_context)
        }
    }
}

pub struct CustomErrorBuilder;

impl BuildSerializer for CustomErrorBuilder {
    const EXPECTED_TYPE: &'static str = "custom_error";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let sub_schema: &PyDict = schema.get_as_req(intern!(schema.py(), "schema"))?;
        CombinedSerializer::build(sub_schema, config, build_context)
    }
}
