use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyString};

use ahash::AHashMap;

use crate::build_tools::{py_error_type, ExtraBehavior, SchemaDict};
use crate::definitions::DefinitionsBuilder;

use super::model::ModelSerializer;
use super::{BuildSerializer, CombinedSerializer, ComputedFields, FieldsMode, GeneralFieldsSerializer, SerField};

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
        let mut fields: AHashMap<String, SerField> = AHashMap::with_capacity(fields_list.len());

        let fields_mode = match ExtraBehavior::from_schema_or_config(py, schema, config, ExtraBehavior::Ignore)? {
            ExtraBehavior::Allow => FieldsMode::TypedDictAllow,
            _ => FieldsMode::SimpleDict,
        };

        for (index, item) in fields_list.iter().enumerate() {
            let field_info: &PyDict = item.downcast()?;
            let name: String = field_info.get_as_req(intern!(py, "name"))?;

            let key_py: Py<PyString> = PyString::intern(py, &name).into_py(py);

            if field_info.get_as(intern!(py, "serialization_exclude"))? == Some(true) {
                fields.insert(name, SerField::new(py, key_py, None, None, true));
            } else {
                let schema = field_info.get_as_req(intern!(py, "schema"))?;
                let serializer = CombinedSerializer::build(schema, config, definitions)
                    .map_err(|e| py_error_type!("Field `{}`:\n  {}", index, e))?;

                let alias = field_info.get_as(intern!(py, "serialization_alias"))?;
                fields.insert(name, SerField::new(py, key_py, alias, Some(serializer), true));
            }
        }

        let computed_fields = ComputedFields::new(schema, config, definitions)?;

        Ok(GeneralFieldsSerializer::new(fields, fields_mode, computed_fields).into())
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
