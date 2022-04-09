use std::collections::HashSet;

use pyo3::exceptions::{PyKeyError, PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict, PyList};

use crate::utils::{dict_get, RegexPattern};
use crate::standalone_validators::validate_str_full;

trait SchemaType {
    fn build(dict: &PyDict) -> PyResult<Self>
    where
        Self: Sized;

    fn validate(&self, py: Python, obj: &PyAny) -> PyResult<PyObject>;
}

#[allow(dead_code)]
#[derive(Debug)]
struct NullSchema {}

impl SchemaType for NullSchema {
    fn build(_dict: &PyDict) -> PyResult<Self> {
        Ok(NullSchema {})
    }

    fn validate(&self, py: Python, _obj: &PyAny) -> PyResult<PyObject> {
        Ok(py.None())
    }
}

#[allow(dead_code)]
#[derive(Debug)]
struct BooleanSchema {
    // enum_ makes no sense here
    const_: Option<bool>,
}

impl SchemaType for BooleanSchema {
    fn build(dict: &PyDict) -> PyResult<Self> {
        Ok(BooleanSchema {
            const_: dict_get!(dict, "const", bool),
        })
    }

    fn validate(&self, py: Python, obj: &PyAny) -> PyResult<PyObject> {
        Ok(bool::extract(obj)?.to_object(py))
    }
}

#[allow(dead_code)]
#[derive(Debug)]
struct IntegerSchema {
    enum_: Option<Vec<i64>>,
    const_: Option<i64>,
    // https://json-schema.org/draft/2020-12/json-schema-validation.html#rfc.section.6.2
    multiple_of: Option<i64>,
    maximum: Option<i64>,
    exclusive_maximum: Option<i64>,
    minimum: Option<i64>,
    exclusive_minimum: Option<i64>,
}

impl SchemaType for IntegerSchema {
    fn build(dict: &PyDict) -> PyResult<Self> {
        Ok(IntegerSchema {
            enum_: dict_get!(dict, "enum", Vec<i64>),
            const_: dict_get!(dict, "const", i64),
            multiple_of: dict_get!(dict, "multiple_of", i64),
            maximum: dict_get!(dict, "maximum", i64),
            exclusive_maximum: dict_get!(dict, "exclusive_maximum", i64),
            minimum: dict_get!(dict, "minimum", i64),
            exclusive_minimum: dict_get!(dict, "exclusive_minimum", i64),
        })
    }

    fn validate(&self, py: Python, obj: &PyAny) -> PyResult<PyObject> {
        Ok(i64::extract(obj)?.to_object(py))
    }
}

#[allow(dead_code)]
#[derive(Debug)]
struct NumberSchema {
    enum_: Option<Vec<f64>>,
    const_: Option<f64>,
    // https://json-schema.org/draft/2020-12/json-schema-validation.html#rfc.section.6.2
    multiple_of: Option<f64>,
    minimum: Option<f64>,
    exclusive_minimum: Option<f64>,
    maximum: Option<f64>,
    exclusive_maximum: Option<f64>,
}

impl SchemaType for NumberSchema {
    fn build(dict: &PyDict) -> PyResult<Self> {
        Ok(NumberSchema {
            enum_: dict_get!(dict, "enum", Vec<f64>),
            const_: dict_get!(dict, "const", f64),
            multiple_of: dict_get!(dict, "multiple_of", f64),
            minimum: dict_get!(dict, "minimum", f64),
            exclusive_minimum: dict_get!(dict, "exclusive_minimum", f64),
            maximum: dict_get!(dict, "maximum", f64),
            exclusive_maximum: dict_get!(dict, "exclusive_maximum", f64),
        })
    }

    fn validate(&self, py: Python, obj: &PyAny) -> PyResult<PyObject> {
        Ok(f64::extract(obj)?.to_object(py))
    }
}

#[allow(dead_code)]
#[derive(Debug)]
struct StringSchema {
    enum_: Option<Vec<String>>,
    const_: Option<String>,
    // https://json-schema.org/draft/2020-12/json-schema-validation.html#rfc.section.6.3
    pattern: Option<RegexPattern>,
    max_length: Option<usize>,
    min_length: Option<usize>,
}

impl SchemaType for StringSchema {
    fn build(dict: &PyDict) -> PyResult<Self> {
        Ok(StringSchema {
            enum_: dict_get!(dict, "enum", Vec<String>),
            const_: dict_get!(dict, "const", String),
            pattern: dict_get!(dict, "pattern", RegexPattern),
            min_length: dict_get!(dict, "min_length", usize),
            max_length: dict_get!(dict, "max_length", usize),
        })
    }

    fn validate(&self, py: Python, obj: &PyAny) -> PyResult<PyObject> {
        let s = validate_str_full(
            py,
            obj,
            self.min_length,
            self.max_length,
            false,
            false,
            false,
            self.pattern.as_ref(),
        )?;
        Ok(s.to_object(py))
    }
}

#[allow(dead_code)]
#[derive(Debug)]
struct ArraySchema {
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
}

impl SchemaType for ArraySchema {
    fn build(dict: &PyDict) -> PyResult<Self> {
        Ok(ArraySchema {
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
        })
    }

    fn validate(&self, py: Python, _obj: &PyAny) -> PyResult<PyObject> {
        Ok("TODO: ArraySchema::validate".to_object(py))
    }
}

