use std::fmt;

use pyo3::types::{PyDict, PyType};
use pyo3::{intern, prelude::*};

use crate::errors::{InputValue, LocItem, ValResult};
use crate::{PyMultiHostUrl, PyUrl};

use super::datetime::{EitherDate, EitherDateTime, EitherTime, EitherTimedelta};
use super::return_enums::{EitherBytes, EitherInt, EitherString};
use super::{EitherFloat, GenericArguments, GenericIterable, GenericIterator, GenericMapping, JsonInput};

#[derive(Debug, Clone, Copy)]
pub enum InputType {
    Python,
    Json,
}

impl IntoPy<PyObject> for InputType {
    fn into_py(self, py: Python<'_>) -> PyObject {
        match self {
            Self::Json => intern!(py, "json").into(),
            Self::Python => intern!(py, "python").into(),
        }
    }
}

/// all types have three methods: `validate_*`, `strict_*`, `lax_*`
/// the convention is to either implement:
/// * `strict_*` & `lax_*` if they have different behavior
/// * or, `validate_*` and `strict_*` to just call `validate_*` if the behavior for strict and lax is the same
pub trait Input<'a>: fmt::Debug + ToPyObject {
    fn as_loc_item(&self) -> LocItem;

    fn as_error_value(&'a self) -> InputValue<'a>;

    fn identity(&self) -> Option<usize> {
        None
    }

    fn is_none(&self) -> bool;

    fn input_is_instance(&self, _class: &PyType) -> Option<&PyAny> {
        None
    }

    fn is_python(&self) -> bool {
        false
    }

    fn as_kwargs(&'a self, py: Python<'a>) -> Option<&'a PyDict>;

    fn input_is_subclass(&self, _class: &PyType) -> PyResult<bool> {
        Ok(false)
    }

    fn input_as_url(&self) -> Option<PyUrl> {
        None
    }

    fn input_as_multi_host_url(&self) -> Option<PyMultiHostUrl> {
        None
    }

    fn callable(&self) -> bool {
        false
    }

    fn validate_args(&'a self) -> ValResult<'a, GenericArguments<'a>>;

    fn validate_dataclass_args(&'a self, dataclass_name: &str) -> ValResult<'a, GenericArguments<'a>>;

    fn parse_json(&'a self) -> ValResult<'a, JsonInput>;

    fn validate_str(&'a self, strict: bool) -> ValResult<EitherString<'a>> {
        if strict {
            self.strict_str()
        } else {
            self.lax_str()
        }
    }
    fn strict_str(&'a self) -> ValResult<EitherString<'a>>;
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn lax_str(&'a self) -> ValResult<EitherString<'a>> {
        self.strict_str()
    }

    fn validate_bytes(&'a self, strict: bool) -> ValResult<EitherBytes<'a>> {
        if strict {
            self.strict_bytes()
        } else {
            self.lax_bytes()
        }
    }
    fn strict_bytes(&'a self) -> ValResult<EitherBytes<'a>>;
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn lax_bytes(&'a self) -> ValResult<EitherBytes<'a>> {
        self.strict_bytes()
    }

    fn validate_bool(&self, strict: bool) -> ValResult<bool> {
        if strict {
            self.strict_bool()
        } else {
            self.lax_bool()
        }
    }
    fn strict_bool(&self) -> ValResult<bool>;
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn lax_bool(&self) -> ValResult<bool> {
        self.strict_bool()
    }

    fn validate_int(&'a self, strict: bool) -> ValResult<EitherInt<'a>> {
        if strict {
            self.strict_int()
        } else {
            self.lax_int()
        }
    }
    fn strict_int(&'a self) -> ValResult<EitherInt<'a>>;
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn lax_int(&'a self) -> ValResult<EitherInt<'a>> {
        self.strict_int()
    }

    /// Extract an EitherInt from the input, only allowing exact
    /// matches for an Int (no subclasses)
    fn exact_int(&'a self) -> ValResult<EitherInt<'a>> {
        self.strict_int()
    }

    /// Extract a String from the input, only allowing exact
    /// matches for a String (no subclasses)
    fn exact_str(&'a self) -> ValResult<EitherString<'a>> {
        self.strict_str()
    }

    fn validate_float(&'a self, strict: bool, ultra_strict: bool) -> ValResult<EitherFloat<'a>> {
        if ultra_strict {
            self.ultra_strict_float()
        } else if strict {
            self.strict_float()
        } else {
            self.lax_float()
        }
    }
    fn ultra_strict_float(&'a self) -> ValResult<EitherFloat<'a>>;
    fn strict_float(&'a self) -> ValResult<EitherFloat<'a>>;
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn lax_float(&'a self) -> ValResult<EitherFloat<'a>> {
        self.strict_float()
    }

    fn validate_dict(&'a self, strict: bool) -> ValResult<GenericMapping<'a>> {
        if strict {
            self.strict_dict()
        } else {
            self.lax_dict()
        }
    }
    fn strict_dict(&'a self) -> ValResult<GenericMapping<'a>>;
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn lax_dict(&'a self) -> ValResult<GenericMapping<'a>> {
        self.strict_dict()
    }

    fn validate_model_fields(&'a self, strict: bool, _from_attributes: bool) -> ValResult<GenericMapping<'a>> {
        self.validate_dict(strict)
    }

    fn validate_list(&'a self, strict: bool) -> ValResult<GenericIterable<'a>> {
        if strict {
            self.strict_list()
        } else {
            self.lax_list()
        }
    }
    fn strict_list(&'a self) -> ValResult<GenericIterable<'a>>;
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn lax_list(&'a self) -> ValResult<GenericIterable<'a>> {
        self.strict_list()
    }

    fn validate_tuple(&'a self, strict: bool) -> ValResult<GenericIterable<'a>> {
        if strict {
            self.strict_tuple()
        } else {
            self.lax_tuple()
        }
    }
    fn strict_tuple(&'a self) -> ValResult<GenericIterable<'a>>;
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn lax_tuple(&'a self) -> ValResult<GenericIterable<'a>> {
        self.strict_tuple()
    }

    fn validate_set(&'a self, strict: bool) -> ValResult<GenericIterable<'a>> {
        if strict {
            self.strict_set()
        } else {
            self.lax_set()
        }
    }
    fn strict_set(&'a self) -> ValResult<GenericIterable<'a>>;
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn lax_set(&'a self) -> ValResult<GenericIterable<'a>> {
        self.strict_set()
    }

    fn validate_frozenset(&'a self, strict: bool) -> ValResult<GenericIterable<'a>> {
        if strict {
            self.strict_frozenset()
        } else {
            self.lax_frozenset()
        }
    }
    fn strict_frozenset(&'a self) -> ValResult<GenericIterable<'a>>;
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn lax_frozenset(&'a self) -> ValResult<GenericIterable<'a>> {
        self.strict_frozenset()
    }

    fn extract_generic_iterable(&'a self) -> ValResult<GenericIterable<'a>>;

    fn validate_iter(&self) -> ValResult<GenericIterator>;

    fn validate_date(&self, strict: bool) -> ValResult<EitherDate> {
        if strict {
            self.strict_date()
        } else {
            self.lax_date()
        }
    }
    fn strict_date(&self) -> ValResult<EitherDate>;
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn lax_date(&self) -> ValResult<EitherDate> {
        self.strict_date()
    }

    fn validate_time(
        &self,
        strict: bool,
        microseconds_overflow_behavior: speedate::MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<EitherTime> {
        if strict {
            self.strict_time(microseconds_overflow_behavior)
        } else {
            self.lax_time(microseconds_overflow_behavior)
        }
    }
    fn strict_time(
        &self,
        microseconds_overflow_behavior: speedate::MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<EitherTime>;
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn lax_time(
        &self,
        microseconds_overflow_behavior: speedate::MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<EitherTime> {
        self.strict_time(microseconds_overflow_behavior)
    }

    fn validate_datetime(
        &self,
        strict: bool,
        microseconds_overflow_behavior: speedate::MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<EitherDateTime> {
        if strict {
            self.strict_datetime(microseconds_overflow_behavior)
        } else {
            self.lax_datetime(microseconds_overflow_behavior)
        }
    }
    fn strict_datetime(
        &self,
        microseconds_overflow_behavior: speedate::MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<EitherDateTime>;
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn lax_datetime(
        &self,
        microseconds_overflow_behavior: speedate::MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<EitherDateTime> {
        self.strict_datetime(microseconds_overflow_behavior)
    }

    fn validate_timedelta(
        &self,
        strict: bool,
        microseconds_overflow_behavior: speedate::MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<EitherTimedelta> {
        if strict {
            self.strict_timedelta(microseconds_overflow_behavior)
        } else {
            self.lax_timedelta(microseconds_overflow_behavior)
        }
    }
    fn strict_timedelta(
        &self,
        microseconds_overflow_behavior: speedate::MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<EitherTimedelta>;
    #[cfg_attr(has_no_coverage, no_coverage)]
    fn lax_timedelta(
        &self,
        microseconds_overflow_behavior: speedate::MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<EitherTimedelta> {
        self.strict_timedelta(microseconds_overflow_behavior)
    }
}
