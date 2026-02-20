use std::borrow::Cow;
use std::sync::Arc;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::pybacked::PyBackedStr;
use pyo3::types::{PyDict, PySet, PyType};

use ahash::AHashMap;
use pyo3::IntoPyObjectExt;

use super::{
    BuildSerializer, CombinedSerializer, ComputedFields, Extra, FieldsMode, GeneralFieldsSerializer, ObType, SerCheck,
    SerField, TypeSerializer, infer_json_key, infer_json_key_known,
};
use crate::build_tools::py_schema_err;
use crate::build_tools::{ExtraBehavior, py_schema_error_type};
use crate::definitions::DefinitionsBuilder;
use crate::serializers::SerializationState;
use crate::serializers::shared::DoSerialize;
use crate::serializers::shared::serialize_to_json;
use crate::serializers::shared::serialize_to_python;
use crate::serializers::type_serializers::any::AnySerializer;
use crate::serializers::type_serializers::function::FunctionPlainSerializer;
use crate::serializers::type_serializers::function::FunctionWrapSerializer;
use crate::tools::SchemaDict;
use crate::tools::root_field_py_str;

pub struct ModelFieldsBuilder;

impl BuildSerializer for ModelFieldsBuilder {
    const EXPECTED_TYPE: &'static str = "model-fields";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        let py = schema.py();

        let fields_mode = match has_extra(schema, config)? {
            true => FieldsMode::ModelExtra,
            false => FieldsMode::SimpleDict,
        };

        let fields_dict: Bound<'_, PyDict> = schema.get_as_req(intern!(py, "fields"))?;
        let mut fields = AHashMap::with_capacity(fields_dict.len());

        let extra_serializer = match (schema.get_item(intern!(py, "extras_schema"))?, &fields_mode) {
            (Some(v), FieldsMode::ModelExtra) => Some(CombinedSerializer::build(&v.extract()?, config, definitions)?),
            (Some(_), _) => return py_schema_err!("extras_schema can only be used if extra_behavior=allow"),
            (_, _) => None,
        };

        let serialize_by_alias = config.get_as(intern!(py, "serialize_by_alias"))?;

        for (key, value) in fields_dict {
            let key: PyBackedStr = key.extract()?;
            let field_info = value.cast()?;

            if field_info.get_as(intern!(py, "serialization_exclude"))? == Some(true) {
                fields.insert(
                    key.clone_ref(py),
                    SerField::new(key, None, None, true, serialize_by_alias, None),
                );
            } else {
                let alias = field_info.get_as(intern!(py, "serialization_alias"))?;
                let serialization_exclude_if: Option<Py<PyAny>> =
                    field_info.get_as(intern!(py, "serialization_exclude_if"))?;
                let schema = field_info.get_as_req(intern!(py, "schema"))?;
                let serializer = CombinedSerializer::build(&schema, config, definitions)
                    .map_err(|e| py_schema_error_type!("Field `{key}`:\n  {e}"))?;

                fields.insert(
                    key.clone_ref(py),
                    SerField::new(
                        key,
                        alias,
                        Some(serializer),
                        true,
                        serialize_by_alias,
                        serialization_exclude_if,
                    ),
                );
            }
        }

        let computed_fields = ComputedFields::new(schema, config, definitions)?;

        Ok(Arc::new(
            GeneralFieldsSerializer::new(fields, fields_mode, extra_serializer, computed_fields).into(),
        ))
    }
}

#[derive(Debug)]
pub struct ModelSerializer {
    class: Py<PyType>,
    serializer: Arc<CombinedSerializer>,
    has_extra: bool,
    root_model: bool,
    name: String,
}

impl BuildSerializer for ModelSerializer {
    const EXPECTED_TYPE: &'static str = "model";

    fn build(
        schema: &Bound<'_, PyDict>,
        _config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        let py = schema.py();

        // models ignore the parent config and always use the config from this model
        let config = schema.get_as(intern!(py, "config"))?;

        let class: Py<PyType> = schema.get_as_req(intern!(py, "cls"))?;
        let sub_schema = schema.get_as_req(intern!(py, "schema"))?;
        let serializer = CombinedSerializer::build(&sub_schema, config.as_ref(), definitions)?;
        let root_model = schema.get_as(intern!(py, "root_model"))?.unwrap_or(false);
        let name = class.bind(py).getattr(intern!(py, "__name__"))?.extract()?;

        Ok(CombinedSerializer::Model(Self {
            class,
            serializer,
            has_extra: has_extra(schema, config.as_ref())?,
            root_model,
            name,
        })
        .into())
    }
}

