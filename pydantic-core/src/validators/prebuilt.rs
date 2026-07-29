use std::sync::Arc;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyType};

use crate::common::prebuilt::get_prebuilt;
use crate::errors::ValResult;
use crate::input::Input;
use crate::tools::SchemaDict;

use super::ValidationState;
use super::{CombinedValidator, SchemaValidator, Validator};

pub struct PrebuiltValidator {
    /// Keeps the referenced `SchemaValidator` alive (and with it, `validator`). This is also the
    /// only field reported to the garbage collector: the contents of `validator` are owned (and
    /// traversed) by the `SchemaValidator`, so they must not be traversed a second time here.
    schema_validator: Py<SchemaValidator>,
    /// The `model`/`dataclass` validator of the referenced class, found by walking the schema
    /// validator's tree from the root (see `find_class_validator`).
    validator: Arc<CombinedValidator>,
}

#[allow(clippy::missing_fields_in_debug)] // `schema_validator` is deliberately omitted
impl std::fmt::Debug for PrebuiltValidator {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        // Note: the delegated validator is deliberately not expanded: it is owned by another
        // `SchemaValidator`, and expanding it per reference can result in exponentially large
        // output with highly interconnected models.
        f.debug_struct("PrebuiltValidator")
            .field("validator", &self.validator.get_name())
            .finish()
    }
}

impl PrebuiltValidator {
    pub fn try_get_from_schema(type_: &str, schema: &Bound<'_, PyDict>) -> PyResult<Option<CombinedValidator>> {
        get_prebuilt(type_, schema, "__pydantic_validator__", |py_any| {
            let schema_validator: Py<SchemaValidator> = match py_any.extract() {
                Ok(schema_validator) => schema_validator,
                // If any Pydantic plugin is installed, `__pydantic_validator__` is a
                // `pydantic.plugin._schema_validator.PluggableSchemaValidator` wrapping the actual
                // `SchemaValidator`. Plugin callbacks only fire on the top-level validation entry
                // points (`validate_python()`, etc.) and never on nested validation of a sub-model,
                // so reusing the wrapped validator is behavior-preserving:
                Err(_) => match py_any.getattr(intern!(py_any.py(), "_schema_validator")) {
                    Ok(inner) => match inner.extract() {
                        Ok(schema_validator) => schema_validator,
                        Err(_) => return Ok(None),
                    },
                    Err(_) => return Ok(None),
                },
            };

            let class: Bound<'_, PyType> = schema.get_as_req(intern!(schema.py(), "cls"))?;
            let Some(validator) = find_class_validator(schema_validator.get().validator.clone(), &class) else {
                return Ok(None);
            };

            Ok(Some(
                Self {
                    schema_validator,
                    validator,
                }
                .into(),
            ))
        })
    }
}

/// Walk a class's prebuilt validator tree from the root to the class's own `model`/`dataclass`
/// validator, which is the only part of the tree that a schema *referencing* the class compiles
/// by reference rather than inline:
///
/// - a recursive class stores its schema in a definition, making the root of its own tree a
///   reference to that definition — resolve it (the class is complete, so the definition is
///   filled);
/// - `@model_validator(mode='after')`/`(mode='wrap')` validators are applied *outside* of the
///   `model` (or `dataclass`) schema, and are therefore compiled inline by the referencing schema
///   before the inner `model`/`dataclass` schema is reached. Delegating to them would run the
///   function validators a second time, so strip them.
///
/// If the walk moves past any of those but does not end at the `model`/`dataclass` validator of
/// the referenced class itself, the schema was built in some non-standard way (e.g. a custom
/// `__get_pydantic_core_schema__` wrapping the model schema), and `None` is returned so that the
/// referencing schema conservatively compiles the class's schema inline instead.
///
/// A root that is none of the above (e.g. a hand-built schema whose validator is a plain function
/// validator) is delegated to wholesale, preserving the longstanding behavior that
/// `__pydantic_validator__` stands in for the class wherever it is referenced.
fn find_class_validator(
    mut target: Arc<CombinedValidator>,
    class: &Bound<'_, PyType>,
) -> Option<Arc<CombinedValidator>> {
    let mut walked = false;
    // Bounded to guard against reference cycles, which a hand-built schema can produce.
    for _ in 0..64 {
        target = match target.as_ref() {
            CombinedValidator::DefinitionRef(definition_ref_validator) => {
                definition_ref_validator.resolved_validator()?
            }
            CombinedValidator::FunctionAfter(function_validator) => function_validator.inner_validator().clone(),
            CombinedValidator::FunctionWrap(function_validator) => function_validator.inner_validator().clone(),
            CombinedValidator::Model(model_validator) => {
                return model_validator.class().is(class).then_some(target.clone());
            }
            CombinedValidator::Dataclass(dataclass_validator) => {
                return dataclass_validator.class().is(class).then_some(target.clone());
            }
            _ if walked => return None,
            _ => return Some(target.clone()),
        };
        walked = true;
    }
    None
}

impl_py_gc_traverse!(PrebuiltValidator { schema_validator });

impl Validator for PrebuiltValidator {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Py<PyAny>> {
        self.validator.validate(py, input, state)
    }

    fn get_name(&self) -> &str {
        self.validator.get_name()
    }
}
