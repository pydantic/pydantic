use indexmap::IndexMap;
use std::collections::HashSet;

use pyo3::exceptions::{PyKeyError, PyTypeError};
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict, PyList};

macro_rules! dict_get_required {
    ($dict:ident, $key:expr, $type:ty) => {
        match $dict.get_item($key) {
            Some(t) => <$type>::extract(t)?,
            None => {
                let msg = format!("{} is required", $key);
                return Err(PyKeyError::new_err(msg));
            }
        }
    };
}

macro_rules! dict_get_optional {
    ($dict:ident, $key:expr, $type:ty) => {
        match $dict.get_item($key) {
            Some(t) => Some(<$type>::extract(t)?),
            None => None,
        }
    };
}

#[allow(dead_code)]
#[derive(Debug)]
pub enum SchemaDef {
    // https://json-schema.org/draft/2020-12/json-schema-validation.html#rfc.section.6
    Null,
    Boolean {
        // enum_ makes no sense here
        const_: Option<bool>,
    },
    Integer {
        enum_: Option<Vec<i64>>,
        const_: Option<i64>,
        // https://json-schema.org/draft/2020-12/json-schema-validation.html#rfc.section.6.2
        multiple_of: Option<i64>,
        maximum: Option<i64>,
        exclusive_maximum: Option<i64>,
        minimum: Option<i64>,
        exclusive_minimum: Option<i64>,
    },
    Number {
        enum_: Option<Vec<f64>>,
        const_: Option<f64>,
        // https://json-schema.org/draft/2020-12/json-schema-validation.html#rfc.section.6.2
        multiple_of: Option<f64>,
        minimum: Option<f64>,
        exclusive_minimum: Option<f64>,
        maximum: Option<f64>,
        exclusive_maximum: Option<f64>,
    },
    String {
        enum_: Option<Vec<String>>,
        const_: Option<String>,
        // https://json-schema.org/draft/2020-12/json-schema-validation.html#rfc.section.6.3
        pattern: Option<String>,
        max_length: Option<i64>,
        min_length: Option<i64>,
    },
    Array {
        enum_: Option<Vec<SchemaDef>>,
        // TODO - const_
        // https://json-schema.org/draft/2020-12/json-schema-core.html#rfc.section.10.3.1
        items: Option<Box<SchemaDef>>,
        prefix_items: Option<Vec<SchemaDef>>,
        contains: Option<Box<SchemaDef>>,
        // https://json-schema.org/draft/2020-12/json-schema-validation.html#rfc.section.6.4
        unique_items: bool,
        min_items: Option<usize>,
        max_items: Option<usize>,
        min_contains: Option<usize>,
        max_contains: Option<usize>,
    },
    Object {
        // TODO what do enum and const mean here?
        // https://json-schema.org/draft/2020-12/json-schema-core.html#rfc.section.10.3.2
        properties: IndexMap<String, SchemaDef>,
        // TODO patternProperties
        additional_properties: Option<Box<SchemaDef>>,
        // TODO propertyNames
        // https://json-schema.org/draft/2020-12/json-schema-validation.html#rfc.section.6.5
        min_properties: Option<usize>,
        max_properties: Option<usize>,
        required: Option<HashSet<String>>,
        // TODO dependentRequired
    },
}

impl<'source> FromPyObject<'source> for SchemaDef {
    fn extract(obj: &'source PyAny) -> Result<Self, PyErr> {
        let dict = <PyDict as PyTryFrom>::try_from(obj)?;
        let type_ = dict_get_required!(dict, "type", String);
        match type_.as_str() {
            "null" => Ok(SchemaDef::Null),
            "boolean" => Ok(SchemaDef::Boolean {
                const_: dict_get_optional!(dict, "const", bool),
            }),
            "integer" => Ok(SchemaDef::Integer {
                enum_: dict_get_optional!(dict, "enum", Vec<i64>),
                const_: dict_get_optional!(dict, "const", i64),
                multiple_of: dict_get_optional!(dict, "multiple_of", i64),
                maximum: dict_get_optional!(dict, "maximum", i64),
                exclusive_maximum: dict_get_optional!(dict, "exclusive_maximum", i64),
                minimum: dict_get_optional!(dict, "minimum", i64),
                exclusive_minimum: dict_get_optional!(dict, "exclusive_minimum", i64),
            }),
            "number" => Ok(SchemaDef::Number {
                enum_: dict_get_optional!(dict, "enum", Vec<f64>),
                const_: dict_get_optional!(dict, "const", f64),
                multiple_of: dict_get_optional!(dict, "multiple_of", f64),
                minimum: dict_get_optional!(dict, "minimum", f64),
                exclusive_minimum: dict_get_optional!(dict, "exclusive_minimum", f64),
                maximum: dict_get_optional!(dict, "maximum", f64),
                exclusive_maximum: dict_get_optional!(dict, "exclusive_maximum", f64),
            }),
            "string" => Ok(SchemaDef::String {
                enum_: dict_get_optional!(dict, "enum", Vec<String>),
                const_: dict_get_optional!(dict, "const", String),
                pattern: dict_get_optional!(dict, "pattern", String),
                min_length: dict_get_optional!(dict, "min_length", i64),
                max_length: dict_get_optional!(dict, "max_length", i64),
            }),
            "array" => Ok(SchemaDef::Array {
                enum_: dict_get_optional!(dict, "enum", Vec<SchemaDef>),
                items: match dict.get_item("items") {
                    Some(t) => Some(Box::new(SchemaDef::extract(t)?)),
                    None => None,
                },
                prefix_items: dict_get_optional!(dict, "prefix_items", Vec<SchemaDef>),
                contains: match dict.get_item("contains") {
                    Some(t) => Some(Box::new(SchemaDef::extract(t)?)),
                    None => None,
                },
                unique_items: match dict.get_item("unique_items") {
                    Some(t) => bool::extract(t)?,
                    None => false,
                },
                min_items: dict_get_optional!(dict, "min_items", usize),
                max_items: dict_get_optional!(dict, "max_items", usize),
                min_contains: dict_get_optional!(dict, "min_contains", usize),
                max_contains: dict_get_optional!(dict, "max_contains", usize),
            }),
            "object" => Ok(SchemaDef::Object {
                properties: match dict.get_item("properties") {
                    Some(t) => {
                        let mut properties = IndexMap::new();
                        let dict = <PyDict as PyTryFrom>::try_from(t)?;
                        for (key, value) in dict.iter() {
                            properties.insert(key.to_string(), SchemaDef::extract(value)?);
                        }
                        properties
                    }
                    None => IndexMap::new(),
                },
                additional_properties: match dict.get_item("additional_properties") {
                    Some(t) => Some(Box::new(SchemaDef::extract(t)?)),
                    None => None,
                },
                min_properties: dict_get_optional!(dict, "min_properties", usize),
                max_properties: dict_get_optional!(dict, "max_properties", usize),
                required: match dict.get_item("required") {
                    Some(t) => {
                        let mut required = HashSet::new();
                        let list = <PyList as PyTryFrom>::try_from(t)?;
                        for item in list.iter() {
                            required.insert(item.to_string());
                        }
                        Some(required)
                    }
                    None => None,
                },
            }),
            _ => Err(PyTypeError::new_err(format!("unsupported type: {}", type_))),
        }
    }
}
