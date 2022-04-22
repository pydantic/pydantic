use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyType};
use serde_json::{Map, Value};

use crate::build_macros::py_error;
use crate::errors::{as_internal, err_val_error, ErrorKind, LocItem, ValResult};

use super::shared::{int_as_bool, str_as_bool};
use super::traits::{DictInput, Input, ListInput, ToLocItem, ToPy};

impl Input for Value {
    fn is_none(&self, _py: Python) -> bool {
        matches!(self, Value::Null)
    }

    fn strict_str(&self, py: Python) -> ValResult<String> {
        match self {
            Value::String(s) => Ok(s.to_string()),
            _ => err_val_error!(py, self, kind = ErrorKind::StrType),
        }
    }

    fn lax_str(&self, py: Python) -> ValResult<String> {
        match self {
            Value::String(s) => Ok(s.to_string()),
            Value::Number(n) => Ok(n.to_string()),
            _ => err_val_error!(py, self, kind = ErrorKind::StrType),
        }
    }

    fn strict_bool(&self, py: Python) -> ValResult<bool> {
        match self {
            Value::Bool(b) => Ok(*b),
            _ => err_val_error!(py, self, kind = ErrorKind::BoolType),
        }
    }

    fn lax_bool(&self, py: Python) -> ValResult<bool> {
        match self {
            Value::Bool(b) => Ok(*b),
            Value::String(s) => str_as_bool(py, s),
            Value::Number(n) => {
                if let Some(int) = n.as_i64() {
                    int_as_bool(py, int)
                } else {
                    err_val_error!(py, self, kind = ErrorKind::BoolParsing)
                }
            }
            _ => err_val_error!(py, self, kind = ErrorKind::BoolType),
        }
    }

    fn strict_int(&self, py: Python) -> ValResult<i64> {
        match self {
            Value::Number(n) => {
                if let Some(int) = n.as_i64() {
                    Ok(int)
                } else {
                    err_val_error!(py, self, kind = ErrorKind::IntType)
                }
            }
            _ => err_val_error!(py, self, kind = ErrorKind::IntType),
        }
    }

    fn lax_int(&self, py: Python) -> ValResult<i64> {
        match self {
            Value::Number(n) => {
                if let Some(int) = n.as_i64() {
                    Ok(int)
                } else if let Some(float) = n.as_f64() {
                    if float % 1.0 == 0.0 {
                        Ok(float as i64)
                    } else {
                        err_val_error!(py, float, kind = ErrorKind::IntFromFloat)
                    }
                } else {
                    err_val_error!(py, self, kind = ErrorKind::IntType)
                }
            }
            Value::String(str) => match str.parse() {
                Ok(i) => Ok(i),
                Err(_) => err_val_error!(py, str, kind = ErrorKind::IntParsing),
            },
            _ => err_val_error!(py, self, kind = ErrorKind::IntType),
        }
    }

    fn strict_float(&self, py: Python) -> ValResult<f64> {
        match self {
            Value::Number(n) => {
                if let Some(float) = n.as_f64() {
                    Ok(float)
                } else {
                    err_val_error!(py, self, kind = ErrorKind::FloatParsing)
                }
            }
            _ => err_val_error!(py, self, kind = ErrorKind::FloatType),
        }
    }

    fn lax_float(&self, py: Python) -> ValResult<f64> {
        match self {
            Value::Number(n) => {
                if let Some(float) = n.as_f64() {
                    Ok(float)
                } else {
                    err_val_error!(py, self, kind = ErrorKind::FloatParsing)
                }
            }
            Value::String(str) => match str.parse() {
                Ok(i) => Ok(i),
                Err(_) => err_val_error!(py, str, kind = ErrorKind::FloatParsing),
            },
            _ => err_val_error!(py, self, kind = ErrorKind::FloatType),
        }
    }

    fn strict_model_check(&self, _class: &PyType) -> ValResult<bool> {
        Ok(false)
    }

