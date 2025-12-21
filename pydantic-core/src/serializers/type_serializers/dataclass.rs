use pyo3::intern;
use pyo3::prelude::*;
use pyo3::pybacked::PyBackedStr;
use pyo3::types::{PyDict, PyList, PyString, PyType};
use std::borrow::Cow;
use std::sync::Arc;

use ahash::AHashMap;

use crate::build_tools::{ExtraBehavior, py_schema_error_type};
use crate::definitions::DefinitionsBuilder;
use crate::serializers::SerializationState;
use crate::serializers::errors::unwrap_ser_error;
use crate::serializers::shared::SerializeMap;
use crate::serializers::shared::serialize_to_json;
use crate::serializers::shared::serialize_to_python;
use crate::tools::SchemaDict;

use super::{
    BuildSerializer, CombinedSerializer, ComputedFields, FieldsMode, GeneralFieldsSerializer, ObType, SerCheck,
    SerField, TypeSerializer, infer_json_key, infer_json_key_known, infer_serialize, infer_to_python, py_err_se_err,
};

pub struct DataclassArgsBuilder;

impl BuildSerializer for DataclassArgsBuilder {
    const EXPECTED_TYPE: &'static str = "dataclass-args";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        let py = schema.py();

        let fields_list: Bound<'_, PyList> = schema.get_as_req(intern!(py, "fields"))?;
        let mut fields: AHashMap<String, SerField> = AHashMap::with_capacity(fields_list.len());

        let fields_mode = match ExtraBehavior::from_schema_or_config(py, schema, config, ExtraBehavior::Ignore)? {
            ExtraBehavior::Allow => FieldsMode::TypedDictAllow,
            _ => FieldsMode::SimpleDict,
        };

        let serialize_by_alias = config.get_as(intern!(py, "serialize_by_alias"))?;

        for (index, item) in fields_list.iter().enumerate() {
            let field_info = item.cast::<PyDict>()?;
            let key_py: PyBackedStr = field_info.get_as_req(intern!(py, "name"))?;
            let name: String = key_py.to_string();

            if !field_info.get_as(intern!(py, "init_only"))?.unwrap_or(false) {
                if field_info.get_as(intern!(py, "serialization_exclude"))? == Some(true) {
                    fields.insert(name, SerField::new(key_py, None, None, true, serialize_by_alias, None));
                } else {
                    let schema = field_info.get_as_req(intern!(py, "schema"))?;
                    let serializer = CombinedSerializer::build(&schema, config, definitions)
                        .map_err(|e| py_schema_error_type!("Field `{index}`:\n  {e}"))?;

                    let alias = field_info.get_as(intern!(py, "serialization_alias"))?;
                    let serialization_exclude_if: Option<Py<PyAny>> =
                        field_info.get_as(intern!(py, "serialization_exclude_if"))?;
                    fields.insert(
                        name,
                        SerField::new(
                            key_py,
                            alias,
                            Some(serializer),
                            true,
                            serialize_by_alias,
                            serialization_exclude_if,
                        ),
                    );
                }
            }
        }
        let computed_fields = ComputedFields::new(schema, config, definitions)?;

        Ok(CombinedSerializer::Fields(GeneralFieldsSerializer::new(fields, fields_mode, None, computed_fields)).into())
    }
}

#[derive(Debug)]
pub struct DataclassSerializer {
    class: Py<PyType>,
    serializer: Arc<CombinedSerializer>,
    fields: Vec<Py<PyString>>,
    name: String,
}

impl BuildSerializer for DataclassSerializer {
    const EXPECTED_TYPE: &'static str = "dataclass";

    fn build(
        schema: &Bound<'_, PyDict>,
        _config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        let py = schema.py();

        // models ignore the parent config and always use the config from this model
        let config = schema.get_as(intern!(py, "config"))?;

        let class: Bound<'_, PyType> = schema.get_as_req(intern!(py, "cls"))?;
        let sub_schema = schema.get_as_req(intern!(py, "schema"))?;
        let serializer = CombinedSerializer::build(&sub_schema, config.as_ref(), definitions)?;

        let fields = schema
            .get_as_req::<Bound<'_, PyList>>(intern!(py, "fields"))?
            .iter()
            .map(|s| Ok(s.cast_into::<PyString>()?.unbind()))
            .collect::<PyResult<Vec<_>>>()?;

        Ok(CombinedSerializer::Dataclass(Self {
            class: class.clone().unbind(),
            serializer,
            fields,
            name: class.getattr(intern!(py, "__name__"))?.extract()?,
        })
        .into())
    }
}

