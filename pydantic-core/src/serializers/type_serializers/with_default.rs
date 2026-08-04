use std::borrow::Cow;
use std::sync::Arc;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::definitions::DefinitionsBuilder;
use crate::serializers::SerializationState;
use crate::tools::SchemaDict;
use crate::validators::DefaultType;

use super::{BuildSerializer, CombinedSerializer, TypeSerializer};

#[derive(Debug)]
pub struct WithDefaultSerializer {
    default: DefaultType,
    serializer: Arc<CombinedSerializer>,
}

impl BuildSerializer for WithDefaultSerializer {
    const EXPECTED_TYPE: &'static str = "default";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Arc<CombinedSerializer>> {
        let py = schema.py();
        let default = DefaultType::new(schema)?;

        let sub_schema = schema.get_as_req(intern!(py, "schema"))?;
        let serializer = CombinedSerializer::build(&sub_schema, config, definitions)?;

        // key the default by kind + object identity: the same default object always
        // yields an interchangeable node
        let (default_kind, default_obj) = match &default {
            DefaultType::None => (0u8, 0usize),
            DefaultType::Default(obj) => (1, obj.as_ptr() as usize),
            DefaultType::DefaultFactory(obj, takes_data) => (if *takes_data { 3 } else { 2 }, obj.as_ptr() as usize),
        };
        let make_key = move |child| crate::definitions::InternKey::WithDefault {
            child,
            default_kind,
            default_obj,
            on_error: 0,
            validate_default: false,
        };
        // the node is only data-free (eligible for cross-build sharing) if the default
        // is absent or the immortal `None` singleton — never pin arbitrary user objects
        let data_free_default = match &default {
            DefaultType::None => true,
            DefaultType::Default(obj) => obj.bind(py).is_none(),
            DefaultType::DefaultFactory(..) => false,
        };
        let global_child = if data_free_default {
            crate::serializers::shared::global_child_key(&serializer)
        } else {
            None
        };
        let ptr_key = make_key(crate::definitions::ChildKey::Ptr(Arc::as_ptr(&serializer) as usize));
        let build_node = move || Arc::new(Self { default, serializer }.into());
        match global_child {
            Some(child) => Ok(crate::serializers::shared::get_or_intern_global(
                make_key(child),
                build_node,
            )),
            None => Ok(definitions.get_or_intern(ptr_key, build_node)),
        }
    }
}

impl_py_gc_traverse!(WithDefaultSerializer { default, serializer });

impl TypeSerializer for WithDefaultSerializer {
    fn to_python<'py>(&self, value: &Bound<'py, PyAny>, state: &mut SerializationState<'py>) -> PyResult<Py<PyAny>> {
        self.serializer.to_python(value, state)
    }

    fn json_key<'a, 'py>(
        &self,
        key: &'a Bound<'py, PyAny>,
        state: &mut SerializationState<'py>,
    ) -> PyResult<Cow<'a, str>> {
        self.serializer.json_key(key, state)
    }

    fn serde_serialize<'py, S: serde::ser::Serializer>(
        &self,
        value: &Bound<'py, PyAny>,
        serializer: S,
        state: &mut SerializationState<'py>,
    ) -> Result<S::Ok, S::Error> {
        self.serializer.serde_serialize(value, serializer, state)
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }

    fn retry_with_lax_check(&self) -> bool {
        self.serializer.retry_with_lax_check()
    }

    fn get_default(&self, py: Python) -> PyResult<Option<Py<PyAny>>> {
        if let DefaultType::DefaultFactory(_, _takes_data @ true) = self.default {
            // We currently don't compute the default if the default factory takes
            // the data from other fields.
            Ok(None)
        } else {
            self.default.default_value(
                py, None, // Won't be used.
            )
        }
    }
}
