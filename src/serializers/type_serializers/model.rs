use std::borrow::Cow;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyType};

use crate::build_context::BuildContext;
use crate::build_tools::SchemaDict;
use crate::serializers::extra::SerCheck;
use crate::serializers::infer::{infer_serialize, infer_to_python};
use crate::serializers::ob_type::ObType;

use super::{
    infer_json_key, infer_json_key_known, object_to_dict, py_err_se_err, BuildSerializer, CombinedSerializer, Extra,
    TypeSerializer,
};

#[derive(Debug, Clone)]
pub struct ModelSerializer {
    class: Py<PyType>,
    serializer: Box<CombinedSerializer>,
    name: String,
}

impl BuildSerializer for ModelSerializer {
    const EXPECTED_TYPE: &'static str = "model";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let py = schema.py();
        let class: &PyType = schema.get_as_req(intern!(py, "cls"))?;
        let sub_schema: &PyDict = schema.get_as_req(intern!(py, "schema"))?;
        let serializer = Box::new(CombinedSerializer::build(sub_schema, config, build_context)?);

        Ok(Self {
            class: class.into(),
            serializer,
            name: class.getattr(intern!(py, "__name__"))?.extract()?,
        }
        .into())
    }
}

impl ModelSerializer {
    fn allow_value(&self, value: &PyAny, extra: &Extra) -> PyResult<bool> {
        match extra.check {
            SerCheck::Strict => value.get_type().eq(self.class.as_ref(value.py())),
            SerCheck::Lax => value.is_instance(self.class.as_ref(value.py())),
            SerCheck::None => value.hasattr(intern!(value.py(), "__dict__")),
        }
    }
}

impl TypeSerializer for ModelSerializer {
    fn to_python(
        &self,
        value: &PyAny,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        if self.allow_value(value, extra)? {
            let dict = object_to_dict(value, true, extra)?;
            self.serializer.to_python(dict, include, exclude, extra)
        } else {
            extra.warnings.on_fallback_py(self.get_name(), value, extra)?;
            infer_to_python(value, include, exclude, extra)
        }
    }

    fn json_key<'py>(&self, key: &'py PyAny, extra: &Extra) -> PyResult<Cow<'py, str>> {
        if self.allow_value(key, extra)? {
            infer_json_key_known(&ObType::Model, key, extra)
        } else {
            extra.warnings.on_fallback_py(&self.name, key, extra)?;
            infer_json_key(key, extra)
        }
    }

    fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        value: &PyAny,
        serializer: S,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> Result<S::Ok, S::Error> {
        if self.allow_value(value, extra).map_err(py_err_se_err)? {
            let dict = object_to_dict(value, true, extra).map_err(py_err_se_err)?;
            self.serializer
                .serde_serialize(dict, serializer, include, exclude, extra)
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
