use std::fmt;

use indexmap::IndexMap;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use serde::de::{Deserialize, DeserializeSeed, Error as SerdeError, MapAccess, SeqAccess, Visitor};

// taken from `serde_json`
// We only use our own error type; no need for From conversions provided by the
// standard library's try! macro. This reduces lines of LLVM IR by 4%.
macro_rules! tri {
    ($e:expr $(,)?) => {
        match $e {
            Ok(val) => val,
            Err(err) => return Err(err),
        }
    };
}

/// similar to serde `Value` but with int and float split
#[derive(Clone, Debug)]
pub enum JsonInput {
    Null,
    Bool(bool),
    Int(i64),
    Float(f64),
    String(String),
    Array(JsonArray),
    Object(JsonObject),
}
pub type JsonArray = Vec<JsonInput>;
pub type JsonObject = IndexMap<String, JsonInput>;

impl ToPyObject for JsonInput {
    fn to_object(&self, py: Python<'_>) -> PyObject {
        match self {
            Self::Null => py.None(),
            Self::Bool(b) => b.into_py(py),
            Self::Int(i) => i.into_py(py),
            Self::Float(f) => f.into_py(py),
            Self::String(s) => s.into_py(py),
            Self::Array(v) => v.iter().map(|v| v.to_object(py)).collect::<Vec<_>>().into_py(py),
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
    #[inline]
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

            #[inline]
            fn visit_bool<E>(self, value: bool) -> Result<JsonInput, E> {
                Ok(JsonInput::Bool(value))
            }

            #[inline]
            fn visit_i64<E>(self, value: i64) -> Result<JsonInput, E> {
                Ok(JsonInput::Int(value))
            }

            #[inline]
            fn visit_u64<E>(self, value: u64) -> Result<JsonInput, E> {
                Ok(JsonInput::Int(value as i64))
            }

            #[inline]
            fn visit_f64<E>(self, value: f64) -> Result<JsonInput, E> {
                Ok(JsonInput::Float(value))
            }

            #[inline]
            fn visit_str<E>(self, value: &str) -> Result<JsonInput, E>
            where
                E: SerdeError,
            {
                Ok(JsonInput::String(value.to_string()))
            }

            #[inline]
            fn visit_string<E>(self, value: String) -> Result<JsonInput, E> {
                Ok(JsonInput::String(value))
            }

            #[inline]
            fn visit_none<E>(self) -> Result<JsonInput, E> {
                Ok(JsonInput::Null)
            }

            #[inline]
            fn visit_some<D>(self, deserializer: D) -> Result<JsonInput, D::Error>
            where
                D: serde::Deserializer<'de>,
            {
                Deserialize::deserialize(deserializer)
            }

            #[inline]
            fn visit_unit<E>(self) -> Result<JsonInput, E> {
                Ok(JsonInput::Null)
            }

            #[inline]
            fn visit_seq<V>(self, mut visitor: V) -> Result<JsonInput, V::Error>
            where
                V: SeqAccess<'de>,
            {
                let mut vec = Vec::new();

                while let Some(elem) = tri!(visitor.next_element()) {
                    vec.push(elem);
                }

                Ok(JsonInput::Array(vec))
            }

            fn visit_map<V>(self, mut visitor: V) -> Result<JsonInput, V::Error>
            where
                V: MapAccess<'de>,
            {
                match visitor.next_key_seed(KeyDeserializer)? {
                    Some(first_key) => {
                        let mut values = IndexMap::new();

                        values.insert(first_key, tri!(visitor.next_value()));
                        while let Some((key, value)) = tri!(visitor.next_entry()) {
                            values.insert(key, value);
                        }
                        Ok(JsonInput::Object(values))
                    }
                    None => Ok(JsonInput::Object(IndexMap::new())),
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

    fn visit_string<E>(self, s: String) -> Result<Self::Value, E>
    where
        E: serde::de::Error,
    {
        Ok(s)
    }
}
