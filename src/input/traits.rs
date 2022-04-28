use std::fmt;
use std::fmt::Debug;

use pyo3::prelude::*;
use pyo3::types::PyType;

use crate::errors::{LocItem, ValResult};

pub trait ToPy: Debug {
    fn to_py(&self, py: Python) -> PyObject;
}

pub trait ToLocItem {
    fn to_loc(&self) -> LocItem;
}

impl ToLocItem for String {
    fn to_loc(&self) -> LocItem {
        LocItem::S(self.clone())
    }
}

impl ToLocItem for &str {
    fn to_loc(&self) -> LocItem {
        LocItem::S(self.to_string())
    }
}

pub trait Input: fmt::Debug + ToPy + ToLocItem {
    fn is_none(&self, py: Python) -> bool;

    fn strict_str(&self, py: Python) -> ValResult<String>;

    fn lax_str(&self, py: Python) -> ValResult<String>;

    fn strict_bool(&self, py: Python) -> ValResult<bool>;

    fn lax_bool(&self, py: Python) -> ValResult<bool>;

    fn strict_int(&self, py: Python) -> ValResult<i64>;

    fn lax_int(&self, py: Python) -> ValResult<i64>;

    fn strict_float(&self, py: Python) -> ValResult<f64>;

    fn lax_float(&self, py: Python) -> ValResult<f64>;

    fn strict_model_check(&self, class: &PyType) -> ValResult<bool>;

    fn strict_dict<'data>(&'data self, py: Python<'data>) -> ValResult<Box<dyn DictInput<'data> + 'data>>;

    fn lax_dict<'data>(
        &'data self,
        py: Python<'data>,
        try_instance: bool,
    ) -> ValResult<Box<dyn DictInput<'data> + 'data>>;

    fn strict_list<'data>(&'data self, py: Python<'data>) -> ValResult<Box<dyn ListInput<'data> + 'data>>;

    fn lax_list<'data>(&'data self, py: Python<'data>) -> ValResult<Box<dyn ListInput<'data> + 'data>>;
}

// these are ugly, is there any way to avoid the maps in iter, one of the boxes and/or the duplication?
// is this harming performance, particularly the .map(|item| item)?
// https://stackoverflow.com/a/47156134/949890
pub trait DictInput<'data>: ToPy {
    fn input_iter(&self) -> Box<dyn Iterator<Item = (&'data dyn Input, &'data dyn Input)> + 'data>;

    fn input_get(&self, key: &str) -> Option<&'data dyn Input>;

    fn input_len(&self) -> usize;
}

pub trait ListInput<'data>: ToPy {
    fn input_iter(&self) -> Box<dyn Iterator<Item = &'data dyn Input> + 'data>;

    fn input_len(&self) -> usize;
}
