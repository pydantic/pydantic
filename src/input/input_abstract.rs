use std::fmt;

use pyo3::exceptions::PyValueError;
use pyo3::types::{PyDict, PyList, PyType};
use pyo3::{intern, prelude::*};

use crate::errors::{ErrorTypeDefaults, InputValue, ValError, ValResult};
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
            Self::Json => intern!(py, "json").into_py(py),
            Self::Python => intern!(py, "python").into_py(py),
            Self::String => intern!(py, "string").into_py(py),
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

pub type ValMatch<T> = ValResult<ValidationMatch<T>>;

/// all types have three methods: `validate_*`, `strict_*`, `lax_*`
/// the convention is to either implement:
/// * `strict_*` & `lax_*` if they have different behavior
/// * or, `validate_*` and `strict_*` to just call `validate_*` if the behavior for strict and lax is the same
pub trait Input<'py>: fmt::Debug + ToPyObject {
    fn as_error_value(&self) -> InputValue;

    fn identity(&self) -> Option<usize> {
        None
    }

    fn is_none(&self) -> bool {
        false
    }

    fn input_is_instance(&self, _class: &Bound<'py, PyType>) -> Option<&Bound<'py, PyAny>> {
        None
    }

    fn is_python(&self) -> bool {
        false
    }

    fn as_kwargs(&self, py: Python<'py>) -> Option<Bound<'py, PyDict>>;

    fn input_is_subclass(&self, _class: &Bound<'_, PyType>) -> PyResult<bool> {
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

    fn validate_args(&self) -> ValResult<GenericArguments<'_, 'py>>;

    fn validate_dataclass_args<'a>(&'a self, dataclass_name: &str) -> ValResult<GenericArguments<'a, 'py>>;

    fn validate_str(&self, strict: bool, coerce_numbers_to_str: bool) -> ValMatch<EitherString<'_>>;

    fn validate_bytes<'a>(&'a self, strict: bool) -> ValMatch<EitherBytes<'a, 'py>>;

    fn validate_bool(&self, strict: bool) -> ValMatch<bool>;

    fn validate_int(&self, strict: bool) -> ValMatch<EitherInt<'_>>;

    fn exact_int(&self) -> ValResult<EitherInt<'_>> {
        self.validate_int(true).and_then(|val_match| {
            val_match
                .require_exact()
                .ok_or_else(|| ValError::new(ErrorTypeDefaults::IntType, self))
        })
    }

    /// Extract a String from the input, only allowing exact
    /// matches for a String (no subclasses)
    fn exact_str(&self) -> ValResult<EitherString<'_>> {
        self.validate_str(true, false).and_then(|val_match| {
            val_match
                .require_exact()
                .ok_or_else(|| ValError::new(ErrorTypeDefaults::StringType, self))
        })
    }

    fn validate_float(&self, strict: bool) -> ValMatch<EitherFloat<'_>>;

    fn validate_decimal(&self, strict: bool, py: Python<'py>) -> ValResult<Bound<'py, PyAny>> {
        if strict {
            self.strict_decimal(py)
        } else {
            self.lax_decimal(py)
        }
    }
    fn strict_decimal(&self, py: Python<'py>) -> ValResult<Bound<'py, PyAny>>;
    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn lax_decimal(&self, py: Python<'py>) -> ValResult<Bound<'py, PyAny>> {
        self.strict_decimal(py)
    }

    fn validate_dict<'a>(&'a self, strict: bool) -> ValResult<GenericMapping<'a, 'py>> {
        if strict {
            self.strict_dict()
        } else {
            self.lax_dict()
        }
    }
    fn strict_dict<'a>(&'a self) -> ValResult<GenericMapping<'a, 'py>>;
    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn lax_dict<'a>(&'a self) -> ValResult<GenericMapping<'a, 'py>> {
        self.strict_dict()
    }

    fn validate_model_fields<'a>(&'a self, strict: bool, _from_attributes: bool) -> ValResult<GenericMapping<'a, 'py>> {
        self.validate_dict(strict)
    }

    type List<'a>: Iterable<'py> + AsPyList<'py>
    where
        Self: 'a;

    fn validate_list(&self, strict: bool) -> ValMatch<Self::List<'_>>;

    fn validate_tuple<'a>(&'a self, strict: bool) -> ValResult<GenericIterable<'a, 'py>> {
        if strict {
            self.strict_tuple()
        } else {
            self.lax_tuple()
        }
    }
    fn strict_tuple<'a>(&'a self) -> ValResult<GenericIterable<'a, 'py>>;
    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn lax_tuple<'a>(&'a self) -> ValResult<GenericIterable<'a, 'py>> {
        self.strict_tuple()
    }

    fn validate_set<'a>(&'a self, strict: bool) -> ValResult<GenericIterable<'a, 'py>> {
        if strict {
            self.strict_set()
        } else {
            self.lax_set()
        }
    }
    fn strict_set<'a>(&'a self) -> ValResult<GenericIterable<'a, 'py>>;
    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn lax_set<'a>(&'a self) -> ValResult<GenericIterable<'a, 'py>> {
        self.strict_set()
    }

    fn validate_frozenset<'a>(&'a self, strict: bool) -> ValResult<GenericIterable<'a, 'py>> {
        if strict {
            self.strict_frozenset()
        } else {
            self.lax_frozenset()
        }
    }
    fn strict_frozenset<'a>(&'a self) -> ValResult<GenericIterable<'a, 'py>>;
    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn lax_frozenset<'a>(&'a self) -> ValResult<GenericIterable<'a, 'py>> {
        self.strict_frozenset()
    }

    fn extract_generic_iterable<'a>(&'a self) -> ValResult<GenericIterable<'a, 'py>>;

    fn validate_iter(&self) -> ValResult<GenericIterator>;

    fn validate_date(&self, strict: bool) -> ValMatch<EitherDate<'py>>;

    fn validate_time(
        &self,
        strict: bool,
        microseconds_overflow_behavior: speedate::MicrosecondsPrecisionOverflowBehavior,
    ) -> ValMatch<EitherTime<'py>>;

    fn validate_datetime(
        &self,
        strict: bool,
        microseconds_overflow_behavior: speedate::MicrosecondsPrecisionOverflowBehavior,
    ) -> ValMatch<EitherDateTime<'py>>;

    fn validate_timedelta(
        &self,
        strict: bool,
        microseconds_overflow_behavior: speedate::MicrosecondsPrecisionOverflowBehavior,
    ) -> ValMatch<EitherTimedelta<'py>>;
}

