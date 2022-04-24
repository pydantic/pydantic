use std::str::from_utf8;

use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict, PyInt, PyList, PyMapping, PyString, PyTuple, PyType};

use crate::errors::{as_internal, err_val_error, ErrorKind, InputValue, LocItem, ValResult};

use super::shared::{int_as_bool, str_as_bool};
use super::traits::{DictInput, Input, ListInput, ToLocItem, ToPy};

impl Input for PyAny {
    fn is_none(&self, _py: Python) -> bool {
        self.is_none()
    }

    fn strict_str(&self, _py: Python) -> ValResult<String> {
        if let Ok(py_str) = self.cast_as::<PyString>() {
            py_str.extract().map_err(as_internal)
        } else {
            err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::StrType)
        }
    }

    fn lax_str(&self, _py: Python) -> ValResult<String> {
        if let Ok(py_str) = self.cast_as::<PyString>() {
            py_str.extract().map_err(as_internal)
        } else if let Ok(bytes) = self.cast_as::<PyBytes>() {
            let str = match from_utf8(bytes.as_bytes()) {
                Ok(s) => s.to_string(),
                Err(_) => {
                    return err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::StrUnicode)
                }
            };
            Ok(str)
        } else if self.extract::<bool>().is_ok() {
            // do this before int and float parsing as `False` is cast to `0` and we don't want False to
            // be returned as a string
            err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::StrType)
        } else if let Ok(int) = self.cast_as::<PyInt>() {
            let int = i64::extract(int).map_err(as_internal)?;
            Ok(int.to_string())
        } else if let Ok(float) = f64::extract(self) {
            // don't cast_as here so Decimals are covered - internally f64:extract uses PyFloat_AsDouble
            Ok(float.to_string())
        } else {
            err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::StrType)
        }
    }

    fn strict_bool(&self, _py: Python) -> ValResult<bool> {
        if let Ok(bool) = self.extract::<bool>() {
            Ok(bool)
        } else {
            err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::BoolType)
        }
    }

    fn lax_bool(&self, _py: Python) -> ValResult<bool> {
        if let Ok(bool) = self.extract::<bool>() {
            Ok(bool)
        } else if let Some(str) = _maybe_as_string(self, ErrorKind::BoolParsing)? {
            str_as_bool(self, &str)
        } else if let Ok(int) = self.extract::<i64>() {
            int_as_bool(self, int)
        } else {
            err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::BoolType)
        }
    }

    fn strict_int(&self, _py: Python) -> ValResult<i64> {
        // bool check has to come before int check as bools would be cast to ints below
        if self.extract::<bool>().is_ok() {
            err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::IntType)
        } else if let Ok(int) = self.extract::<i64>() {
            Ok(int)
        } else {
            err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::IntType)
        }
    }

    fn lax_int<'a>(&'a self, py: Python<'a>) -> ValResult<'a, i64> {
        if let Ok(int) = self.extract::<i64>() {
            Ok(int)
        } else if let Some(str) = _maybe_as_string(self, ErrorKind::IntParsing)? {
            match str.parse() {
                Ok(i) => Ok(i),
                Err(_) => err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::IntParsing),
            }
        } else if let Ok(float) = self.lax_float(py) {
            if float % 1.0 == 0.0 {
                Ok(float as i64)
            } else {
                err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::IntFromFloat)
            }
        } else {
            err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::IntType)
        }
    }

    fn strict_float(&self, _py: Python) -> ValResult<f64> {
        if let Ok(int) = self.extract::<f64>() {
            Ok(int)
        } else {
            err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::FloatType)
        }
    }

    fn lax_float<'a>(&'a self, _py: Python<'a>) -> ValResult<'a, f64> {
        if let Ok(int) = self.extract::<f64>() {
            Ok(int)
        } else if let Some(str) = _maybe_as_string(self, ErrorKind::FloatParsing)? {
            match str.parse() {
                Ok(i) => Ok(i),
                Err(_) => err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::FloatParsing),
            }
        } else {
            err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::FloatType)
        }
    }

    fn strict_model_check(&self, class: &PyType) -> ValResult<bool> {
        self.get_type().eq(class).map_err(as_internal)
    }

    fn strict_dict<'py>(&'py self, _py: Python<'py>) -> ValResult<Box<dyn DictInput<'py> + 'py>> {
        if let Ok(dict) = self.cast_as::<PyDict>() {
            Ok(Box::new(dict))
        } else {
            err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::DictType)
        }
    }

    fn lax_dict<'py>(&'py self, py: Python<'py>, try_instance: bool) -> ValResult<Box<dyn DictInput<'py> + 'py>> {
        if let Ok(dict) = self.cast_as::<PyDict>() {
            Ok(Box::new(dict))
        } else if let Ok(mapping) = self.cast_as::<PyMapping>() {
            // this is ugly, but we'd have to do it in `input_iter` anyway
            // we could perhaps use an indexmap instead of a python dict?
            let dict = match mapping_as_dict(py, mapping) {
                Ok(dict) => dict,
                Err(err) => {
                    return err_val_error!(
                        input_value = InputValue::InputRef(self),
                        message = Some(err.to_string()),
                        kind = ErrorKind::DictFromMapping
                    )
                }
            };
            Ok(Box::new(dict))
        } else if try_instance {
            let inner_dict = match instance_as_dict(py, self) {
                Ok(dict) => dict,
                Err(err) => {
                    return err_val_error!(
                        input_value = InputValue::InputRef(self),
                        message = Some(err.to_string()),
                        kind = ErrorKind::DictFromObject
                    )
                }
            };
            inner_dict.lax_dict(py, false)
        } else {
            err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::DictType)
        }
    }

    fn strict_list<'py>(&'py self, _py: Python<'py>) -> ValResult<Box<dyn ListInput + 'py>> {
        if let Ok(list) = self.cast_as::<PyList>() {
            Ok(Box::new(list))
        } else {
            err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::ListType)
        }
    }

    fn lax_list<'py>(&'py self, _py: Python<'py>) -> ValResult<Box<dyn ListInput + 'py>> {
        if let Ok(list) = self.cast_as::<PyList>() {
            Ok(Box::new(list))
            // TODO support sets, tuples, frozen set etc. like in pydantic
        } else {
            err_val_error!(input_value = InputValue::InputRef(self), kind = ErrorKind::ListType)
        }
    }
}

