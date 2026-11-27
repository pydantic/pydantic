//! A byte-backed JSON input for the existing validator graph.
//!
//! Parsing failures are recorded for the ordinary parser to handle. Scalars and less common
//! operations use the existing JsonValue implementation, while objects retain
//! field spans and arrays materialize locally before ordinary list validation.

use std::cell::{Cell, OnceCell};

use jiter::{Jiter, JsonArray, JsonValue};
use pyo3::prelude::*;
use pyo3::types::PyDict;
use speedate::MicrosecondsPrecisionOverflowBehavior;

use super::datetime::{EitherDate, EitherDateTime, EitherTime};
use super::input_abstract::ValMatch;
use super::input_json::JsonArgs;
use super::return_enums::EitherComplex;
use super::{
    BorrowInput, ConsumeIterator, EitherBytes, EitherFloat, EitherInt, EitherString, EitherTimedelta, GenericIterator,
    Input, ValidatedDict, ValidationMatch,
};
use crate::errors::{ErrorTypeDefaults, InputValue, ValError, ValResult};
use crate::lookup_key::LookupPath;
use crate::validators::{TemporalUnitMode, ValBytesMode};

pub(crate) type JsonObjectBytes<'a> = (&'a [(String, &'a [u8])], &'a Cell<bool>);

#[derive(Debug)]
pub(crate) struct JsonBytesInput<'data> {
    data: &'data [u8],
    failed: &'data Cell<bool>,
    value: OnceCell<JsonValue<'data>>,
    fields: OnceCell<Vec<(String, &'data [u8])>>,
}

impl<'data> JsonBytesInput<'data> {
    pub fn new(data: &'data [u8], failed: &'data Cell<bool>) -> Self {
        Self {
            data: data.trim_ascii_start(),
            failed,
            value: OnceCell::new(),
            fields: OnceCell::new(),
        }
    }

    fn parsed(value: JsonValue<'data>, failed: &'data Cell<bool>) -> Self {
        Self {
            data: &[],
            failed,
            value: OnceCell::from(value),
            fields: OnceCell::new(),
        }
    }

    fn value(&self) -> &JsonValue<'data> {
        self.value.get_or_init(|| {
            JsonValue::parse(self.data, true).unwrap_or_else(|_| {
                self.failed.set(true);
                JsonValue::Null
            })
        })
    }

    fn object(&self, deduplicate: bool) -> ValResult<JsonObjectInput<'_, 'data>> {
        if self.data.first() == Some(&b'{') || matches!(self.value.get(), Some(JsonValue::Object(_))) {
            Ok(JsonObjectInput {
                input: self,
                deduplicate,
            })
        } else {
            Err(ValError::new(ErrorTypeDefaults::DictType, self))
        }
    }

    fn fields(&self) -> &[(String, &'data [u8])] {
        self.fields.get_or_init(|| {
            let parse = || -> jiter::JiterResult<_> {
                let mut cursor = Jiter::new(self.data).with_allow_inf_nan();
                let mut fields = Vec::new();
                let mut key = cursor.next_object()?;
                while let Some(name) = key {
                    let name = name.to_owned();
                    cursor.peek()?;
                    let start = cursor.current_index();
                    cursor.next_skip()?;
                    fields.push((name, cursor.slice_to_current(start)));
                    key = cursor.next_key()?;
                }
                cursor.finish()?;
                Ok(fields)
            };
            parse().unwrap_or_else(|_| {
                self.failed.set(true);
                Vec::new()
            })
        })
    }

    /// Complete checks that validation may not have needed (for example an empty model).
    pub fn finish(&self) -> bool {
        if self.value.get().is_none() {
            if self.data.first() == Some(&b'{') {
                self.fields();
            } else {
                self.value();
            }
        }
        !self.failed.get()
    }
}

impl BorrowInput<'_> for JsonBytesInput<'_> {
    type Input = Self;
    fn borrow_input(&self) -> &Self {
        self
    }
}

pub(crate) struct JsonObjectInput<'a, 'data> {
    input: &'a JsonBytesInput<'data>,
    deduplicate: bool,
}

impl<'data> ValidatedDict<'_> for JsonObjectInput<'_, 'data> {
    type Key<'a>
        = String
    where
        Self: 'a;
    type Item<'a>
        = JsonBytesInput<'data>
    where
        Self: 'a;

    fn get_item(&self, key: &LookupPath) -> ValResult<Option<Self::Item<'_>>> {
        if self.input.data.is_empty() || !key.rest().is_empty() {
            let JsonValue::Object(object) = self.input.value() else {
                return Ok(None);
            };
            return key
                .json_get(object)
                .map(|v| v.cloned().map(|v| JsonBytesInput::parsed(v, self.input.failed)));
        }
        Ok(self
            .input
            .fields()
            .iter()
            .rev()
            .find(|(name, _)| name == key.first_key())
            .map(|(_, data)| JsonBytesInput::new(data, self.input.failed)))
    }

    fn iterate<'a, R>(
        &'a self,
        consumer: impl ConsumeIterator<ValResult<(Self::Key<'a>, Self::Item<'a>)>, Output = R>,
    ) -> ValResult<R> {
        if self.input.data.is_empty() {
            let JsonValue::Object(object) = self.input.value() else {
                return Ok(consumer.consume_iterator(std::iter::empty()));
            };
            return Ok(consumer.consume_iterator(object.iter().map(|(key, value)| {
                Ok((
                    key.to_string(),
                    JsonBytesInput::parsed(value.clone(), self.input.failed),
                ))
            })));
        }
        let fields = self.input.fields();
        let mut unique = indexmap::IndexMap::new();
        if self.deduplicate {
            for (name, data) in fields {
                unique.insert(name, data);
            }
        }
        let iter: Box<dyn Iterator<Item = (&String, &&'data [u8])>> = if self.deduplicate {
            Box::new(unique.into_iter())
        } else {
            Box::new(fields.iter().map(|(name, data)| (name, data)))
        };
        Ok(consumer.consume_iterator(
            iter.map(|(name, data)| Ok((name.clone(), JsonBytesInput::new(data, self.input.failed)))),
        ))
    }

    fn last_key(&self) -> Option<Self::Key<'_>> {
        if self.input.data.is_empty() {
            let JsonValue::Object(object) = self.input.value() else {
                return None;
            };
            object.last().map(|(name, _)| name.to_string())
        } else {
            self.input.fields().last().map(|(name, _)| name.clone())
        }
    }
}

