use std::borrow::Cow;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PySet, PyString, PyType};

use ahash::AHashMap;

use super::{
    infer_json_key, infer_json_key_known, infer_serialize, infer_to_python, py_err_se_err, BuildSerializer,
    CombinedSerializer, ComputedFields, Extra, FieldsMode, GeneralFieldsSerializer, ObType, SerCheck, SerField,
    TypeSerializer,
};
use crate::build_tools::py_schema_err;
use crate::build_tools::{py_schema_error_type, ExtraBehavior};
use crate::definitions::DefinitionsBuilder;
use crate::serializers::errors::PydanticSerializationUnexpectedValue;
use crate::serializers::extra::DuckTypingSerMode;
use crate::tools::SchemaDict;

const ROOT_FIELD: &str = "root";

pub struct ModelFieldsBuilder;

impl BuildSerializer for ModelFieldsBuilder {
    const EXPECTED_TYPE: &'static str = "model-fields";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let py = schema.py();

        let fields_mode = match has_extra(schema, config)? {
            true => FieldsMode::ModelExtra,
            false => FieldsMode::SimpleDict,
        };

        let fields_dict: Bound<'_, PyDict> = schema.get_as_req(intern!(py, "fields"))?;
        let mut fields: AHashMap<String, SerField> = AHashMap::with_capacity(fields_dict.len());

        let extra_serializer = match (schema.get_item(intern!(py, "extras_schema"))?, &fields_mode) {
            (Some(v), FieldsMode::ModelExtra) => Some(CombinedSerializer::build(&v.extract()?, config, definitions)?),
            (Some(_), _) => return py_schema_err!("extras_schema can only be used if extra_behavior=allow"),
            (_, _) => None,
        };

        for (key, value) in fields_dict {
            let key_py = key.downcast_into::<PyString>()?;
            let key: String = key_py.extract()?;
            let field_info = value.downcast()?;

            let key_py: Py<PyString> = key_py.into();

            if field_info.get_as(intern!(py, "serialization_exclude"))? == Some(true) {
                fields.insert(key, SerField::new(py, key_py, None, None, true));
            } else {
                let alias: Option<String> = field_info.get_as(intern!(py, "serialization_alias"))?;

                let schema = field_info.get_as_req(intern!(py, "schema"))?;
                let serializer = CombinedSerializer::build(&schema, config, definitions)
                    .map_err(|e| py_schema_error_type!("Field `{}`:\n  {}", key, e))?;

                fields.insert(key, SerField::new(py, key_py, alias, Some(serializer), true));
            }
        }

        let computed_fields = ComputedFields::new(schema, config, definitions)?;

        Ok(GeneralFieldsSerializer::new(fields, fields_mode, extra_serializer, computed_fields).into())
    }
}

#[derive(Debug)]
pub struct ModelSerializer {
    class: Py<PyType>,
    serializer: Box<CombinedSerializer>,
    has_extra: bool,
    root_model: bool,
    name: String,
}

impl BuildSerializer for ModelSerializer {
    const EXPECTED_TYPE: &'static str = "model";

    fn build(
        schema: &Bound<'_, PyDict>,
        _config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let py = schema.py();

        // models ignore the parent config and always use the config from this model
        let config = schema.get_as(intern!(py, "config"))?;

        let class: Py<PyType> = schema.get_as_req(intern!(py, "cls"))?;
        let sub_schema = schema.get_as_req(intern!(py, "schema"))?;
        let serializer = Box::new(CombinedSerializer::build(&sub_schema, config.as_ref(), definitions)?);
        let root_model = schema.get_as(intern!(py, "root_model"))?.unwrap_or(false);
        let name = class.bind(py).getattr(intern!(py, "__name__"))?.extract()?;

        Ok(Self {
            class,
            serializer,
            has_extra: has_extra(schema, config.as_ref())?,
            root_model,
            name,
        }
        .into())
    }
}

fn has_extra(schema: &Bound<'_, PyDict>, config: Option<&Bound<'_, PyDict>>) -> PyResult<bool> {
    let py = schema.py();
    let extra_behaviour = ExtraBehavior::from_schema_or_config(py, schema, config, ExtraBehavior::Ignore)?;
    Ok(matches!(extra_behaviour, ExtraBehavior::Allow))
}

