use std::fmt;

use pyo3::exceptions::PyValueError;
use pyo3::types::{PyDict, PyList};
use pyo3::{intern, prelude::*};

use crate::errors::{ErrorTypeDefaults, InputValue, LocItem, ValError, ValResult};
use crate::lookup_key::{LookupKey, LookupPath};
use crate::tools::py_err;

use super::datetime::{EitherDate, EitherDateTime, EitherTime, EitherTimedelta};
use super::return_enums::{EitherBytes, EitherInt, EitherString};
use super::{EitherFloat, GenericIterator, ValidationMatch};

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

    fn is_none(&self) -> bool {
        false
    }

    fn as_python(&self) -> Option<&Bound<'py, PyAny>> {
        None
    }

    fn as_kwargs(&self, py: Python<'py>) -> Option<Bound<'py, PyDict>>;

    type Arguments<'a>: Arguments<'py>
    where
        Self: 'a;

    fn validate_args(&self) -> ValResult<Self::Arguments<'_>>;

    fn validate_dataclass_args<'a>(&'a self, dataclass_name: &str) -> ValResult<Self::Arguments<'a>>;

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

    type Dict<'a>: ValidatedDict<'py>
    where
        Self: 'a;

    fn validate_dict(&self, strict: bool) -> ValResult<Self::Dict<'_>> {
        if strict {
            self.strict_dict()
        } else {
            self.lax_dict()
        }
    }
    fn strict_dict(&self) -> ValResult<Self::Dict<'_>>;
    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn lax_dict(&self) -> ValResult<Self::Dict<'_>> {
        self.strict_dict()
    }

    fn validate_model_fields(&self, strict: bool, _from_attributes: bool) -> ValResult<Self::Dict<'_>> {
        self.validate_dict(strict)
    }

    type List<'a>: ValidatedList<'py>
    where
        Self: 'a;

    fn validate_list(&self, strict: bool) -> ValMatch<Self::List<'_>>;

    type Tuple<'a>: ValidatedTuple<'py>
    where
        Self: 'a;

    fn validate_tuple(&self, strict: bool) -> ValMatch<Self::Tuple<'_>>;

    type Set<'a>: ValidatedSet<'py>
    where
        Self: 'a;

    fn validate_set(&self, strict: bool) -> ValMatch<Self::Set<'_>>;

    fn validate_frozenset(&self, strict: bool) -> ValMatch<Self::Set<'_>>;

    fn validate_iter(&self) -> ValResult<GenericIterator<'static>>;

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

pub trait Arguments<'py> {
    type Args: PositionalArgs<'py> + ?Sized;
    type Kwargs: KeywordArgs<'py> + ?Sized;

    fn args(&self) -> Option<&Self::Args>;
    fn kwargs(&self) -> Option<&Self::Kwargs>;
}

pub trait PositionalArgs<'py> {
    type Item<'a>: BorrowInput<'py>
    where
        Self: 'a;
    fn len(&self) -> usize;
    fn get_item(&self, index: usize) -> Option<Self::Item<'_>>;
    fn iter(&self) -> impl Iterator<Item = Self::Item<'_>>;
}
pub trait KeywordArgs<'py> {
    type Key<'a>: BorrowInput<'py> + Clone + Into<LocItem>
    where
        Self: 'a;
    type Item<'a>: BorrowInput<'py> + ToPyObject
    where
        Self: 'a;
    fn len(&self) -> usize;
    fn get_item<'k>(&self, key: &'k LookupKey) -> ValResult<Option<(&'k LookupPath, Self::Item<'_>)>>;
    fn iter(&self) -> impl Iterator<Item = ValResult<(Self::Key<'_>, Self::Item<'_>)>>;
}

/// Some of the associated types like `ValidatedDict` and `ValidatedList` have multiple possible iterators
/// depending on the source input. This trait allows to pass a generic consumer to these iterator-producing
/// methods and dispatch over the different iterator types.
pub trait ConsumeIterator<T> {
    type Output;
    fn consume_iterator(self, iterator: impl Iterator<Item = T>) -> Self::Output;
}

/// For validations from a dictionary
pub trait ValidatedDict<'py> {
    type Key<'a>: BorrowInput<'py> + Clone + Into<LocItem>
    where
        Self: 'a;
    type Item<'a>: BorrowInput<'py>
    where
        Self: 'a;
    fn get_item<'k>(&self, key: &'k LookupKey) -> ValResult<Option<(&'k LookupPath, Self::Item<'_>)>>;
    fn as_py_dict(&self) -> Option<&Bound<'py, PyDict>>;
    // FIXME this is a bit of a leaky abstraction
    fn is_py_get_attr(&self) -> bool {
        false
    }
    fn iterate<'a, R>(
        &'a self,
        consumer: impl ConsumeIterator<ValResult<(Self::Key<'a>, Self::Item<'a>)>, Output = R>,
    ) -> ValResult<R>;
}

