use std::borrow::Cow;
use std::sync::Arc;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PySet, PyString, PyType};

use ahash::AHashMap;
use pyo3::IntoPyObjectExt;

use super::{
    infer_json_key, infer_json_key_known, infer_serialize, infer_to_python, BuildSerializer, CombinedSerializer,
    ComputedFields, Extra, FieldsMode, GeneralFieldsSerializer, ObType, SerCheck, SerField, TypeSerializer,
    WrappedSerError,
};
use crate::build_tools::py_schema_err;
use crate::build_tools::{py_schema_error_type, ExtraBehavior};
use crate::definitions::DefinitionsBuilder;
use crate::serializers::type_serializers::any::AnySerializer;
use crate::serializers::type_serializers::function::FunctionPlainSerializer;
use crate::serializers::type_serializers::function::FunctionWrapSerializer;
use crate::tools::SchemaDict;

const ROOT_FIELD: &str = "root";

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
        let mut fields: AHashMap<String, SerField> = AHashMap::with_capacity(fields_dict.len());

        let extra_serializer = match (schema.get_item(intern!(py, "extras_schema"))?, &fields_mode) {
            (Some(v), FieldsMode::ModelExtra) => Some(CombinedSerializer::build(&v.extract()?, config, definitions)?),
            (Some(_), _) => return py_schema_err!("extras_schema can only be used if extra_behavior=allow"),
            (_, _) => None,
        };

        let serialize_by_alias = config.get_as(intern!(py, "serialize_by_alias"))?;

        for (key, value) in fields_dict {
            let key_py = key.downcast_into::<PyString>()?;
            let key: String = key_py.extract()?;
            let field_info = value.downcast()?;

            let key_py: Py<PyString> = key_py.into();

            if field_info.get_as(intern!(py, "serialization_exclude"))? == Some(true) {
                fields.insert(
                    key,
                    SerField::new(py, key_py, None, None, true, serialize_by_alias, None),
                );
            } else {
                let alias: Option<String> = field_info.get_as(intern!(py, "serialization_alias"))?;
                let serialization_exclude_if: Option<Py<PyAny>> =
                    field_info.get_as(intern!(py, "serialization_exclude_if"))?;
                let schema = field_info.get_as_req(intern!(py, "schema"))?;
                let serializer = CombinedSerializer::build(&schema, config, definitions)
                    .map_err(|e| py_schema_error_type!("Field `{}`:\n  {}", key, e))?;

                fields.insert(
                    key,
                    SerField::new(
                        py,
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
    ///
    /// `do_serialize` should be a function which performs the actual serialization, and should not
    /// apply any type inference. (`Model` serialization is strongly coupled with its child
    /// serializer, and in the few cases where `serialize_as_any` applies, it is handled here.)
    ///
    /// If the value is not applicable, `do_serialize` will be called with `None` to indicate fallback
    /// behaviour should be used.
    fn serialize<T, E: From<PyErr>>(
        &self,
        value: &Bound<'_, PyAny>,
        extra: &Extra,
        do_serialize: impl FnOnce(Option<(&Arc<CombinedSerializer>, &Bound<'_, PyAny>, &Extra)>) -> Result<T, E>,
    ) -> Result<T, E> {
        match self.root_model {
            true if self.allow_value_root_model(value, extra.check)? => {
                let root_extra = Extra {
                    field_name: Some(ROOT_FIELD),
                    model: Some(value),
                    ..extra.clone()
                };
                let root = value.getattr(intern!(value.py(), ROOT_FIELD))?;

                // for root models, `serialize_as_any` may apply unless a `field_serializer` is used
                let serializer = if root_extra.serialize_as_any
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

                do_serialize(Some((serializer, &root, &root_extra)))
            }
            false if self.allow_value(value, extra.check)? => {
                let model_extra = Extra {
                    model: Some(value),
                    ..extra.clone()
                };
                let inner_value = self.get_inner_value(value, &model_extra)?;
                do_serialize(Some((&self.serializer, &inner_value, &model_extra)))
            }
            _ => do_serialize(None),
        }
    }

    fn get_inner_value<'py>(&self, model: &Bound<'py, PyAny>, extra: &Extra) -> PyResult<Bound<'py, PyAny>> {
        let py: Python<'_> = model.py();
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
            (attrs, model_extra).into_bound_py_any(py)
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
    ) -> PyResult<Py<PyAny>> {
        self.serialize(value, extra, |resolved| match resolved {
            Some((serializer, value, extra)) => serializer.to_python_no_infer(value, include, exclude, extra),
            None => {
                extra.warnings.on_fallback_py(self.get_name(), value, extra)?;
                infer_to_python(value, include, exclude, extra)
            }
        })
    }

    fn json_key<'a>(&self, key: &'a Bound<'_, PyAny>, extra: &Extra) -> PyResult<Cow<'a, str>> {
        // FIXME: root model in json key position should serialize as inner value?
        if self.allow_value(key, extra.check)? {
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
        self.serialize(value, extra, |resolved| match resolved {
            Some((cs, value, extra)) => cs
                .serde_serialize_no_infer(value, serializer, include, exclude, extra)
                .map_err(WrappedSerError),
            None => {
                extra
                    .warnings
                    .on_fallback_ser::<S>(self.get_name(), value, extra)
                    .map_err(WrappedSerError)?;
                infer_serialize(value, serializer, include, exclude, extra).map_err(WrappedSerError)
            }
        })
        .map_err(|e| e.0)
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn retry_with_lax_check(&self) -> bool {
        true
    }
}
