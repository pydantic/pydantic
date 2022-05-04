use std::fmt;

use pyo3::types::PyType;

use crate::errors::ValResult;

use super::{DictInput, ListInput, ToLocItem, ToPy};

pub trait Input: fmt::Debug + ToPy + ToLocItem {
    fn is_none(&self) -> bool;

    fn strict_str(&self) -> ValResult<String>;

    fn lax_str(&self) -> ValResult<String>;

    fn strict_bool(&self) -> ValResult<bool>;

    fn lax_bool(&self) -> ValResult<bool>;

    fn strict_int(&self) -> ValResult<i64>;

    fn lax_int(&self) -> ValResult<i64>;

    fn strict_float(&self) -> ValResult<f64>;

    fn lax_float(&self) -> ValResult<f64>;

    fn strict_model_check(&self, class: &PyType) -> ValResult<bool>;

    fn strict_dict<'data>(&'data self) -> ValResult<Box<dyn DictInput<'data> + 'data>>;

    fn lax_dict<'data>(&'data self, _try_instance: bool) -> ValResult<Box<dyn DictInput<'data> + 'data>> {
        self.strict_dict()
    }

    fn strict_list<'data>(&'data self) -> ValResult<Box<dyn ListInput<'data> + 'data>>;

    fn lax_list<'data>(&'data self) -> ValResult<Box<dyn ListInput<'data> + 'data>> {
        self.strict_list()
    }

    fn strict_set<'data>(&'data self) -> ValResult<Box<dyn ListInput<'data> + 'data>>;

    fn lax_set<'data>(&'data self) -> ValResult<Box<dyn ListInput<'data> + 'data>> {
        self.strict_set()
    }
}
