use std::{borrow::Cow, sync::Arc};

use pyo3::{prelude::*, types::PyType};

use crate::serializers::{
    CombinedSerializer, SerializationState,
    errors::unwrap_ser_error,
    extra::SerCheck,
    infer::call_pydantic_serializer,
    shared::{DoSerialize, TypeSerializer, serialize_to_json, serialize_to_python},
};

/// The polymorphism trampoline detects subclasses of its target type and dispatches to their
/// `__pydantic_serializer__` serializer for serialization.
///
/// This exists as a separate structure to allow for cases such as model serializers where the
/// inner serializer may just be a function serializer and so cannot handle polymorphism itself.
#[derive(Debug)]
pub struct PolymorphismTrampoline {
    class: Py<PyType>,
    /// Inner serializer used when the type is not a subclass (responsible for any fallback etc)
    pub(crate) serializer: Arc<CombinedSerializer>,
    /// Whether polymorphic serialization is enabled from config
    enabled_from_config: bool,
}

impl_py_gc_traverse!(PolymorphismTrampoline { class, serializer });

impl PolymorphismTrampoline {
    pub fn new(class: Py<PyType>, serializer: Arc<CombinedSerializer>, enabled_from_config: bool) -> Self {
        Self {
            class,
            serializer,
            enabled_from_config,
        }
    }

    fn is_subclass(&self, value: &Bound<'_, PyAny>) -> PyResult<bool> {
        Ok(!value.get_type().is(&self.class) && value.is_instance(self.class.bind(value.py()))?)
    }

    fn serialize<'py, T, E: From<PyErr>>(
        &self,
        value: &Bound<'py, PyAny>,
        state: &mut SerializationState<'py>,
        do_serialize: impl DoSerialize<'py, T, E>,
    ) -> Result<T, E> {
        let runtime_polymorphic = state.extra.polymorphic_serialization;
        if state.check != SerCheck::Strict // strict disables polymorphism
            && runtime_polymorphic.unwrap_or(self.enabled_from_config)
            && self.is_subclass(value)?
        {
            call_pydantic_serializer(value, state, do_serialize)
        } else {
            do_serialize.serialize_no_infer(&self.serializer, value, state)
        }
    }
}

impl TypeSerializer for PolymorphismTrampoline {
    fn to_python<'py>(&self, value: &Bound<'py, PyAny>, state: &mut SerializationState<'py>) -> PyResult<Py<PyAny>> {
        self.serialize(value, state, serialize_to_python())
    }

    fn json_key<'a, 'py>(
        &self,
        key: &'a Bound<'py, PyAny>,
        state: &mut SerializationState<'py>,
    ) -> PyResult<Cow<'a, str>> {
        // json key serialization for models and dataclasses was always polymorphic anyway
        // FIXME: make this consistent with the other cases?
        self.serializer.json_key(key, state)
    }

    fn serde_serialize<'py, S: serde::ser::Serializer>(
        &self,
        value: &Bound<'py, PyAny>,
        serializer: S,
        state: &mut SerializationState<'py>,
    ) -> Result<S::Ok, S::Error> {
        self.serialize(value, state, serialize_to_json(serializer))
            .map_err(unwrap_ser_error)
    }

    fn get_name(&self) -> &str {
        self.serializer.get_name()
    }

    fn retry_with_lax_check(&self) -> bool {
        self.serializer.retry_with_lax_check()
    }
}