/// The problem to solve here is that iterating collections often returns owned
/// values, but inputs are usually taken by reference. By introducing
/// this trait we abstract over whether the return value from the iterator is owned
/// or borrowed; all we care about is that we can borrow it again with `borrow_input`
/// for some lifetime 'a.
pub trait BorrowInput<'py> {
    type Input: Input<'py> + ?Sized;
    fn borrow_input(&self) -> &Self::Input;
}

impl<'py, T: Input<'py> + ?Sized> BorrowInput<'py> for &'_ T {
    type Input = T;
    fn borrow_input(&self) -> &Self::Input {
        self
    }
}

pub enum Never {}

// Pairs with Iterable below
pub trait ConsumeIterator<T> {
    type Output;
    fn consume_iterator(self, iterator: impl Iterator<Item = T>) -> Self::Output;
}

// This slightly awkward trait is used to define types which can be iterable. This formulation
// arises because the Python enums have several different underlying iterator types, and we want to
// be able to dispatch over each of them without overhead.
pub trait Iterable<'py> {
    type Input: BorrowInput<'py>;
    fn len(&self) -> Option<usize>;
    fn iterate<R>(self, consumer: impl ConsumeIterator<PyResult<Self::Input>, Output = R>) -> ValResult<R>;
}

// Necessary for inputs which don't support certain types, e.g. String -> list
impl<'py> Iterable<'py> for Never {
    type Input = Bound<'py, PyAny>; // Doesn't really matter what this is
    fn len(&self) -> Option<usize> {
        unreachable!()
    }
    fn iterate<R>(self, _consumer: impl ConsumeIterator<PyResult<Self::Input>, Output = R>) -> ValResult<R> {
        unreachable!()
    }
}

// Optimization pathway for inputs which are already python lists
pub trait AsPyList<'py>: Iterable<'py> {
    fn as_py_list(&self) -> Option<&Bound<'py, PyList>>;
}

impl<'py> AsPyList<'py> for Never {
    fn as_py_list(&self) -> Option<&Bound<'py, PyList>> {
        unreachable!()
    }
}