#[allow(dead_code)]
#[derive(Debug)]
struct SchemaProperty {
    key: String,
    required: bool,
    schema: Schema,
    validator: Option<PyObject>,
}

#[allow(dead_code)]
#[derive(Debug)]
struct ModelSchema {
    // TODO what do enum and const mean here?
    // https://json-schema.org/draft/2020-12/json-schema-core.html#rfc.section.10.3.2
    pub properties: Vec<SchemaProperty>,
    // missing patternProperties
    additional_properties: Option<Box<Schema>>,
    // missing propertyNames
    // https://json-schema.org/draft/2020-12/json-schema-validation.html#rfc.section.6.5
    min_properties: Option<usize>,
    max_properties: Option<usize>,
    // missing dependentRequired
}

impl SchemaType for ModelSchema {
    fn build(dict: &PyDict) -> PyResult<Self> {
        let required = match dict.get_item("required") {
            Some(t) => {
                let mut required = HashSet::new();
                let list: &PyList = t.cast_as()?;
                for item in list.iter() {
                    required.insert(item.to_string());
                }
                required
            }
            None => HashSet::new(),
        };

        Ok(ModelSchema {
            properties: match dict.get_item("properties") {
                Some(t) => {
                    let dict: &PyDict = t.cast_as()?;
                    let mut properties: Vec<SchemaProperty> = Vec::with_capacity(dict.len());
                    for (key, value) in dict.iter() {
                        let value_dict: &PyDict = value.cast_as()?;

                        let validator: Option<PyObject> = match value_dict.get_item("validator") {
                            Some(t) => {
                                if !t.is_callable() {
                                    return Err(PyTypeError::new_err("validator must be callable".to_string()));
                                }
                                Some(t.into())
                            }
                            None => None,
                        };
                        properties.push(SchemaProperty {
                            key: key.to_string(),
                            required: required.contains(&key.to_string()),
                            schema: Schema::extract(value)?,
                            validator,
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

    fn validate(&self, py: Python, obj: &PyAny) -> PyResult<PyObject> {
        let obj_dict: &PyDict = obj.cast_as()?;
        let new_obj = PyDict::new(py);
        let mut errors = Vec::new();
        for property in &self.properties {
            if let Some(value) = obj_dict.get_item(property.key.clone()) {
                let mut value = property.schema.validate(py, value)?;
                if let Some(validator) = &property.validator {
                    value = validator.call(py, (value,), None)?;
                }
                new_obj.set_item(property.key.clone(), value)?;
            } else if property.required {
                errors.push(format!("Missing property: {}", property.key));
            }
        }
        if errors.is_empty() {
            Ok(new_obj.into())
        } else {
            Err(PyValueError::new_err(errors))
        }
    }
}

#[allow(dead_code)]
#[derive(Debug)]
enum Schema {
    // https://json-schema.org/draft/2020-12/json-schema-validation.html#rfc.section.6
    Null(NullSchema),
    Boolean(BooleanSchema),
    Integer(IntegerSchema),
    Number(NumberSchema),
    String(StringSchema),
    Array(ArraySchema),
    Model(ModelSchema),
    // TODO date, datetime, set, bytes, custom types, dict, union, enum only - e.g. literal
}

impl SchemaType for Schema {
    fn build(dict: &PyDict) -> PyResult<Self> {
        let type_ = match dict_get!(dict, "type", String) {
            Some(type_) => type_,
            None => {
                return Err(PyKeyError::new_err("'type' is required"));
            }
        };
        let s = match type_.as_str() {
            "null" => Schema::Null(NullSchema::build(dict)?),
            "boolean" => Schema::Boolean(BooleanSchema::build(dict)?),
            "integer" => Schema::Integer(IntegerSchema::build(dict)?),
            "number" => Schema::Number(NumberSchema::build(dict)?),
            "string" => Schema::String(StringSchema::build(dict)?),
            "array" => Schema::Array(ArraySchema::build(dict)?),
            "object" => Schema::Model(ModelSchema::build(dict)?),
            _ => return Err(PyTypeError::new_err(format!("unknown type: '{}'", type_))),
        };
        Ok(s)
    }

    fn validate(&self, py: Python, obj: &PyAny) -> PyResult<PyObject> {
        match self {
            Schema::Null(v) => v.validate(py, obj),
            Schema::Boolean(v) => v.validate(py, obj),
            Schema::Integer(v) => v.validate(py, obj),
            Schema::Number(v) => v.validate(py, obj),
            Schema::String(v) => v.validate(py, obj),
            Schema::Array(v) => v.validate(py, obj),
            Schema::Model(v) => v.validate(py, obj),
        }
    }
}

impl<'source> FromPyObject<'source> for Schema {
    fn extract(obj: &'source PyAny) -> Result<Self, PyErr> {
        let dict: &PyDict = obj.cast_as()?;
        Schema::build(dict)
    }
}

#[pyclass]
pub struct SchemaValidator {
    schema: Schema,
}

#[pymethods]
impl SchemaValidator {
    #[new]
    fn py_new(py: Python, schema: PyObject) -> PyResult<Self> {
        let schema: Schema = schema.extract(py)?;
        Ok(Self { schema })
    }

    fn validate(&self, py: Python, data: &PyAny) -> PyResult<PyObject> {
        self.schema.validate(py, data)
    }

    fn __repr__(&self) -> PyResult<String> {
        Ok(format!("SchemaValidator({:?})", self.schema))
    }
}