fn has_extra(schema: &Bound<'_, PyDict>, config: Option<&Bound<'_, PyDict>>) -> PyResult<bool> {
    let py = schema.py();
    let extra_behaviour = ExtraBehavior::from_schema_or_config(py, schema, config, ExtraBehavior::Ignore)?;
    Ok(matches!(extra_behaviour, ExtraBehavior::Allow))
}

impl ModelSerializer {
    fn allow_value(&self, value: &Bound<'_, PyAny>, check: SerCheck) -> PyResult<bool> {
        match check {
            SerCheck::Strict => Ok(value.get_type().is(&self.class)),
            SerCheck::Lax => value.is_instance(self.class.bind(value.py())),
            SerCheck::None => value.hasattr(intern!(value.py(), "__dict__")),
        }
    }

    fn allow_value_root_model(&self, value: &Bound<'_, PyAny>, check: SerCheck) -> PyResult<bool> {
        match check {
            SerCheck::Strict => Ok(value.get_type().is(&self.class)),
            SerCheck::Lax | SerCheck::None => value.is_instance(self.class.bind(value.py())),
        }
    }

    /// Performs serialization for the model. This handles
    /// - compatibility checks
    /// - extracting the inner value for root models
    /// - applying `serialize_as_any` where needed
    fn serialize<'py, S: DoSerialize>(
        &self,
        value: &Bound<'py, PyAny>,
        state: &mut SerializationState<'py>,
        do_serialize: S,
    ) -> Result<S::Ok, S::Error> {
        if self.root_model {
            return self.serialize_root_model(value, state, do_serialize);
        }

        if !self.allow_value(value, state.check)? {
            return do_serialize.serialize_fallback(self.get_name(), value, state);
        }

        let inner_value = self.get_inner_value(value, &state.extra)?;

        let state = &mut state.scoped_set(|s| &mut s.model, Some(value.clone()));
        do_serialize.serialize_no_infer(&self.serializer, &inner_value, state)
    }

    fn serialize_root_model<'py, S: DoSerialize>(
        &self,
        value: &Bound<'py, PyAny>,
        state: &mut SerializationState<'py>,
        do_serialize: S,
    ) -> Result<S::Ok, S::Error> {
        if !self.allow_value_root_model(value, state.check)? {
            return do_serialize.serialize_fallback(self.get_name(), value, state);
        }

        let root_field = root_field_py_str(value.py());
        let root = value.getattr(root_field)?;

        // for root models, `serialize_as_any` may apply unless a `field_serializer` is used
        let serializer = if state.extra.serialize_as_any
            && !matches!(
                self.serializer.as_ref(),
                CombinedSerializer::Function(FunctionPlainSerializer {
                    is_field_serializer: true,
                    ..
                }) | CombinedSerializer::FunctionWrap(FunctionWrapSerializer {
                    is_field_serializer: true,
                    ..
                }),
            ) {
            AnySerializer::get()
        } else {
            &self.serializer
        };

        let state = &mut state.scoped_set_field_name(Some(root_field.clone()));
        let state = &mut state.scoped_set(|s| &mut s.model, Some(value.clone()));
        do_serialize.serialize_no_infer(serializer, &root, state)
    }

    fn get_inner_value<'py>(&self, model: &Bound<'py, PyAny>, extra: &Extra) -> PyResult<Bound<'py, PyAny>> {
        let py: Python<'_> = model.py();
        let mut attrs = model.getattr(intern!(py, "__dict__"))?.cast_into::<PyDict>()?;

        if extra.exclude_unset {
            let fields_set = model
                .getattr(intern!(py, "__pydantic_fields_set__"))?
                .cast_into::<PySet>()?;

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
            (attrs, model_extra).into_bound_py_any(py)
        } else {
            Ok(attrs.into_any())
        }
    }
}

impl_py_gc_traverse!(ModelSerializer { class, serializer });

impl TypeSerializer for ModelSerializer {
    fn to_python<'py>(&self, value: &Bound<'py, PyAny>, state: &mut SerializationState<'py>) -> PyResult<Py<PyAny>> {
        self.serialize(value, state, serialize_to_python(value.py()))
    }

    fn json_key<'a, 'py>(
        &self,
        key: &'a Bound<'py, PyAny>,
        state: &mut SerializationState<'py>,
    ) -> PyResult<Cow<'a, str>> {
        // FIXME: root model in json key position should serialize as inner value?
        if self.allow_value(key, state.check)? {
            infer_json_key_known(ObType::PydanticSerializable, key, state)
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
        self.serialize(value, state, serialize_to_json(serializer))
            .map_err(|e| e.0)
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn retry_with_lax_check(&self) -> bool {
        true
    }
}
