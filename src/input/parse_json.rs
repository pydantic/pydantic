use std::fmt;

use num_bigint::BigInt;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use serde::de::{Deserialize, DeserializeSeed, Error as SerdeError, MapAccess, SeqAccess, Visitor};

use crate::lazy_index_map::LazyIndexMap;

/// similar to serde `Value` but with int and float split
#[derive(Clone, Debug)]
pub enum JsonInput {
    Null,
    Bool(bool),
    Int(i64),
    BigInt(BigInt),
    Uint(u64),
    Float(f64),
    String(String),
    Array(JsonArray),
    Object(JsonObject),
}
pub type JsonArray = Vec<JsonInput>;
pub type JsonObject = LazyIndexMap<String, JsonInput>;

impl ToPyObject for JsonInput {
    fn to_object(&self, py: Python<'_>) -> PyObject {
        match self {
            Self::Null => py.None(),
            Self::Bool(b) => b.into_py(py),
            Self::Int(i) => i.into_py(py),
            Self::BigInt(b) => b.to_object(py),
            Self::Uint(i) => i.into_py(py),
            Self::Float(f) => f.into_py(py),
            Self::String(s) => s.into_py(py),
            Self::Array(v) => PyList::new(py, v.iter().map(|v| v.to_object(py))).into_py(py),
            Self::Object(o) => {
                let dict = PyDict::new(py);
                for (k, v) in o.iter() {
                    dict.set_item(k, v.to_object(py)).unwrap();
                }
                dict.into_py(py)
            }
        }
    }
}

impl<'de> Deserialize<'de> for JsonInput {
    fn deserialize<D>(deserializer: D) -> Result<JsonInput, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        struct JsonVisitor;

        impl<'de> Visitor<'de> for JsonVisitor {
            type Value = JsonInput;

            #[cfg_attr(has_no_coverage, no_coverage)]
            fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
                formatter.write_str("any valid JSON value")
            }

            fn visit_bool<E>(self, value: bool) -> Result<JsonInput, E> {
                Ok(JsonInput::Bool(value))
            }

            fn visit_i64<E>(self, value: i64) -> Result<JsonInput, E> {
                Ok(JsonInput::Int(value))
            }

            fn visit_u64<E>(self, value: u64) -> Result<JsonInput, E> {
                match i64::try_from(value) {
                    Ok(i) => Ok(JsonInput::Int(i)),
                    Err(_) => Ok(JsonInput::Uint(value)),
                }
            }

            fn visit_f64<E>(self, value: f64) -> Result<JsonInput, E> {
                Ok(JsonInput::Float(value))
            }

            fn visit_str<E>(self, value: &str) -> Result<JsonInput, E>
            where
                E: SerdeError,
            {
                Ok(JsonInput::String(value.to_string()))
            }

            fn visit_string<E>(self, value: String) -> Result<JsonInput, E> {
                Ok(JsonInput::String(value))
            }

            #[cfg_attr(has_no_coverage, no_coverage)]
            fn visit_none<E>(self) -> Result<JsonInput, E> {
                unreachable!()
            }

            #[cfg_attr(has_no_coverage, no_coverage)]
            fn visit_some<D>(self, _: D) -> Result<JsonInput, D::Error>
            where
                D: serde::Deserializer<'de>,
            {
                unreachable!()
            }

            fn visit_unit<E>(self) -> Result<JsonInput, E> {
                Ok(JsonInput::Null)
            }

            fn visit_seq<V>(self, mut visitor: V) -> Result<JsonInput, V::Error>
            where
                V: SeqAccess<'de>,
            {
                let mut vec = Vec::new();

                while let Some(elem) = visitor.next_element()? {
                    vec.push(elem);
                }

                Ok(JsonInput::Array(vec))
            }

            fn visit_map<V>(self, mut visitor: V) -> Result<JsonInput, V::Error>
            where
                V: MapAccess<'de>,
            {
                const SERDE_JSON_NUMBER: &str = "$serde_json::private::Number";
                match visitor.next_key_seed(KeyDeserializer)? {
                    Some(first_key) => {
                        let mut values = LazyIndexMap::new();
                        let first_value = visitor.next_value()?;

                        // serde_json will parse arbitrary precision numbers into a map
                        // structure with a "number" key and a String value
                        'try_number: {
                            if first_key == SERDE_JSON_NUMBER {
                                // Just in case someone tries to actually store that key in a real map,
                                // keep parsing and continue as a map if so

                                if let Some((key, value)) = visitor.next_entry::<String, JsonInput>()? {
                                    // Important to preserve order of the keys
                                    values.insert(first_key, first_value);
                                    values.insert(key, value);
                                    break 'try_number;
                                }

                                if let JsonInput::String(s) = &first_value {
                                    // Normalize the string to either an int or float
                                    let normalized = if s.contains('.') {
                                        JsonInput::Float(
                                            s.parse()
                                                .map_err(|e| V::Error::custom(format!("expected a float: {e}")))?,
                                        )
                                    } else if let Ok(i) = s.parse::<i64>() {
                                        JsonInput::Int(i)
                                    } else if let Ok(big) = s.parse::<BigInt>() {
                                        JsonInput::BigInt(big)
                                    } else {
                                        // Failed to normalize, just throw it in the map and continue
                                        values.insert(first_key, first_value);
                                        break 'try_number;
                                    };

                                    return Ok(normalized);
                                };
                            } else {
                                values.insert(first_key, first_value);
                            }
                        }

                        while let Some((key, value)) = visitor.next_entry()? {
                            values.insert(key, value);
                        }
                        Ok(JsonInput::Object(values))
                    }
                    None => Ok(JsonInput::Object(LazyIndexMap::new())),
                }
            }
        }

        deserializer.deserialize_any(JsonVisitor)
    }
}

struct KeyDeserializer;

impl<'de> DeserializeSeed<'de> for KeyDeserializer {
    type Value = String;

    fn deserialize<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        deserializer.deserialize_str(self)
    }
}

impl<'de> Visitor<'de> for KeyDeserializer {
    type Value = String;

    #[cfg_attr(has_no_coverage, no_coverage)]
    fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
        formatter.write_str("a string key")
    }

    fn visit_str<E>(self, s: &str) -> Result<Self::Value, E>
    where
        E: serde::de::Error,
    {
        Ok(s.to_string())
    }

    #[cfg_attr(has_no_coverage, no_coverage)]
    fn visit_string<E>(self, _: String) -> Result<Self::Value, E>
    where
        E: serde::de::Error,
    {
        unreachable!()
    }
}
