use std::fmt;

use pyo3::types::PyType;
use pyo3::ToPyObject;

use crate::errors::location::LocItem;
use crate::errors::{InputValue, ValResult};
use crate::input::datetime::EitherTime;

use super::datetime::{EitherDate, EitherDateTime};
use super::return_enums::{EitherBytes, EitherString};
use super::{GenericMapping, GenericSequence};

pub trait Input<'a>: fmt::Debug + ToPyObject {
    fn as_loc_item(&'a self) -> LocItem;

    fn as_error_value(&'a self) -> InputValue<'a>;

    fn is_none(&self) -> bool;

    fn strict_str<'data>(&'data self) -> ValResult<EitherString<'data>>;

    fn lax_str<'data>(&'data self) -> ValResult<EitherString<'data>> {
        self.strict_str()
    }

    fn strict_bool(&self) -> ValResult<bool>;

    fn lax_bool(&self) -> ValResult<bool>;

    fn strict_int(&self) -> ValResult<i64>;

    fn lax_int(&self) -> ValResult<i64>;

    fn strict_float(&self) -> ValResult<f64>;

    fn lax_float(&self) -> ValResult<f64>;

    fn strict_model_check(&self, class: &PyType) -> ValResult<bool>;

    fn strict_dict<'data>(&'data self) -> ValResult<GenericMapping<'data>>;

    fn lax_dict<'data>(&'data self) -> ValResult<GenericMapping<'data>> {
        self.strict_dict()
    }

    fn typed_dict<'data>(&'data self, _from_attributes: bool, _from_mapping: bool) -> ValResult<GenericMapping<'data>> {
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

    fn strict_frozenset<'data>(&'data self) -> ValResult<GenericSequence<'data>>;

    fn lax_frozenset<'data>(&'data self) -> ValResult<GenericSequence<'data>> {
        self.strict_frozenset()
    }

    fn strict_bytes<'data>(&'data self) -> ValResult<EitherBytes<'data>>;

    fn lax_bytes<'data>(&'data self) -> ValResult<EitherBytes<'data>> {
        self.strict_bytes()
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

    fn strict_tuple<'data>(&'data self) -> ValResult<GenericSequence<'data>>;

    fn lax_tuple<'data>(&'data self) -> ValResult<GenericSequence<'data>> {
        self.strict_tuple()
    }
}