impl DataclassSerializer {
    fn allow_value(&self, value: &Bound<'_, PyAny>, state: &SerializationState<'_>) -> PyResult<bool> {
        match state.check {
            SerCheck::Strict => Ok(value.get_type().is(self.class.bind(value.py()))),
            SerCheck::Lax => value.is_instance(self.class.bind(value.py())),
            SerCheck::None => value.hasattr(intern!(value.py(), "__dataclass_fields__")),
        }
    }

    fn get_inner_value<'py>(&self, value: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyDict>> {
        let py = value.py();
        let dict = PyDict::new(py);

        for field_name in &self.fields {
            let field_name = field_name.bind(py);
            dict.set_item(field_name, value.getattr(field_name)?)?;
        }
        Ok(dict)
    }
}

impl_py_gc_traverse!(DataclassSerializer { class, serializer });

impl TypeSerializer for DataclassSerializer {
    fn to_python<'py>(&self, value: &Bound<'py, PyAny>, state: &mut SerializationState<'py>) -> PyResult<Py<PyAny>> {
        if self.allow_value(value, state)? {
            let model = value;
            let state = &mut state.scoped_set(|s| &mut s.model, Some(value.clone()));
            let py = value.py();
            if let CombinedSerializer::Fields(ref fields_serializer) = *self.serializer {
                let mut map = fields_serializer.serialize_main(
                    py,
                    model,
                    known_dataclass_iter(&self.fields, model),
                    state,
                    serialize_to_python(py),
                )?;

                fields_serializer.add_computed_fields(model, &mut map, state)?;
                Ok(map.into())
            } else {
                let inner_value = self.get_inner_value(value)?;
                self.serializer.to_python(&inner_value, state)
            }
        } else {
            state.warn_fallback_py(self.get_name(), value)?;
            infer_to_python(value, state)
        }
    }

    fn json_key<'a, 'py>(
        &self,
        key: &'a Bound<'py, PyAny>,
        state: &mut SerializationState<'py>,
    ) -> PyResult<Cow<'a, str>> {
        if self.allow_value(key, state)? {
            infer_json_key_known(ObType::Dataclass, key, state)
        } else {
            state.warn_fallback_py(&self.name, key)?;
            infer_json_key(key, state)
        }
    }

    fn serde_serialize<'py, S: serde::ser::Serializer>(
        &self,
        value: &Bound<'py, PyAny>,
        serializer: S,
        state: &mut SerializationState<'py>,
    ) -> Result<S::Ok, S::Error> {
        if self.allow_value(value, state).map_err(py_err_se_err)? {
            let state = &mut state.scoped_set(|s| &mut s.model, Some(value.clone()));
            if let CombinedSerializer::Fields(ref fields_serializer) = *self.serializer {
                let mut map = fields_serializer
                    .serialize_main(
                        value.py(),
                        value,
                        known_dataclass_iter(&self.fields, value),
                        state,
                        serialize_to_json(serializer),
                    )
                    .map_err(unwrap_ser_error)?;
                fields_serializer
                    .add_computed_fields(value, &mut map, state)
                    .map_err(unwrap_ser_error)?;
                map.end().map_err(unwrap_ser_error)
            } else {
                let inner_value = self.get_inner_value(value).map_err(py_err_se_err)?;
                self.serializer.serde_serialize(&inner_value, serializer, state)
            }
        } else {
            state.warn_fallback_ser::<S>(self.get_name(), value)?;
            infer_serialize(value, serializer, state)
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn retry_with_lax_check(&self) -> bool {
        true
    }
}

fn known_dataclass_iter<'a, 'py>(
    fields: &'a [Py<PyString>],
    dataclass: &'a Bound<'py, PyAny>,
) -> impl Iterator<Item = PyResult<(Bound<'py, PyAny>, Bound<'py, PyAny>)>> + 'a
where
    'py: 'a,
{
    let py = dataclass.py();
    fields.iter().map(move |field| {
        let value = dataclass.getattr(field)?;
        Ok((field.bind(py).clone().into_any(), value))
    })
}