/// For validations from a list
pub trait ValidatedList<'py> {
    type Item: BorrowInput<'py>;
    fn len(&self) -> Option<usize>;
    fn as_py_list(&self) -> Option<&Bound<'py, PyList>>;
    fn iterate<R>(self, consumer: impl ConsumeIterator<PyResult<Self::Item>, Output = R>) -> ValResult<R>;
}

/// For validations from a tuple
pub trait ValidatedTuple<'py> {
    type Item: BorrowInput<'py>;
    fn len(&self) -> Option<usize>;
    fn iterate<R>(self, consumer: impl ConsumeIterator<PyResult<Self::Item>, Output = R>) -> ValResult<R>;
}

/// For validations from a set
pub trait ValidatedSet<'py> {
    type Item: BorrowInput<'py>;
    fn iterate<R>(self, consumer: impl ConsumeIterator<PyResult<Self::Item>, Output = R>) -> ValResult<R>;
}

/// This type is used for inputs which don't support certain types.
/// It implements all the associated traits, but never actually gets called.

pub enum Never {}

impl<'py> ValidatedDict<'py> for Never {
    type Key<'a> = Bound<'py, PyAny>;
    type Item<'a> = Bound<'py, PyAny>;
    fn get_item<'k>(&self, _key: &'k LookupKey) -> ValResult<Option<(&'k LookupPath, Self::Item<'_>)>> {
        unreachable!()
    }
    fn as_py_dict(&self) -> Option<&Bound<'py, PyDict>> {
        unreachable!()
    }
    fn iterate<'a, R>(
        &'a self,
        _consumer: impl ConsumeIterator<ValResult<(Self::Key<'a>, Self::Item<'a>)>, Output = R>,
    ) -> ValResult<R> {
        unreachable!()
    }
}

impl<'py> ValidatedList<'py> for Never {
    type Item = Bound<'py, PyAny>;
    fn len(&self) -> Option<usize> {
        unreachable!()
    }
    fn as_py_list(&self) -> Option<&Bound<'py, PyList>> {
        unreachable!()
    }
    fn iterate<R>(self, _consumer: impl ConsumeIterator<PyResult<Self::Item>, Output = R>) -> ValResult<R> {
        unreachable!()
    }
}

impl<'py> ValidatedTuple<'py> for Never {
    type Item = Bound<'py, PyAny>;
    fn len(&self) -> Option<usize> {
        unreachable!()
    }
    fn iterate<R>(self, _consumer: impl ConsumeIterator<PyResult<Self::Item>, Output = R>) -> ValResult<R> {
        unreachable!()
    }
}

impl<'py> ValidatedSet<'py> for Never {
    type Item = Bound<'py, PyAny>;
    fn iterate<R>(self, _consumer: impl ConsumeIterator<PyResult<Self::Item>, Output = R>) -> ValResult<R> {
        unreachable!()
    }
}

impl Arguments<'_> for Never {
    type Args = Never;
    type Kwargs = Never;
    fn args(&self) -> Option<&Self::Args> {
        unreachable!()
    }
    fn kwargs(&self) -> Option<&Self::Kwargs> {
        unreachable!()
    }
}

impl<'py> PositionalArgs<'py> for Never {
    type Item<'a> = Bound<'py, PyAny> where Self: 'a;
    fn len(&self) -> usize {
        unreachable!()
    }
    fn get_item(&self, _index: usize) -> Option<Self::Item<'_>> {
        unreachable!()
    }
    fn iter(&self) -> impl Iterator<Item = Self::Item<'_>> {
        [].into_iter()
    }
}

impl<'py> KeywordArgs<'py> for Never {
    type Key<'a> = Bound<'py, PyAny> where Self: 'a;
    type Item<'a> = Bound<'py, PyAny> where Self: 'a;
    fn len(&self) -> usize {
        unreachable!()
    }
    fn get_item<'k>(&self, _key: &'k LookupKey) -> ValResult<Option<(&'k LookupPath, Self::Item<'_>)>> {
        unreachable!()
    }
    fn iter(&self) -> impl Iterator<Item = ValResult<(Self::Key<'_>, Self::Item<'_>)>> {
        [].into_iter()
    }
}