fn mapping_as_dict<'py>(py: Python<'py>, mapping: &'py PyMapping) -> PyResult<&'py PyDict> {
    let seq = mapping.items()?;
    let dict = PyDict::new(py);
    for r in seq.iter()? {
        let t: &PyTuple = r?.extract()?;
        let k = t.get_item(0)?;
        let v = t.get_item(1)?;
        dict.set_item(k, v)?;
    }
    Ok(dict)
}

/// This is equivalent to `GetterDict` in pydantic v1
fn instance_as_dict<'py>(py: Python<'py>, instance: &'py PyAny) -> PyResult<&'py PyDict> {
    let dict = PyDict::new(py);
    for k_any in instance.dir() {
        let k_str: &str = k_any.extract()?;
        if !k_str.starts_with('_') {
            let v = instance.getattr(k_any)?;
            dict.set_item(k_any, v)?;
        }
    }
    Ok(dict)
}

impl<'py> DictInput<'py> for &'py PyDict {
    fn input_iter(&self) -> Box<dyn Iterator<Item = (&'py dyn Input, &'py dyn Input)> + 'py> {
        Box::new(self.iter().map(|(k, v)| (k as &dyn Input, v as &dyn Input)))
    }

    fn input_get(&self, key: &str) -> Option<&'py dyn Input> {
        self.get_item(key).map(|item| item as &dyn Input)
    }

    fn input_len(&self) -> usize {
        self.len()
    }
}

impl<'py> ListInput<'py> for &'py PyList {
    fn input_iter(&self) -> Box<dyn Iterator<Item = &'py dyn Input> + 'py> {
        Box::new(self.iter().map(|item| item as &dyn Input))
    }

    fn input_len(&self) -> usize {
        self.len()
    }
}

/// Utility for extracting a string from a PyAny, if possible.
fn _maybe_as_string(v: &PyAny, unicode_error: ErrorKind) -> ValResult<Option<String>> {
    if let Ok(str) = v.extract::<String>() {
        Ok(Some(str))
    } else if let Ok(bytes) = v.cast_as::<PyBytes>() {
        let str = match from_utf8(bytes.as_bytes()) {
            Ok(s) => s.to_string(),
            Err(_) => return err_val_error!(input_value = InputValue::InputRef(v), kind = unicode_error),
        };
        Ok(Some(str))
    } else {
        Ok(None)
    }
}

impl ToPy for PyAny {
    #[inline]
    fn to_py(&self, py: Python) -> PyObject {
        self.into_py(py)
    }
}

impl ToPy for &PyDict {
    #[inline]
    fn to_py(&self, py: Python) -> PyObject {
        self.into_py(py)
    }
}

impl ToPy for &PyList {
    #[inline]
    fn to_py(&self, py: Python) -> PyObject {
        self.into_py(py)
    }
}

impl ToLocItem for PyAny {
    fn to_loc(&self) -> LocItem {
        if let Ok(key_str) = self.extract::<String>() {
            LocItem::S(key_str)
        } else if let Ok(key_int) = self.extract::<usize>() {
            LocItem::I(key_int)
        } else {
            // best effort is to use repr
            match repr_string(self) {
                Ok(s) => LocItem::S(s),
                Err(_) => LocItem::S(format!("{:?}", self)),
            }
        }
    }
}

fn repr_string(py_any: &PyAny) -> PyResult<String> {
    let repr_result = py_any.repr()?;
    let repr: String = repr_result.extract()?;
    Ok(repr)
}
