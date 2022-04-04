use std::collections::HashSet;

use pyo3::exceptions::{PyKeyError, PyTypeError};
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict, PyList};

macro_rules! dict_get {
    ($dict:ident, $key:expr, $type:ty) => {
        match $dict.get_item($key) {
            Some(t) => Some(<$type>::extract(t)?),
            None => None,
        }
    };
}

#[allow(dead_code)]
#[derive(Debug)]
pub enum Schema {
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
        max_length: Option<usize>,
        min_length: Option<usize>,
    },
    Array {
        enum_: Option<Vec<Schema>>,
        // TODO - const_
        // https://json-schema.org/draft/2020-12/json-schema-core.html#rfc.section.10.3.1
        items: Option<Box<Schema>>,
        prefix_items: Option<Vec<Schema>>,
        contains: Option<Box<Schema>>,
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
        properties: Vec<SchemaProperty>,
        // missing patternProperties
        additional_properties: Option<Box<Schema>>,
        // missing propertyNames
        // https://json-schema.org/draft/2020-12/json-schema-validation.html#rfc.section.6.5
        min_properties: Option<usize>,
        max_properties: Option<usize>,
        // missing dependentRequired
    },
}

#[allow(dead_code)]
#[derive(Debug)]
pub struct SchemaProperty {
    pub key: String,
    pub required: bool,
    pub schema: Schema,
}

impl<'source> FromPyObject<'source> for Schema {
    fn extract(obj: &'source PyAny) -> Result<Self, PyErr> {
        let dict = <PyDict as PyTryFrom>::try_from(obj)?;
        let type_ = match dict_get!(dict, "type", String) {
            Some(type_) => type_,
            None => {
                return Err(PyKeyError::new_err("'type' is required"));
            }
        };
        match type_.as_str() {
            "null" => Ok(Schema::Null),
            "boolean" => Ok(Schema::Boolean {
                const_: dict_get!(dict, "const", bool),
            }),
            "integer" => Ok(Schema::Integer {
                enum_: dict_get!(dict, "enum", Vec<i64>),
                const_: dict_get!(dict, "const", i64),
                multiple_of: dict_get!(dict, "multiple_of", i64),
                maximum: dict_get!(dict, "maximum", i64),
                exclusive_maximum: dict_get!(dict, "exclusive_maximum", i64),
                minimum: dict_get!(dict, "minimum", i64),
                exclusive_minimum: dict_get!(dict, "exclusive_minimum", i64),
            }),
            "number" => Ok(Schema::Number {
                enum_: dict_get!(dict, "enum", Vec<f64>),
                const_: dict_get!(dict, "const", f64),
                multiple_of: dict_get!(dict, "multiple_of", f64),
                minimum: dict_get!(dict, "minimum", f64),
                exclusive_minimum: dict_get!(dict, "exclusive_minimum", f64),
                maximum: dict_get!(dict, "maximum", f64),
                exclusive_maximum: dict_get!(dict, "exclusive_maximum", f64),
            }),
            "string" => Ok(Schema::String {
                enum_: dict_get!(dict, "enum", Vec<String>),
                const_: dict_get!(dict, "const", String),
                pattern: dict_get!(dict, "pattern", String),
                min_length: dict_get!(dict, "min_length", usize),
                max_length: dict_get!(dict, "max_length", usize),
            }),
            "array" => Ok(Schema::Array {
                enum_: dict_get!(dict, "enum", Vec<Schema>),
                items: match dict.get_item("items") {
                    Some(t) => Some(Box::new(Schema::extract(t)?)),
                    None => None,
                },
                prefix_items: dict_get!(dict, "prefix_items", Vec<Schema>),
                contains: match dict.get_item("contains") {
                    Some(t) => Some(Box::new(Schema::extract(t)?)),
                    None => None,
                },
                unique_items: match dict.get_item("unique_items") {
                    Some(t) => bool::extract(t)?,
                    None => false,
                },
                min_items: dict_get!(dict, "min_items", usize),
                max_items: dict_get!(dict, "max_items", usize),
                min_contains: dict_get!(dict, "min_contains", usize),
                max_contains: dict_get!(dict, "max_contains", usize),
            }),
            "object" => {
                let required = match dict.get_item("required") {
                    Some(t) => {
                        let mut required = HashSet::new();
                        let list = <PyList as PyTryFrom>::try_from(t)?;
                        for item in list.iter() {
                            required.insert(item.to_string());
                        }
                        required
                    }
                    None => HashSet::new(),
                };

                Ok(Schema::Object {
                    properties: match dict.get_item("properties") {
                        Some(t) => {
                            let mut properties: Vec<SchemaProperty> = Vec::with_capacity(5);
                            let dict = <PyDict as PyTryFrom>::try_from(t)?;
                            for (key, value) in dict.iter() {
                                properties.push(SchemaProperty {
                                    key: key.to_string(),
                                    required: required.contains(&key.to_string()),
                                    schema: Schema::extract(value)?,
                                });
                            }
                            properties
                        }
                        None => Vec::new(),
                    },
                    additional_properties: match dict.get_item("additional_properties") {
                        Some(t) => Some(Box::new(Schema::extract(t)?)),
                        None => None,
                    },
                    min_properties: dict_get!(dict, "min_properties", usize),
                    max_properties: dict_get!(dict, "max_properties", usize),
                })
            }
            _ => Err(PyTypeError::new_err(format!("unknown type: '{}'", type_))),
        }
    }
}
