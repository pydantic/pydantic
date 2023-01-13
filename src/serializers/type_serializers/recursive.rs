use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::build_context::BuildContext;
use crate::build_tools::SchemaDict;

use super::{py_err_se_err, BuildSerializer, CombinedSerializer, Extra, TypeSerializer};

#[derive(Debug, Clone)]
pub struct RecursiveRefSerializer {
    serializer_id: usize,
}

impl RecursiveRefSerializer {
    pub fn from_id(serializer_id: usize) -> CombinedSerializer {
        Self { serializer_id }.into()
    }
}

impl BuildSerializer for RecursiveRefSerializer {
    const EXPECTED_TYPE: &'static str = "recursive-ref";

    fn build(
        schema: &PyDict,
        _config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let name: String = schema.get_as_req(intern!(schema.py(), "schema_ref"))?;
        let (serializer_id, _) = build_context.find_slot_id_answer(&name)?;
        Ok(Self { serializer_id }.into())
    }
}

impl TypeSerializer for RecursiveRefSerializer {
    fn to_python(
        &self,
        value: &PyAny,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> PyResult<PyObject> {
        let value_id = extra.rec_guard.add(value)?;
        let comb_serializer = unsafe { extra.slots.get_unchecked(self.serializer_id) };
        let r = comb_serializer.to_python(value, include, exclude, extra);
        extra.rec_guard.pop(value_id);
        r
    }

    fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        value: &PyAny,
        serializer: S,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> Result<S::Ok, S::Error> {
        let value_id = extra.rec_guard.add(value).map_err(py_err_se_err)?;
        let comb_serializer = unsafe { extra.slots.get_unchecked(self.serializer_id) };
        let r = comb_serializer.serde_serialize(value, serializer, include, exclude, extra);
        extra.rec_guard.pop(value_id);
        r
    }
}