impl<'py, 'data> Input<'py> for JsonBytesInput<'data> {
    fn as_json(&self) -> Option<&JsonValue<'_>> {
        self.value.get()
    }

    fn as_json_object_bytes(&self) -> Option<JsonObjectBytes<'_>> {
        (self.data.first() == Some(&b'{')).then(|| (self.fields(), self.failed))
    }

    fn materialized_json(&self) -> Option<&JsonValue<'_>> {
        Some(self.value())
    }

    fn identity(&self) -> Option<usize> {
        None
    }

    #[inline]
    fn py_converter(&self) -> impl IntoPyObject<'py> + '_ {
        self.value()
    }

    fn as_error_value(&self) -> InputValue {
        self.value().as_error_value()
    }

    fn is_none(&self) -> bool {
        self.value().is_none()
    }

    fn as_kwargs(&self, py: Python<'py>) -> Option<Bound<'py, PyDict>> {
        self.value().as_kwargs(py)
    }

    type Arguments<'a>
        = JsonArgs<'a, 'data>
    where
        Self: 'a;

    fn validate_args(&self) -> ValResult<JsonArgs<'_, 'data>> {
        self.value().validate_args()
    }

    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn validate_args_v3(&self) -> ValResult<Self::Arguments<'_>> {
        self.value().validate_args_v3()
    }

    fn validate_dataclass_args<'a>(&'a self, class_name: &str) -> ValResult<JsonArgs<'a, 'data>> {
        self.value().validate_dataclass_args(class_name)
    }

    fn validate_str(
        &self,
        strict: bool,
        coerce_numbers_to_str: bool,
    ) -> ValResult<ValidationMatch<EitherString<'_, 'py>>> {
        self.value().validate_str(strict, coerce_numbers_to_str)
    }

    fn validate_bytes<'a>(
        &'a self,
        _strict: bool,
        mode: ValBytesMode,
    ) -> ValResult<ValidationMatch<EitherBytes<'a, 'py>>> {
        self.value().validate_bytes(_strict, mode)
    }

    fn validate_bool(&self, strict: bool) -> ValResult<ValidationMatch<bool>> {
        self.value().validate_bool(strict)
    }

    fn validate_int(&self, strict: bool) -> ValResult<ValidationMatch<EitherInt<'_>>> {
        self.value().validate_int(strict)
    }

    fn exact_str(&self) -> ValResult<EitherString<'_, 'py>> {
        self.value().exact_str()
    }

    fn validate_float(&self, strict: bool) -> ValResult<ValidationMatch<EitherFloat<'_>>> {
        self.value().validate_float(strict)
    }

    fn validate_decimal(&self, strict: bool, py: Python<'py>) -> ValMatch<Bound<'py, PyAny>> {
        self.value().validate_decimal(strict, py)
    }

    fn validate_fraction(&self, _strict: bool, py: Python<'py>) -> ValMatch<Bound<'py, PyAny>> {
        self.value().validate_fraction(_strict, py)
    }

    type Dict<'a>
        = JsonObjectInput<'a, 'data>
    where
        Self: 'a;

    fn validate_dict(&self, _strict: bool) -> ValResult<Self::Dict<'_>> {
        self.object(false)
    }
    #[cfg_attr(has_coverage_attribute, coverage(off))]
    fn strict_dict(&self) -> ValResult<Self::Dict<'_>> {
        self.object(false)
    }

    fn strict_frozendict(&self) -> ValMatch<Self::Dict<'_>> {
        self.value().strict_frozendict()?;
        Ok(ValidationMatch::strict(JsonObjectInput {
            input: self,
            deduplicate: false,
        }))
    }

    fn strict_ordered_dict(&self) -> ValMatch<Self::Dict<'_>> {
        self.value().strict_ordered_dict()?;
        Ok(ValidationMatch::strict(JsonObjectInput {
            input: self,
            deduplicate: false,
        }))
    }

    fn strict_counter(&self) -> ValMatch<Self::Dict<'_>> {
        self.value().strict_counter()?;
        Ok(ValidationMatch::strict(JsonObjectInput {
            input: self,
            deduplicate: false,
        }))
    }

    fn validate_model_fields(&self, _strict: bool, _from_attributes: bool) -> ValResult<Self::Dict<'_>> {
        self.object(true)
    }

    type List<'a>
        = &'a JsonArray<'data>
    where
        Self: 'a;

    fn validate_list(&self, _strict: bool) -> ValMatch<Self::List<'_>> {
        self.value().validate_list(_strict)
    }

    fn validate_deque(&self, _strict: bool) -> ValMatch<(Self::List<'_>, Option<usize>)> {
        self.value().validate_deque(_strict)
    }

    type Tuple<'a>
        = &'a JsonArray<'data>
    where
        Self: 'a;

    fn validate_tuple(&self, _strict: bool) -> ValMatch<&JsonArray<'data>> {
        self.value().validate_tuple(_strict)
    }

    type Set<'a>
        = &'a JsonArray<'data>
    where
        Self: 'a;

    fn validate_set(&self, _strict: bool) -> ValMatch<&JsonArray<'data>> {
        self.value().validate_set(_strict)
    }

    fn validate_frozenset(&self, _strict: bool) -> ValMatch<&JsonArray<'data>> {
        self.value().validate_frozenset(_strict)
    }

    fn validate_iter(&self) -> ValResult<GenericIterator<'static>> {
        self.value().validate_iter()
    }

    fn validate_date(&self, _strict: bool, mode: TemporalUnitMode) -> ValResult<ValidationMatch<EitherDate<'py>>> {
        self.value().validate_date(_strict, mode)
    }
    fn validate_time(
        &self,
        strict: bool,
        microseconds_overflow_behavior: MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<ValidationMatch<EitherTime<'py>>> {
        self.value().validate_time(strict, microseconds_overflow_behavior)
    }

    fn validate_datetime(
        &self,
        strict: bool,
        microseconds_overflow_behavior: speedate::MicrosecondsPrecisionOverflowBehavior,
        mode: TemporalUnitMode,
    ) -> ValResult<ValidationMatch<EitherDateTime<'py>>> {
        self.value()
            .validate_datetime(strict, microseconds_overflow_behavior, mode)
    }

    fn validate_timedelta(
        &self,
        strict: bool,
        microseconds_overflow_behavior: speedate::MicrosecondsPrecisionOverflowBehavior,
    ) -> ValResult<ValidationMatch<EitherTimedelta<'py>>> {
        self.value().validate_timedelta(strict, microseconds_overflow_behavior)
    }

    fn validate_complex(&self, strict: bool, py: Python<'py>) -> ValResult<ValidationMatch<EitherComplex<'py>>> {
        self.value().validate_complex(strict, py)
    }
}
