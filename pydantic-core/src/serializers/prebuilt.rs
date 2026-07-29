use std::borrow::Cow;
use std::sync::Arc;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyType};

use crate::SchemaSerializer;
use crate::common::prebuilt::get_prebuilt;
use crate::serializers::SerializationState;
use crate::tools::SchemaDict;

use super::shared::{CombinedSerializer, TypeSerializer};

pub struct PrebuiltSerializer {
    /// Keeps the referenced `SchemaSerializer` alive (and with it, `serializer`). This is also the
    /// only field reported to the garbage collector: the contents of `serializer` are owned (and
    /// traversed) by the `SchemaSerializer`, so they must not be traversed a second time here.
    schema_serializer: Py<SchemaSerializer>,
    /// The polymorphism trampoline around the `model`/`dataclass` serializer of the referenced
    /// class, found by walking the schema serializer's tree from the root (see
    /// `find_class_serializer`).
    serializer: Arc<CombinedSerializer>,
}

#[allow(clippy::missing_fields_in_debug)] // `schema_serializer` is deliberately omitted
impl std::fmt::Debug for PrebuiltSerializer {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        // Note: the delegated serializer is deliberately not expanded: it is owned by another
        // `SchemaSerializer`, and expanding it per reference can result in exponentially large
        // output with highly interconnected models.
        f.debug_struct("PrebuiltSerializer")
            .field("serializer", &self.serializer.get_name())
            .finish()
    }
}

impl PrebuiltSerializer {
    pub fn try_get_from_schema(type_: &str, schema: &Bound<'_, PyDict>) -> PyResult<Option<CombinedSerializer>> {
        get_prebuilt(type_, schema, "__pydantic_serializer__", |py_any| {
            let schema_serializer = py_any.extract::<Py<SchemaSerializer>>()?;

            let class: Bound<'_, PyType> = schema.get_as_req(intern!(schema.py(), "cls"))?;
            let Some(serializer) = find_class_serializer(schema_serializer.get().serializer.clone(), &class) else {
                return Ok(None);
            };

            Ok(Some(
                Self {
                    schema_serializer,
                    serializer,
                }
                .into(),
            ))
        })
    }
}

/// Walk a class's prebuilt serializer tree from the root to the polymorphism trampoline around
/// the class's own `model`/`dataclass` serializer, which is what a schema *referencing* the class
/// compiles by reference rather than inline (the serializer of a `model`/`dataclass` schema is
/// always built wrapped in a trampoline):
///
/// - a recursive class stores its schema in a definition, making the root of its own tree a
///   reference to that definition — resolve it (the class is complete, so the definition is
///   filled);
/// - a `'wrap'` model serializer is applied *around* the `model`/`dataclass` serializer (under
///   the trampoline). A referencing schema embeds the class's full core schema (including the
///   `serialization` key), so the wrap function serializer is compiled inline before the
///   `model`/`dataclass` schema (with the `serialization` key removed) is reached. Delegating to
///   it would apply the wrap function a second time, so strip it, along with the trampoline
///   wrapping it.
///
/// If the walk moves past any of those but does not end at the trampoline around the
/// `model`/`dataclass` serializer of the referenced class itself, the class serializes in some
/// non-standard way (e.g. a custom `__get_pydantic_core_schema__` wrapping the model schema), and
/// `None` is returned so that the referencing schema conservatively compiles the class's schema
/// inline instead. Delegating to anything else (e.g. a bare model serializer) could also skip the
/// polymorphic subclass dispatch that inline compilation would preserve.
///
/// A root that is none of the above (e.g. a `'plain'` model serializer, which — unlike a `'wrap'`
/// one — cannot double-apply, or a hand-built schema whose serializer is a plain function
/// serializer) is delegated to wholesale, preserving the longstanding behavior that
/// `__pydantic_serializer__` stands in for the class wherever it is referenced.
fn find_class_serializer(
    mut target: Arc<CombinedSerializer>,
    class: &Bound<'_, PyType>,
) -> Option<Arc<CombinedSerializer>> {
    let mut walked = false;
    // Bounded to guard against reference cycles, which a hand-built schema can produce.
    for _ in 0..64 {
        target = match target.as_ref() {
            CombinedSerializer::Recursive(definition_ref_serializer) => {
                definition_ref_serializer.resolved_serializer()?
            }
            CombinedSerializer::PolymorphismTrampoline(trampoline) if trampoline.class.bind(class.py()).is(class) => {
                match trampoline.serializer.as_ref() {
                    // The final target: the trampoline around the class's `model`/`dataclass`
                    // serializer.
                    CombinedSerializer::Model(_) | CombinedSerializer::Dataclass(_) => return Some(target.clone()),
                    // Descend through a nested trampoline (the builder can apply the trampoline
                    // twice) or into a `'wrap'` model serializer so that it can be stripped;
                    // a trampoline around anything else (e.g. a `'plain'` model serializer) is
                    // left intact for the wholesale delegation below.
                    CombinedSerializer::PolymorphismTrampoline(_) | CombinedSerializer::FunctionWrap(_) => {
                        trampoline.serializer.clone()
                    }
                    _ if walked => return None,
                    _ => return Some(target.clone()),
                }
            }
            CombinedSerializer::FunctionWrap(function_serializer) => function_serializer.inner_serializer().clone(),
            _ if walked => return None,
            _ => return Some(target.clone()),
        };
        walked = true;
    }
    None
}

impl_py_gc_traverse!(PrebuiltSerializer { schema_serializer });

impl TypeSerializer for PrebuiltSerializer {
    fn to_python<'py>(&self, value: &Bound<'py, PyAny>, state: &mut SerializationState<'py>) -> PyResult<Py<PyAny>> {
        self.serializer.to_python_no_infer(value, state)
    }

    fn json_key<'a, 'py>(
        &self,
        key: &'a Bound<'py, PyAny>,
        state: &mut SerializationState<'py>,
    ) -> PyResult<Cow<'a, str>> {
        self.serializer.json_key_no_infer(key, state)
    }

    fn serde_serialize<'py, S: serde::ser::Serializer>(
        &self,
        value: &Bound<'py, PyAny>,
        serializer: S,
        state: &mut SerializationState<'py>,
    ) -> Result<S::Ok, S::Error> {
        self.serializer.serde_serialize_no_infer(value, serializer, state)
    }

    fn get_name(&self) -> &str {
        self.serializer.get_name()
    }

    fn retry_with_lax_check(&self) -> bool {
        self.serializer.retry_with_lax_check()
    }
}
