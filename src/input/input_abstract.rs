use std::fmt;

use pyo3::exceptions::PyValueError;
use pyo3::types::{PyDict, PyType};
use pyo3::{intern, prelude::*};

use jiter::JsonValue;

use crate::errors::{AsLocItem, ErrorTypeDefaults, InputValue, ValError, ValResult};
use crate::tools::py_err;
use crate::{PyMultiHostUrl, PyUrl};

use super::datetime::{EitherDate, EitherDateTime, EitherTime, EitherTimedelta};
use super::return_enums::{EitherBytes, EitherInt, EitherString};
use super::{EitherFloat, GenericArguments, GenericIterable, GenericIterator, GenericMapping, ValidationMatch};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum InputType {
    Python,
    Json,
    String,
}

impl IntoPy<PyObject> for InputType {
    fn into_py(self, py: Python<'_>) -> PyObject {
        match self {
            Self::Json => intern!(py, "json").into(),
            Self::Python => intern!(py, "python").into(),
            Self::String => intern!(py, "string").into(),
        }
    }
}

impl TryFrom<&str> for InputType {
    type Error = PyErr;

    fn try_from(error_mode: &str) -> PyResult<Self> {
        match error_mode {
            "python" => Ok(Self::Python),
            "json" => Ok(Self::Json),
            "string" => Ok(Self::String),
            s => py_err!(PyValueError; "Invalid error mode: {}", s),
        }
    }
}

/// all types have three methods: `validate_*`, `strict_*`, `lax_*`
/// the convention is to either implement:
/// * `strict_*` & `lax_*` if they have different behavior
/// * or, `validate_*` and `strict_*` to just call `validate_*` if the behavior for strict and lax is the same
pub trait Input<'a>: fmt::Debug + ToPyObject + AsLocItem + Sized {
    fn as_error_value(&'a self) -> InputValue<'a>;

    fn identity(&self) -> Option<usize> {
        None
    }

    fn is_none(&self) -> bool {
        false
    }

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

    fn parse_json(&'a self) -> ValResult<'a, JsonValue>;

    fn validate_str(
        &'a self,
        strict: bool,
        coerce_numbers_to_str: bool,
    ) -> ValResult<ValidationMatch<EitherString<'a>>>;

    fn validate_bytes(&'a self, strict: bool) -> ValResult<ValidationMatch<EitherBytes<'a>>>;

    fn validate_bool(&self, strict: bool) -> ValResult<'_, ValidationMatch<bool>>;

    fn validate_int(&'a self, strict: bool) -> ValResult<'a, ValidationMatch<EitherInt<'a>>>;

    fn exact_int(&'a self) -> ValResult<EitherInt<'a>> {
        self.validate_int(true).and_then(|val_match| {
            val_match
                .require_exact()
                .ok_or_else(|| ValError::new(ErrorTypeDefaults::IntType, self))
        })
    }

    /// Extract a String from the input, only allowing exact
    /// matches for a String (no subclasses)
    fn exact_str(&'a self) -> ValResult<EitherString<'a>> {
        self.validate_str(true, false).and_then(|val_match| {
            val_match
                .require_exact()
                .ok_or_else(|| ValError::new(ErrorTypeDefaults::StringType, self))
        })
    }

    fn validate_float(&'a self, strict: bool) -> ValResult<'a, ValidationMatch<EitherFloat<'a>>>;

    fn validate_decimal(&'a self, strict: bool, py: Python<'a>) -> ValResult<&'a PyAny> {
        if strict {
            self.strict_decimal(py)
        } else {
            self.lax_decimal(py)
        }
    }
    fn strict_decimal(&'a self, py: Python<'a>) -> ValResult<&'a PyAny>;
    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn lax_decimal(&'a self, py: Python<'a>) -> ValResult<&'a PyAny> {
        self.strict_decimal(py)
    }

    fn validate_dict(&'a self, strict: bool) -> ValResult<GenericMapping<'a>> {
        if strict {
            self.strict_dict()
        } else {
            self.lax_dict()
        }
    }
    fn strict_dict(&'a self) -> ValResult<GenericMapping<'a>>;
    #[cfg_attr(has_coverage_attribute, coverage(off))]
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
    #[cfg_attr(has_coverage_attribute, coverage(off))]
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
    #[cfg_attr(has_coverage_attribute, coverage(off))]
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
    #[cfg_attr(has_coverage_attribute, coverage(off))]
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
    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn lax_frozenset(&'a self) -> ValResult<GenericIterable<'a>> {
        self.strict_frozenset()
    }

    fn extract_generic_iterable(&'a self) -> ValResult<GenericIterable<'a>>;

    fn validate_iter(&self) -> ValResult<GenericIterator>;

    fn validate_date(&self, strict: bool) -> ValResult<ValidationMatch<EitherDate>>;

    fn validate_time(
        &self,
        strict: bool,
        microseconds_overflow_behavior: speedate::MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<ValidationMatch<EitherTime>>;

    fn validate_datetime(
        &self,
        strict: bool,
        microseconds_overflow_behavior: speedate::MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<ValidationMatch<EitherDateTime>>;

    fn validate_timedelta(
        &self,
        strict: bool,
        microseconds_overflow_behavior: speedate::MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<ValidationMatch<EitherTimedelta>>;
}

/// The problem to solve here is that iterating a `StringMapping` returns an owned
/// `StringMapping`, but all the other iterators return references. By introducing
/// this trait we abstract over whether the return value from the iterator is owned
/// or borrowed; all we care about is that we can borrow it again with `borrow_input`
/// for some lifetime 'a.
///
/// This lifetime `'a` is shorter than the original lifetime `'data` of the input,
/// which is only a problem in error branches. To resolve we have to call `into_owned`
/// to extend out the lifetime to match the original input.
pub trait BorrowInput {
    type Input<'a>: Input<'a>
    where
        Self: 'a;
    fn borrow_input(&self) -> &Self::Input<'_>;
}
