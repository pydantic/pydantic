use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyString};

use ahash::AHashMap;

use crate::build_tools::{py_error_type, SchemaDict};
use crate::definitions::DefinitionsBuilder;

use super::model::ModelSerializer;
use super::typed_dict::{FieldSerializer, TypedDictSerializer};
use super::{BuildSerializer, CombinedSerializer, ComputedFields};

pub struct DataclassArgsBuilder;

impl BuildSerializer for DataclassArgsBuilder {
    const EXPECTED_TYPE: &'static str = "dataclass-args";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let py = schema.py();

        let fields_list: &PyList = schema.get_as_req(intern!(py, "fields"))?;
        let mut fields: AHashMap<String, FieldSerializer> = AHashMap::with_capacity(fields_list.len());

        for (index, item) in fields_list.iter().enumerate() {
            let field_info: &PyDict = item.downcast()?;
            let name: String = field_info.get_as_req(intern!(py, "name"))?;

            let key_py: Py<PyString> = PyString::intern(py, &name).into_py(py);

            if field_info.get_as(intern!(py, "serialization_exclude"))? == Some(true) {
                fields.insert(name, FieldSerializer::new(py, key_py, None, None, true));
            } else {
                let schema = field_info.get_as_req(intern!(py, "schema"))?;
                let serializer = CombinedSerializer::build(schema, config, definitions)
                    .map_err(|e| py_error_type!("Field `{}`:\n  {}", index, e))?;

                let alias = field_info.get_as(intern!(py, "serialization_alias"))?;
                fields.insert(name, FieldSerializer::new(py, key_py, alias, Some(serializer), true));
            }
        }

        let computed_fields = ComputedFields::new(schema)?;

        Ok(TypedDictSerializer::new(fields, false, computed_fields).into())
    }
}

pub struct DataclassBuilder;

impl BuildSerializer for DataclassBuilder {
    const EXPECTED_TYPE: &'static str = "dataclass";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        ModelSerializer::build(schema, config, definitions)
    }
}
