use pyo3::prelude::*;
use pyo3::types::{PyDict, PyType};
use serde_json::{Map, Value};

use crate::errors::{err_val_error, ErrorKind, InputValue, LocItem, ValResult};

use super::shared::{float_as_int, int_as_bool, str_as_bool, str_as_int};
use super::traits::{DictInput, Input, ListInput, ToLocItem, ToPy};

impl Input for Value {
    fn is_none(&self) -> bool {
        matches!(self, Value::Null)
    }

    fn strict_str(&self) -> ValResult<String> {
        match self {
            Value::String(s) => Ok(s.to_string()),
            _ => err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::StrType),
        }
    }

    fn lax_str(&self) -> ValResult<String> {
        match self {
            Value::String(s) => Ok(s.to_string()),
            Value::Number(n) => Ok(n.to_string()),
            _ => err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::StrType),
        }
    }

    fn strict_bool(&self) -> ValResult<bool> {
        match self {
            Value::Bool(b) => Ok(*b),
            _ => err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::BoolType),
        }
    }

    fn lax_bool(&self) -> ValResult<bool> {
        match self {
            Value::Bool(b) => Ok(*b),
            Value::String(s) => str_as_bool(self, s),
            Value::Number(n) => {
                if let Some(int) = n.as_i64() {
                    int_as_bool(self, int)
                } else {
                    err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::BoolParsing)
                }
            }
            _ => err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::BoolType),
        }
    }

    fn strict_int(&self) -> ValResult<i64> {
        match self {
            Value::Number(n) => {
                if let Some(int) = n.as_i64() {
                    Ok(int)
                } else {
                    err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::IntType)
                }
            }
            _ => err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::IntType),
        }
    }

    fn lax_int(&self) -> ValResult<i64> {
        match self {
            Value::Bool(b) => match *b {
                true => Ok(1),
                false => Ok(0),
            },
            Value::Number(n) => {
                if let Some(int) = n.as_i64() {
                    Ok(int)
                } else if let Some(float) = n.as_f64() {
                    float_as_int(self, float)
                } else {
                    err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::IntType)
                }
            }
            Value::String(str) => str_as_int(self, str),
            _ => err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::IntType),
        }
    }

    fn strict_float(&self) -> ValResult<f64> {
        match self {
            Value::Number(n) => {
                if let Some(float) = n.as_f64() {
                    Ok(float)
                } else {
                    err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::FloatParsing)
                }
            }
            _ => err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::FloatType),
        }
    }

    fn lax_float(&self) -> ValResult<f64> {
        match self {
            Value::Bool(b) => match *b {
                true => Ok(1.0),
                false => Ok(0.0),
            },
            Value::Number(n) => {
                if let Some(float) = n.as_f64() {
                    Ok(float)
                } else {
                    err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::FloatParsing)
                }
            }
            Value::String(str) => match str.parse() {
                Ok(i) => Ok(i),
                Err(_) => err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::FloatParsing),
            },
            _ => err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::FloatType),
        }
    }

    fn strict_model_check(&self, _class: &PyType) -> ValResult<bool> {
        Ok(false)
    }

    fn strict_dict<'data>(&'data self) -> ValResult<Box<dyn DictInput<'data> + 'data>> {
        match self {
            Value::Object(dict) => Ok(Box::new(dict)),
            _ => err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::DictType),
        }
    }

    fn strict_list<'data>(&'data self) -> ValResult<Box<dyn ListInput<'data> + 'data>> {
        match self {
            Value::Array(a) => Ok(Box::new(a)),
            _ => err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::ListType),
        }
    }

    fn strict_set<'data>(&'data self) -> ValResult<Box<dyn ListInput<'data> + 'data>> {
        // we allow a list here since otherwise it would be impossible to create a set from JSON
        match self {
            Value::Array(a) => Ok(Box::new(a)),
            _ => err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::SetType),
        }
    }
}

