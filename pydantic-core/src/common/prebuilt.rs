use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict, PyString, PyType};

use crate::tools::SchemaDict;

/// Which prebuilt object to fetch from the class' `__dict__`.
#[derive(Clone, Copy)]
pub enum PrebuiltAttr {
    Validator,
    Serializer,
}

impl PrebuiltAttr {
    fn name(self, py: Python<'_>) -> &Bound<'_, PyString> {
        match self {
            Self::Validator => intern!(py, "__pydantic_validator__"),
            Self::Serializer => intern!(py, "__pydantic_serializer__"),
        }
    }
}

pub fn get_prebuilt<T>(
    type_: &str,
    schema: &Bound<'_, PyDict>,
    prebuilt_attr: PrebuiltAttr,
    extractor: impl FnOnce(Bound<'_, PyAny>) -> PyResult<Option<T>>,
) -> PyResult<Option<T>> {
    let py = schema.py();

    // we can only use prebuilt validators/serializers from models and Pydantic dataclasses.
    // However, we don't want to use a prebuilt structure from dataclasses if we have a `generic_origin`
    // as this means the dataclass was parametrized (so a generic alias instance), and `cls` in the
    // core schema is still the (unparametrized) class, meaning we would fetch the wrong validator/serializer.
    if !matches!(type_, "model" | "dataclass")
        || (type_ == "dataclass" && schema.contains(intern!(py, "generic_origin"))?)
    {
        return Ok(None);
    }

    let class: Bound<'_, PyType> = schema.get_as_req(intern!(py, "cls"))?;

    // Note: we NEED to use the __dict__ here (and perform get_item calls rather than getattr)
    // because we don't want to fetch prebuilt validators from parent classes.
    let Some(class_dict) = type_dict(&class)? else {
        return Ok(None);
    };

    let is_complete: bool = class_dict_get(&class_dict, intern!(py, "__pydantic_complete__"))?
        .is_some_and(|b| b.extract().unwrap_or(false));

    if !is_complete {
        return Ok(None);
    }

    // Retrieve the prebuilt validator / serializer if available
    match class_dict_get(&class_dict, prebuilt_attr.name(py))? {
        Some(prebuilt) => extractor(prebuilt),
        None => Ok(None),
    }
}

/// Get the class `__dict__`.
///
/// On CPython 3.12+, for a class whose metaclass doesn't customize the attribute access nor `__dict__` (see
/// `has_standard_type_dict()`), this reads the type's dict directly (the same object the `__dict__` mappingproxy
/// then wraps), avoiding the attribute lookup and the mappingproxy allocation; otherwise (e.g. a metaclass
/// defining `__dict__` as a property, or `__getattribute__`), the attribute is looked up as usual.
#[cfg(all(Py_3_12, not(any(PyPy, GraalPy, Py_LIMITED_API))))]
fn type_dict<'py>(class: &Bound<'py, PyType>) -> PyResult<Option<Bound<'py, PyAny>>> {
    use pyo3::types::PyTypeMethods;
    // SAFETY: `class` is a valid type object; PyType_GetDict returns a new (strong) reference to the type's
    // dict, or NULL (without an exception set) for a type that is not initialized yet
    unsafe {
        if crate::model_class_lookup::has_standard_type_dict(class.as_ptr()) {
            return Ok(Bound::from_owned_ptr_or_opt(
                class.py(),
                pyo3::ffi::PyType_GetDict(class.as_type_ptr()),
            ));
        }
    }
    class.as_any().getattr(intern!(class.py(), "__dict__")).map(Some)
}

#[cfg(not(all(Py_3_12, not(any(PyPy, GraalPy, Py_LIMITED_API)))))]
fn type_dict<'py>(class: &Bound<'py, PyType>) -> PyResult<Option<Bound<'py, PyAny>>> {
    class.as_any().getattr(intern!(class.py(), "__dict__")).map(Some)
}

/// `class_dict.get(key)`: works for both a real dict (fast path) and a mappingproxy / arbitrary mapping.
fn class_dict_get<'py>(
    class_dict: &Bound<'py, PyAny>,
    key: &Bound<'py, PyString>,
) -> PyResult<Option<Bound<'py, PyAny>>> {
    if let Ok(dict) = class_dict.cast_exact::<PyDict>() {
        dict.get_item(key)
    } else {
        match class_dict.get_item(key) {
            Ok(v) => Ok(Some(v)),
            Err(e) if e.is_instance_of::<pyo3::exceptions::PyKeyError>(class_dict.py()) => Ok(None),
            Err(e) => Err(e),
        }
    }
}
