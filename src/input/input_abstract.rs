use std::fmt;

use pyo3::types::PyType;

use crate::errors::ValResult;
use crate::input::datetime::EitherTime;

use super::datetime::{EitherDate, EitherDateTime};
use super::{GenericMapping, GenericSequence, ToLocItem, ToPy};

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

    fn strict_dict<'data>(&'data self) -> ValResult<GenericMapping<'data>>;

    fn lax_dict<'data>(&'data self, _try_instance: bool) -> ValResult<GenericMapping<'data>> {
        self.strict_dict()
    }

    fn strict_list<'data>(&'data self) -> ValResult<GenericSequence<'data>>;

    fn lax_list<'data>(&'data self) -> ValResult<GenericSequence<'data>> {
        self.strict_list()
    }

    fn strict_set<'data>(&'data self) -> ValResult<GenericSequence<'data>>;

    fn lax_set<'data>(&'data self) -> ValResult<GenericSequence<'data>> {
        self.strict_set()
    }

    fn strict_date(&self) -> ValResult<EitherDate>;

    fn lax_date(&self) -> ValResult<EitherDate> {
        self.strict_date()
    }

    fn strict_time(&self) -> ValResult<EitherTime>;

    fn lax_time(&self) -> ValResult<EitherTime> {
        self.strict_time()
    }

    fn strict_datetime(&self) -> ValResult<EitherDateTime>;

    fn lax_datetime(&self) -> ValResult<EitherDateTime> {
        self.strict_datetime()
    }
}
