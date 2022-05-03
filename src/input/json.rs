use pyo3::prelude::*;
use pyo3::types::{PyDict, PyType};

use crate::errors::{err_val_error, ErrorKind, InputValue, LocItem, ValResult};

use super::parse_json::{JsonArray, JsonInput, JsonObject};
use super::shared::{float_as_int, int_as_bool, str_as_bool, str_as_int};
use super::traits::{DictInput, Input, ListInput, ToLocItem, ToPy};

impl Input for JsonInput {
    fn is_none(&self) -> bool {
        matches!(self, JsonInput::Null)
    }

    fn strict_str(&self) -> ValResult<String> {
        match self {
            JsonInput::String(s) => Ok(s.to_string()),
            _ => err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::StrType),
        }
    }

    fn lax_str(&self) -> ValResult<String> {
        match self {
            JsonInput::String(s) => Ok(s.to_string()),
            JsonInput::Int(int) => Ok(int.to_string()),
            JsonInput::Float(float) => Ok(float.to_string()),
            _ => err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::StrType),
        }
    }

    fn strict_bool(&self) -> ValResult<bool> {
        match self {
            JsonInput::Bool(b) => Ok(*b),
            _ => err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::BoolType),
        }
    }

    fn lax_bool(&self) -> ValResult<bool> {
        match self {
            JsonInput::Bool(b) => Ok(*b),
            JsonInput::String(s) => str_as_bool(self, s),
            JsonInput::Int(int) => int_as_bool(self, *int),
            // TODO float??
            _ => err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::BoolType),
        }
    }

    fn strict_int(&self) -> ValResult<i64> {
        match self {
            JsonInput::Int(i) => Ok(*i),
            _ => err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::IntType),
        }
    }

    fn lax_int(&self) -> ValResult<i64> {
        match self {
            JsonInput::Bool(b) => match *b {
                true => Ok(1),
                false => Ok(0),
            },
            JsonInput::Int(i) => Ok(*i),
            JsonInput::Float(f) => float_as_int(self, *f),
            JsonInput::String(str) => str_as_int(self, str),
            _ => err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::IntType),
        }
    }

    fn strict_float(&self) -> ValResult<f64> {
        match self {
            JsonInput::Float(f) => Ok(*f),
            JsonInput::Int(i) => Ok(*i as f64),
            _ => err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::FloatType),
        }
    }

    fn lax_float(&self) -> ValResult<f64> {
        match self {
            JsonInput::Bool(b) => match *b {
                true => Ok(1.0),
                false => Ok(0.0),
            },
            JsonInput::Float(f) => Ok(*f),
            JsonInput::Int(i) => Ok(*i as f64),
            JsonInput::String(str) => match str.parse() {
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
            JsonInput::Object(dict) => Ok(Box::new(dict)),
            _ => err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::DictType),
        }
    }

    fn strict_list<'data>(&'data self) -> ValResult<Box<dyn ListInput<'data> + 'data>> {
        match self {
            JsonInput::Array(a) => Ok(Box::new(a)),
            _ => err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::ListType),
        }
    }

    fn strict_set<'data>(&'data self) -> ValResult<Box<dyn ListInput<'data> + 'data>> {
        // we allow a list here since otherwise it would be impossible to create a set from JSON
        match self {
            JsonInput::Array(a) => Ok(Box::new(a)),
            _ => err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::SetType),
        }
    }
}

impl ToPy for &JsonArray {
    #[inline]
    fn to_py(&self, py: Python) -> PyObject {
        self.iter().map(|v| v.to_py(py)).collect::<Vec<_>>().into_py(py)
    }
}

impl<'data> ListInput<'data> for &'data JsonArray {
    fn input_iter(&self) -> Box<dyn Iterator<Item = &'data dyn Input> + 'data> {
        Box::new(self.iter().map(|item| item as &dyn Input))
    }

    fn input_len(&self) -> usize {
        self.len()
    }
}

impl ToPy for &JsonObject {
    #[inline]
    fn to_py(&self, py: Python) -> PyObject {
        let dict = PyDict::new(py);
        for (k, v) in self.iter() {
            dict.set_item(k, v.to_py(py)).unwrap();
        }
        dict.into_py(py)
    }
}

impl<'data> DictInput<'data> for &'data JsonObject {
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

impl ToPy for JsonInput {
    fn to_py(&self, py: Python) -> PyObject {
        match self {
            JsonInput::Null => py.None(),
            JsonInput::Bool(b) => b.into_py(py),
            JsonInput::Int(i) => i.into_py(py),
            JsonInput::Float(f) => f.into_py(py),
            JsonInput::String(s) => s.into_py(py),
            JsonInput::Array(v) => v.to_py(py),
            JsonInput::Object(o) => o.to_py(py),
        }
    }
}

impl ToLocItem for JsonInput {
    fn to_loc(&self) -> LocItem {
        match self {
            JsonInput::Int(i) => LocItem::I(*i as usize),
            JsonInput::String(s) => LocItem::S(s.to_string()),
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
