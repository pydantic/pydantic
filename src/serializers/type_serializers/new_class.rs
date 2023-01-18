use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PySet};

use crate::build_context::BuildContext;
use crate::build_tools::SchemaDict;

use super::{py_err_se_err, BuildSerializer, CombinedSerializer, Extra, TypeSerializer};

#[derive(Debug, Clone)]
pub struct NewClassSerializer {
    serializer: Box<CombinedSerializer>,
}

impl BuildSerializer for NewClassSerializer {
    const EXPECTED_TYPE: &'static str = "new-class";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let py = schema.py();
        let sub_schema: &PyDict = schema.get_as_req(intern!(py, "schema"))?;
        let serializer = Box::new(CombinedSerializer::build(sub_schema, config, build_context)?);

        Ok(Self { serializer }.into())
    }
}

impl TypeSerializer for NewClassSerializer {
    fn to_python(
        &self,
        value: &PyAny,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        let dict = object_to_dict(value, true, extra)?;
        self.serializer.to_python(dict, include, exclude, extra)
    }

    fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        value: &PyAny,
        serializer: S,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> Result<S::Ok, S::Error> {
        let dict = object_to_dict(value, true, extra).map_err(py_err_se_err)?;
        self.serializer
            .serde_serialize(dict, serializer, include, exclude, extra)
    }
}

pub(super) fn object_to_dict<'py>(value: &'py PyAny, is_model: bool, extra: &Extra) -> PyResult<&'py PyDict> {
    let py = value.py();
    let attr = value.getattr(intern!(py, "__dict__"))?;
    let attrs: &PyDict = attr.downcast()?;
    if is_model && extra.exclude_unset {
        let fields_set: &PySet = value.getattr(intern!(py, "__fields_set__"))?.downcast()?;

        let new_attrs = attrs.copy()?;
        for key in new_attrs.keys() {
            if !fields_set.contains(key)? {
                new_attrs.del_item(key)?;
            }
        }
        Ok(new_attrs)
    } else {
        Ok(attrs)
    }
}