    fn strict_dict<'py>(&'py self, py: Python<'py>) -> ValResult<Box<dyn DictInput<'py> + 'py>> {
        match self {
            Value::Object(dict) => Ok(Box::new(dict)),
            _ => err_val_error!(py, self, kind = ErrorKind::DictType),
        }
    }

    fn lax_dict<'py>(&'py self, py: Python<'py>, _try_instance: bool) -> ValResult<Box<dyn DictInput<'py> + 'py>> {
        self.strict_dict(py)
    }

    fn strict_list<'py>(&'py self, py: Python<'py>) -> ValResult<Box<dyn ListInput<'py> + 'py>> {
        match self {
            Value::Array(a) => Ok(Box::new(a)),
            _ => err_val_error!(py, self, kind = ErrorKind::ListType),
        }
    }

    fn lax_list<'py>(&'py self, py: Python<'py>) -> ValResult<Box<dyn ListInput<'py> + 'py>> {
        self.strict_list(py)
    }
}

impl<'py> DictInput<'py> for &'py Map<String, Value> {
    fn input_iter(&self) -> Box<dyn Iterator<Item = (&dyn Input, &dyn Input)> + '_> {
        Box::new(self.iter().map(|(k, v)| (k as &dyn Input, v as &dyn Input)))
    }

    fn input_get(&self, key: &str) -> Option<&dyn Input> {
        self.get(key).map(|item| item as &dyn Input)
    }

    fn input_len(&self) -> usize {
        self.len()
    }
}

impl<'py> ListInput<'py> for &Vec<Value> {
    fn input_iter(&self) -> Box<dyn Iterator<Item = &dyn Input> + '_> {
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
            Value::String(s) => s.clone().into_py(py),
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
    fn to_loc(&self) -> ValResult<LocItem> {
        match self {
            Value::Number(n) => {
                if let Some(int) = n.as_i64() {
                    Ok(LocItem::I(int as usize))
                } else if let Some(float) = n.as_f64() {
                    Ok(LocItem::I(float as usize))
                } else {
                    py_error!(PyValueError; "{:?} is not a valid number", n).map_err(as_internal)
                }
            }
            Value::String(s) => Ok(LocItem::S(s.to_string())),
            v => Ok(LocItem::S(format!("{:?}", v))),
        }
    }
}

/// Required for Dict keys so the string can behave like an Input
impl Input for String {
    fn is_none(&self, _py: Python) -> bool {
        false
    }

    fn strict_str(&self, _py: Python) -> ValResult<String> {
        Ok(self.clone())
    }

    fn lax_str(&self, _py: Python) -> ValResult<String> {
        Ok(self.clone())
    }

    fn strict_bool(&self, py: Python) -> ValResult<bool> {
        err_val_error!(py, self, kind = ErrorKind::BoolType)
    }

    fn lax_bool(&self, py: Python) -> ValResult<bool> {
        str_as_bool(py, self)
    }

    fn strict_int(&self, py: Python) -> ValResult<i64> {
        err_val_error!(py, self, kind = ErrorKind::IntType)
    }

    fn lax_int(&self, py: Python) -> ValResult<i64> {
        match self.parse() {
            Ok(i) => Ok(i),
            Err(_) => err_val_error!(py, self, kind = ErrorKind::IntParsing),
        }
    }

    fn strict_float(&self, py: Python) -> ValResult<f64> {
        err_val_error!(py, self, kind = ErrorKind::FloatType)
    }

    fn lax_float(&self, py: Python) -> ValResult<f64> {
        match self.parse() {
            Ok(i) => Ok(i),
            Err(_) => err_val_error!(py, self, kind = ErrorKind::FloatParsing),
        }
    }

    fn strict_model_check(&self, _class: &PyType) -> ValResult<bool> {
        Ok(false)
    }

    fn strict_dict<'py>(&'py self, py: Python<'py>) -> ValResult<Box<dyn DictInput<'py> + 'py>> {
        err_val_error!(py, self, kind = ErrorKind::DictType)
    }

    fn lax_dict<'py>(&'py self, py: Python<'py>, _try_instance: bool) -> ValResult<Box<dyn DictInput<'py> + 'py>> {
        err_val_error!(py, self, kind = ErrorKind::DictType)
    }

    fn strict_list<'py>(&'py self, py: Python<'py>) -> ValResult<Box<dyn ListInput<'py> + 'py>> {
        err_val_error!(py, self, kind = ErrorKind::ListType)
    }

    fn lax_list<'py>(&'py self, py: Python<'py>) -> ValResult<Box<dyn ListInput<'py> + 'py>> {
        err_val_error!(py, self, kind = ErrorKind::ListType)
    }
}
