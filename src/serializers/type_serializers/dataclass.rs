use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyString};

use ahash::AHashMap;

use crate::build_context::BuildContext;
use crate::build_tools::{py_error_type, SchemaDict};
use crate::serializers::filter::SchemaFilter;
use crate::serializers::shared::CombinedSerializer;

use super::model::ModelSerializer;
use super::typed_dict::{TypedDictField, TypedDictSerializer};
use super::BuildSerializer;

pub struct DataclassArgsBuilder;

impl BuildSerializer for DataclassArgsBuilder {
    const EXPECTED_TYPE: &'static str = "dataclass-args";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let py = schema.py();

        let fields_list: &PyList = schema.get_as_req(intern!(py, "fields"))?;
        let mut fields: AHashMap<String, TypedDictField> = AHashMap::with_capacity(fields_list.len());
        let mut exclude: Vec<Py<PyString>> = Vec::with_capacity(fields_list.len());

        for (index, item) in fields_list.iter().enumerate() {
            let field_info: &PyDict = item.downcast()?;
            let name: String = field_info.get_as_req(intern!(py, "name"))?;

            let key_py: Py<PyString> = PyString::intern(py, &name).into_py(py);

            if field_info.get_as(intern!(py, "serialization_exclude"))? == Some(true) {
                exclude.push(key_py.clone_ref(py));
            } else {
                let schema = field_info.get_as_req(intern!(py, "schema"))?;
                let serializer = CombinedSerializer::build(schema, config, build_context)
                    .map_err(|e| py_error_type!("Field `{}`:\n  {}", index, e))?;

                let alias = field_info.get_as(intern!(py, "serialization_alias"))?;
                fields.insert(name, TypedDictField::new(py, key_py, alias, serializer, true));
            }
        }

        let filter = SchemaFilter::from_vec_hash(py, exclude)?;

        Ok(TypedDictSerializer::new(fields, false, filter).into())
    }
}

pub struct DataclassBuilder;

impl BuildSerializer for DataclassBuilder {
    const EXPECTED_TYPE: &'static str = "dataclass";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        ModelSerializer::build(schema, config, build_context)
    }
}