impl ModelSerializer {
    fn allow_value(&self, value: &Bound<'_, PyAny>, extra: &Extra) -> PyResult<bool> {
        let class = self.class.bind(value.py());
        match extra.check {
            SerCheck::Strict => Ok(value.get_type().is(class)),
            SerCheck::Lax => value.is_instance(class),
            SerCheck::None => value.hasattr(intern!(value.py(), "__dict__")),
        }
    }

    fn get_inner_value<'py>(&self, model: &Bound<'py, PyAny>, extra: &Extra) -> PyResult<Bound<'py, PyAny>> {
        let py = model.py();
        let mut attrs = model.getattr(intern!(py, "__dict__"))?.downcast_into::<PyDict>()?;

        if extra.exclude_unset {
            let fields_set = model
                .getattr(intern!(py, "__pydantic_fields_set__"))?
                .downcast_into::<PySet>()?;

            let new_attrs = attrs.copy()?;
            for key in new_attrs.keys() {
                if !fields_set.contains(&key)? {
                    new_attrs.del_item(key)?;
                }
            }
            attrs = new_attrs;
        }

        if self.has_extra {
            let model_extra = model.getattr(intern!(py, "__pydantic_extra__"))?;
            let py_tuple = (attrs, model_extra).to_object(py).into_bound(py);
            Ok(py_tuple)
        } else {
            Ok(attrs.into_any())
        }
    }
}

impl_py_gc_traverse!(ModelSerializer { class, serializer });

impl TypeSerializer for ModelSerializer {
    fn to_python(
        &self,
        value: &Bound<'_, PyAny>,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        let model = Some(value);
        let duck_typing_ser_mode = extra.duck_typing_ser_mode.next_mode();
        let model_extra = Extra {
            model,
            field_name: None,
            duck_typing_ser_mode,
            ..*extra
        };
        if model_extra.duck_typing_ser_mode == DuckTypingSerMode::Inferred {
            return infer_to_python(value, include, exclude, &model_extra);
        }
        if self.root_model {
            let field_name = Some(ROOT_FIELD);
            let root_extra = Extra {
                field_name,
                ..model_extra
            };
            let py = value.py();
            let root = value.getattr(intern!(py, ROOT_FIELD)).map_err(|original_err| {
                if root_extra.check.enabled() {
                    PydanticSerializationUnexpectedValue::new_err(None)
                } else {
                    original_err
                }
            })?;
            self.serializer.to_python(&root, include, exclude, &root_extra)
        } else if self.allow_value(value, &model_extra)? {
            let inner_value = self.get_inner_value(value, &model_extra)?;
            self.serializer.to_python(&inner_value, include, exclude, &model_extra)
        } else {
            extra.warnings.on_fallback_py(self.get_name(), value, &model_extra)?;
            infer_to_python(value, include, exclude, &model_extra)
        }
    }

    fn json_key<'a>(&self, key: &'a Bound<'_, PyAny>, extra: &Extra) -> PyResult<Cow<'a, str>> {
        if self.allow_value(key, extra)? {
            infer_json_key_known(ObType::PydanticSerializable, key, extra)
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
        let duck_typing_ser_mode = extra.duck_typing_ser_mode.next_mode();
        let model_extra = Extra {
            model,
            field_name: None,
            duck_typing_ser_mode,
            ..*extra
        };
        if model_extra.duck_typing_ser_mode == DuckTypingSerMode::Inferred {
            return infer_serialize(value, serializer, include, exclude, &model_extra);
        }
        if self.root_model {
            let field_name = Some(ROOT_FIELD);
            let root_extra = Extra {
                field_name,
                ..model_extra
            };
            let py = value.py();
            let root = value.getattr(intern!(py, ROOT_FIELD)).map_err(py_err_se_err)?;
            self.serializer
                .serde_serialize(&root, serializer, include, exclude, &root_extra)
        } else if self.allow_value(value, &model_extra).map_err(py_err_se_err)? {
            let inner_value = self.get_inner_value(value, &model_extra).map_err(py_err_se_err)?;
            self.serializer
                .serde_serialize(&inner_value, serializer, include, exclude, &model_extra)
        } else {
            extra
                .warnings
                .on_fallback_ser::<S>(self.get_name(), value, &model_extra)?;
            infer_serialize(value, serializer, include, exclude, &model_extra)
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn retry_with_lax_check(&self) -> bool {
        true
    }
}
