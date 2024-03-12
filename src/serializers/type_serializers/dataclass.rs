use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyString, PyType};
use std::borrow::Cow;

use ahash::AHashMap;
use serde::ser::SerializeMap;

use crate::build_tools::{py_schema_error_type, ExtraBehavior};
use crate::definitions::DefinitionsBuilder;
use crate::tools::SchemaDict;

use super::{
    infer_json_key, infer_json_key_known, infer_serialize, infer_to_python, py_err_se_err, BuildSerializer,
    CombinedSerializer, ComputedFields, Extra, FieldsMode, GeneralFieldsSerializer, ObType, SerCheck, SerField,
    TypeSerializer,
};

pub struct DataclassArgsBuilder;

impl BuildSerializer for DataclassArgsBuilder {
    const EXPECTED_TYPE: &'static str = "dataclass-args";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let py = schema.py();

        let fields_list: Bound<'_, PyList> = schema.get_as_req(intern!(py, "fields"))?;
        let mut fields: AHashMap<String, SerField> = AHashMap::with_capacity(fields_list.len());

        let fields_mode = match ExtraBehavior::from_schema_or_config(py, schema, config, ExtraBehavior::Ignore)? {
            ExtraBehavior::Allow => FieldsMode::TypedDictAllow,
            _ => FieldsMode::SimpleDict,
        };

        for (index, item) in fields_list.iter().enumerate() {
            let field_info = item.downcast::<PyDict>()?;
            let name: String = field_info.get_as_req(intern!(py, "name"))?;

            let key_py: Py<PyString> = PyString::new_bound(py, &name).into();

            if field_info.get_as(intern!(py, "serialization_exclude"))? == Some(true) {
                fields.insert(name, SerField::new(py, key_py, None, None, true));
            } else {
                let schema = field_info.get_as_req(intern!(py, "schema"))?;
                let serializer = CombinedSerializer::build(&schema, config, definitions)
                    .map_err(|e| py_schema_error_type!("Field `{}`:\n  {}", index, e))?;

                let alias = field_info.get_as(intern!(py, "serialization_alias"))?;
                fields.insert(name, SerField::new(py, key_py, alias, Some(serializer), true));
            }
        }

        let computed_fields = ComputedFields::new(schema, config, definitions)?;

        Ok(GeneralFieldsSerializer::new(fields, fields_mode, None, computed_fields).into())
    }
}

#[derive(Debug, Clone)]
pub struct DataclassSerializer {
    class: Py<PyType>,
    serializer: Box<CombinedSerializer>,
    fields: Vec<Py<PyString>>,
    name: String,
}

impl BuildSerializer for DataclassSerializer {
    const EXPECTED_TYPE: &'static str = "dataclass";

    fn build(
        schema: &Bound<'_, PyDict>,
        _config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let py = schema.py();

        // models ignore the parent config and always use the config from this model
        let config = schema.get_as(intern!(py, "config"))?;

        let class: &PyType = schema.get_as_req(intern!(py, "cls"))?;
        let sub_schema = schema.get_as_req(intern!(py, "schema"))?;
        let serializer = Box::new(CombinedSerializer::build(&sub_schema, config.as_ref(), definitions)?);

        let fields = schema
            .get_as_req::<&PyList>(intern!(py, "fields"))?
            .iter()
            .map(|s| Ok(s.downcast::<PyString>()?.into_py(py)))
            .collect::<PyResult<Vec<_>>>()?;

        Ok(Self {
            class: class.into(),
            serializer,
            fields,
            name: class.getattr(intern!(py, "__name__"))?.extract()?,
        }
        .into())
    }
}

impl DataclassSerializer {
    fn allow_value(&self, value: &Bound<'_, PyAny>, extra: &Extra) -> PyResult<bool> {
        match extra.check {
            SerCheck::Strict => Ok(value.get_type().is(self.class.bind(value.py()))),
            SerCheck::Lax => value.is_instance(self.class.bind(value.py())),
            SerCheck::None => value.hasattr(intern!(value.py(), "__dataclass_fields__")),
        }
    }

    fn get_inner_value<'py>(&self, value: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyDict>> {
        let py = value.py();
        let dict = PyDict::new_bound(py);

        for field_name in &self.fields {
            let field_name = field_name.bind(py);
            dict.set_item(field_name, value.getattr(field_name)?)?;
        }
        Ok(dict)
    }
}

impl_py_gc_traverse!(DataclassSerializer { class, serializer });

impl TypeSerializer for DataclassSerializer {
    fn to_python(
        &self,
        value: &Bound<'_, PyAny>,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        let dc_extra = Extra {
            model: Some(value),
            ..*extra
        };
        if self.allow_value(value, extra)? {
            let py = value.py();
            if let CombinedSerializer::Fields(ref fields_serializer) = *self.serializer {
                let output_dict = fields_serializer.main_to_python(
                    py,
                    known_dataclass_iter(&self.fields, value),
                    include,
                    exclude,
                    dc_extra,
                )?;

                fields_serializer.add_computed_fields_python(Some(value), &output_dict, include, exclude, extra)?;
                Ok(output_dict.into_py(py))
            } else {
                let inner_value = self.get_inner_value(value)?;
                self.serializer.to_python(&inner_value, include, exclude, &dc_extra)
            }
        } else {
            extra.warnings.on_fallback_py(self.get_name(), value, &dc_extra)?;
            infer_to_python(value, include, exclude, &dc_extra)
        }
    }

    fn json_key<'a>(&self, key: &'a Bound<'_, PyAny>, extra: &Extra) -> PyResult<Cow<'a, str>> {
        if self.allow_value(key, extra)? {
            infer_json_key_known(ObType::Dataclass, key, extra)
        } else {
            extra.warnings.on_fallback_py(&self.name, key, extra)?;
            infer_json_key(key, extra)
        }
    }

    fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        value: &Bound<'_, PyAny>,
        serializer: S,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> Result<S::Ok, S::Error> {
        let model = Some(value);
        let dc_extra = Extra { model, ..*extra };
        if self.allow_value(value, extra).map_err(py_err_se_err)? {
            if let CombinedSerializer::Fields(ref fields_serializer) = *self.serializer {
                let expected_len = self.fields.len() + fields_serializer.computed_field_count();
                let mut map = fields_serializer.main_serde_serialize(
                    known_dataclass_iter(&self.fields, value),
                    expected_len,
                    serializer,
                    include,
                    exclude,
                    dc_extra,
                )?;
                fields_serializer.add_computed_fields_json::<S>(model, &mut map, include, exclude, extra)?;
                map.end()
            } else {
                let inner_value = self.get_inner_value(value).map_err(py_err_se_err)?;
                self.serializer
                    .serde_serialize(&inner_value, serializer, include, exclude, extra)
            }
        } else {
            extra.warnings.on_fallback_ser::<S>(self.get_name(), value, extra)?;
            infer_serialize(value, serializer, include, exclude, extra)
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