impl<'data> DictInput<'data> for &'data Map<String, Value> {
    fn input_iter(&self) -> Box<dyn Iterator<Item = (&'data dyn Input, &'data dyn Input)> + 'data> {
        Box::new(self.iter().map(|(k, v)| (k as &dyn Input, v as &dyn Input)))
    }

    fn input_get(&self, key: &str) -> Option<&'data dyn Input> {
        self.get(key).map(|item| item as &dyn Input)
    }

    fn input_len(&self) -> usize {
        self.len()
    }
}

impl<'data> ListInput<'data> for &'data Vec<Value> {
    fn input_iter(&self) -> Box<dyn Iterator<Item = &'data dyn Input> + 'data> {
        Box::new(self.iter().map(|item| item as &dyn Input))
    }

    fn input_len(&self) -> usize {
        self.len()
    }
}

impl ToPy for Value {
    #[inline]
    fn to_py(&self, py: Python) -> PyObject {
        match self {
            Value::Null => py.None(),
            Value::Bool(b) => b.into_py(py),
            Value::Number(n) => {
                if let Some(int) = n.as_i64() {
                    int.into_py(py)
                } else if let Some(float) = n.as_f64() {
                    float.into_py(py)
                } else {
                    panic!("{:?} is not a valid number", n)
                }
            }
            Value::String(s) => s.into_py(py),
            Value::Array(v) => v.to_py(py),
            Value::Object(m) => m.to_py(py),
        }
    }
}

impl ToPy for &Map<String, Value> {
    #[inline]
    fn to_py(&self, py: Python) -> PyObject {
        let dict = PyDict::new(py);
        for (k, v) in self.iter() {
            dict.set_item(k, v.to_py(py)).unwrap();
        }
        dict.into_py(py)
    }
}
impl ToPy for &Vec<Value> {
    #[inline]
    fn to_py(&self, py: Python) -> PyObject {
        self.iter().map(|v| v.to_py(py)).collect::<Vec<_>>().into_py(py)
    }
}

impl ToLocItem for Value {
    fn to_loc(&self) -> LocItem {
        match self {
            Value::Number(n) => {
                if let Some(int) = n.as_i64() {
                    LocItem::I(int as usize)
                } else if let Some(float) = n.as_f64() {
                    LocItem::I(float as usize)
                } else {
                    // something's gone wrong, best effort
                    LocItem::S(format!("{:?}", n))
                }
            }
            Value::String(s) => LocItem::S(s.to_string()),
            v => LocItem::S(format!("{:?}", v)),
        }
    }
}

impl ToPy for String {
    #[inline]
    fn to_py(&self, py: Python) -> PyObject {
        self.into_py(py)
    }
}

/// Required for Dict keys so the string can behave like an Input
impl Input for String {
    fn is_none(&self) -> bool {
        false
    }

    fn strict_str(&self) -> ValResult<String> {
        Ok(self.clone())
    }

    fn lax_str(&self) -> ValResult<String> {
        Ok(self.clone())
    }

    fn strict_bool(&self) -> ValResult<bool> {
        err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::BoolType)
    }

    fn lax_bool(&self) -> ValResult<bool> {
        str_as_bool(self, self)
    }

    fn strict_int(&self) -> ValResult<i64> {
        err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::IntType)
    }

    fn lax_int(&self) -> ValResult<i64> {
        match self.parse() {
            Ok(i) => Ok(i),
            Err(_) => err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::IntParsing),
        }
    }

    fn strict_float(&self) -> ValResult<f64> {
        err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::FloatType)
    }

    fn lax_float(&self) -> ValResult<f64> {
        match self.parse() {
            Ok(i) => Ok(i),
            Err(_) => err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::FloatParsing),
        }
    }

    fn strict_model_check(&self, _class: &PyType) -> ValResult<bool> {
        Ok(false)
    }

    fn strict_dict<'data>(&'data self) -> ValResult<Box<dyn DictInput<'data> + 'data>> {
        err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::DictType)
    }

    fn strict_list<'data>(&'data self) -> ValResult<Box<dyn ListInput<'data> + 'data>> {
        err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::ListType)
    }

    fn strict_set<'data>(&'data self) -> ValResult<Box<dyn ListInput<'data> + 'data>> {
        err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::SetType)
    }
}
