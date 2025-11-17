use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict, PyType};

use crate::tools::SchemaDict;

pub fn get_prebuilt<T>(
    type_: &str,
    schema: &Bound<'_, PyDict>,
    prebuilt_attr_name: &str,
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
    // We don't downcast here because __dict__ on a class is a readonly mappingproxy,
    // so we can just leave it as is and do get_item checks.
    let class_dict = class.getattr(intern!(py, "__dict__"))?;

    let is_complete: bool = class_dict
        .get_item(intern!(py, "__pydantic_complete__"))
        .is_ok_and(|b| b.extract().unwrap_or(false));

    if !is_complete {
        return Ok(None);
    }

    // Retrieve the prebuilt validator / serializer if available
    let prebuilt: Bound<'_, PyAny> = class_dict.get_item(prebuilt_attr_name)?;
    extractor(prebuilt)
}
