use std::sync::Arc;

use pyo3::exceptions::{PyTypeError, PyValueError};
use pyo3::intern;
use pyo3::sync::PyOnceLock;
use pyo3::types::{IntoPyDict, PyDict, PyString, PyTuple, PyType};
use pyo3::{PyTypeInfo, prelude::*};

use crate::build_tools::{is_strict, schema_or_config_same};
use crate::errors::ErrorType;
use crate::errors::ValResult;
use crate::errors::{ErrorTypeDefaults, Number};
use crate::errors::{ToErrorValue, ValError};
use crate::input::Input;
use crate::tools::SchemaDict;

use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

static DECIMAL_TYPE: PyOnceLock<Py<PyType>> = PyOnceLock::new();

pub fn get_decimal_type(py: Python<'_>) -> &Bound<'_, PyType> {
    DECIMAL_TYPE
        .get_or_init(py, || {
            py.import("decimal")
                .and_then(|decimal_module| decimal_module.getattr("Decimal"))
                .unwrap()
                .extract()
                .unwrap()
        })
        .bind(py)
}

fn validate_as_decimal(
    py: Python,
    schema: &Bound<'_, PyDict>,
    key: &Bound<'_, PyString>,
) -> PyResult<Option<Py<PyAny>>> {
    match schema.get_item(key)? {
        Some(value) => match value.validate_decimal(false, py) {
            Ok(v) => Ok(Some(v.into_inner().unbind())),
            Err(_) => Err(PyValueError::new_err(format!(
                "'{key}' must be coercible to a Decimal instance",
            ))),
        },
        None => Ok(None),
    }
}

#[derive(Debug, Clone)]
pub struct DecimalValidator {
    strict: bool,
    allow_inf_nan: bool,
    check_digits: bool,
    multiple_of: Option<Py<PyAny>>,
    le: Option<Py<PyAny>>,
    lt: Option<Py<PyAny>>,
    ge: Option<Py<PyAny>>,
    gt: Option<Py<PyAny>>,
    max_digits: Option<u64>,
    decimal_places: Option<u64>,
}

impl BuildValidator for DecimalValidator {
    const EXPECTED_TYPE: &'static str = "decimal";
    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<Arc<CombinedValidator>>,
    ) -> PyResult<Arc<CombinedValidator>> {
        let py = schema.py();

        let allow_inf_nan = schema_or_config_same(schema, config, intern!(py, "allow_inf_nan"))?.unwrap_or(false);
        let decimal_places = schema.get_as(intern!(py, "decimal_places"))?;
        let max_digits = schema.get_as(intern!(py, "max_digits"))?;
        if allow_inf_nan && (decimal_places.is_some() || max_digits.is_some()) {
            return Err(PyValueError::new_err(
                "allow_inf_nan=True cannot be used with max_digits or decimal_places",
            ));
        }

        Ok(CombinedValidator::Decimal(Self {
            strict: is_strict(schema, config)?,
            allow_inf_nan,
            check_digits: decimal_places.is_some() || max_digits.is_some(),
            decimal_places,
            multiple_of: validate_as_decimal(py, schema, intern!(py, "multiple_of"))?,
            le: validate_as_decimal(py, schema, intern!(py, "le"))?,
            lt: validate_as_decimal(py, schema, intern!(py, "lt"))?,
            ge: validate_as_decimal(py, schema, intern!(py, "ge"))?,
            gt: validate_as_decimal(py, schema, intern!(py, "gt"))?,
            max_digits,
        })
        .into())
    }
}

impl_py_gc_traverse!(DecimalValidator {
    multiple_of,
    le,
    lt,
    ge,
    gt
});

fn count_digits(num_digits: u64, exponent: i64) -> (u64, u64) {
    if exponent >= 0 {
        // A positive exponent adds that many trailing zeros.
        (0, num_digits.saturating_add(exponent as u64))
    } else {
        // If the absolute value of the negative exponent is larger than the
        // number of digits, then it's the same as the number of digits,
        // because it'll consume all the digits in digit_tuple and then
        // add abs(exponent) - len(digit_tuple) leading zeros after the
        // decimal point.
        let decimals = exponent.unsigned_abs();
        (decimals, num_digits.max(decimals))
    }
}

fn extract_decimal_digits_info(decimal: &Bound<'_, PyAny>) -> ValResult<((u64, u64), (u64, u64))> {
    let py = decimal.py();
    let (_, digit_tuple, exponent): (Bound<'_, PyAny>, Bound<'_, PyTuple>, Bound<'_, PyAny>) =
        decimal.call_method0(intern!(py, "as_tuple"))?.extract()?;

    let num_digits: u64 = u64::try_from(digit_tuple.len()).map_err(|e| ValError::InternalErr(e.into()))?;

    // While we could use `Decimal.normalize()` to strip trailing zeros, this method also
    // rounds according to current context (with default precision of 28). Instead, we
    // strip them manually:
    let mut trailing_zeros: u64 = 0;
    for digit in digit_tuple.iter().rev() {
        if digit.extract::<u8>()? != 0 {
            break;
        }
        trailing_zeros += 1;
    }
    // `Decimal.normalize()` canonicalizes any zero to `0E0`, whatever the exponent is:
    let is_zero = trailing_zeros == num_digits;

    // Finite values have a numeric exponent (we checked `Decimal.is_finite()` before calling
    // `extract_decimal_digits_info()`). The C implementation of the `decimal` module bounds
    // the exponent (see https://docs.python.org/3/library/decimal.html#constants), so it always fits
    // in an `i64`. However, the pure Python implementation does not, and the exponent can be an arbitrarily
    // large integer.
    let Ok(exponent) = exponent.extract::<i64>() else {
        // We don't need the exact number of digits and decimal places: they are only ever compared
        // against the `max_digits` and `decimal_places` constraints, which are `u64`s. If the exponent
        // doesn't fit in an `i64`, the value has more than `i64::MAX` digits (when the exponent is
        // positive) or more than `i64::MAX` decimal places and digits (when the exponent is negative),
        // so the result of these comparisons is already known: any constraint one can set is exceeded.
        // Saturating the counts to `u64::MAX` gives that outcome (except for the theoretical `u64::MAX`
        // constraint) without having to represent the actual exponent.
        let is_negative: bool = exponent.lt(0)?;
        let counts = if is_negative {
            (u64::MAX, u64::MAX)
        } else {
            (0, u64::MAX)
        };
        let normalized = if is_zero { (0, 1) } else { counts };
        return Ok((counts, normalized));
    };

    let counts = count_digits(num_digits, exponent);
    let normalized = if is_zero {
        (0, 1)
    } else if exponent >= 0 {
        // Stripping `k` trailing zeros increments the exponent by `k`, and the number of digits is
        // `num_digits + exponent` for a non-negative exponent, so the counts are unchanged. Reusing
        // them also avoids overflowing the exponent when it is close to `i64::MAX`.
        counts
    } else {
        // Each stripped trailing zero is compensated by incrementing the exponent. This can't
        // overflow, as the exponent is negative and `trailing_zeros <= num_digits`.
        count_digits(num_digits - trailing_zeros, exponent + trailing_zeros as i64)
    };

    Ok((counts, normalized))
}

impl Validator for DecimalValidator {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Py<PyAny>> {
        let decimal = input.validate_decimal(state.strict_or(self.strict), py)?.unpack(state);

        if !self.allow_inf_nan || self.check_digits {
            if !decimal.call_method0(intern!(py, "is_finite"))?.extract()? {
                return Err(ValError::new(ErrorTypeDefaults::FiniteNumber, input));
            }

            if self.check_digits
                // TODO: should errors be raised if extract_decimal_digits_info fails?
                && let Ok(((decimals, digits), (normalized_decimals, normalized_digits))) =
                    extract_decimal_digits_info(&decimal)
            {
                if let Some(max_digits) = self.max_digits
                    && (digits > max_digits)
                    && (normalized_digits > max_digits)
                {
                    return Err(ValError::new(
                        ErrorType::DecimalMaxDigits {
                            max_digits,
                            context: None,
                        },
                        input,
                    ));
                }

                if let Some(decimal_places) = self.decimal_places {
                    if (decimals > decimal_places) && (normalized_decimals > decimal_places) {
                        return Err(ValError::new(
                            ErrorType::DecimalMaxPlaces {
                                decimal_places,
                                context: None,
                            },
                            input,
                        ));
                    }

                    if let Some(max_digits) = self.max_digits {
                        let whole_digits = digits.saturating_sub(decimals);
                        let max_whole_digits = max_digits.saturating_sub(decimal_places);

                        let normalized_whole_digits = normalized_digits.saturating_sub(normalized_decimals);
                        let normalized_max_whole_digits = max_digits.saturating_sub(decimal_places);

                        if (whole_digits > max_whole_digits) && (normalized_whole_digits > normalized_max_whole_digits)
                        {
                            return Err(ValError::new(
                                ErrorType::DecimalWholeDigits {
                                    whole_digits: max_whole_digits,
                                    context: None,
                                },
                                input,
                            ));
                        }
                    }
                }
            }
        }

        if let Some(multiple_of) = &self.multiple_of {
            // fraction = (decimal / multiple_of) % 1
            let fraction = (decimal.div(multiple_of)?).rem(1)?;
            let zero = 0u8.into_pyobject(py)?;
            if !fraction.eq(&zero)? {
                return Err(ValError::new(
                    ErrorType::MultipleOf {
                        multiple_of: multiple_of.to_string().into(),
                        context: Some([("multiple_of", multiple_of)].into_py_dict(py)?.into()),
                    },
                    input,
                ));
            }
        }

        // Decimal raises DecimalOperation when comparing NaN, so if it's necessary to compare
        // the value to a number, we need to check for NaN first. We cache the result on the first
        // time we check it.
        let mut is_nan: Option<bool> = None;
        let mut is_nan = || -> PyResult<bool> {
            match is_nan {
                Some(is_nan) => Ok(is_nan),
                None => Ok(*is_nan.insert(decimal.call_method0(intern!(py, "is_nan"))?.extract()?)),
            }
        };

        if let Some(le) = &self.le
            && (is_nan()? || !decimal.le(le)?)
        {
            return Err(ValError::new(
                ErrorType::LessThanEqual {
                    le: Number::String(le.to_string()),
                    context: Some([("le", le)].into_py_dict(py)?.into()),
                },
                input,
            ));
        }
        if let Some(lt) = &self.lt
            && (is_nan()? || !decimal.lt(lt)?)
        {
            return Err(ValError::new(
                ErrorType::LessThan {
                    lt: Number::String(lt.to_string()),
                    context: Some([("lt", lt)].into_py_dict(py)?.into()),
                },
                input,
            ));
        }
        if let Some(ge) = &self.ge
            && (is_nan()? || !decimal.ge(ge)?)
        {
            return Err(ValError::new(
                ErrorType::GreaterThanEqual {
                    ge: Number::String(ge.to_string()),
                    context: Some([("ge", ge)].into_py_dict(py)?.into()),
                },
                input,
            ));
        }
        if let Some(gt) = &self.gt
            && (is_nan()? || !decimal.gt(gt)?)
        {
            return Err(ValError::new(
                ErrorType::GreaterThan {
                    gt: Number::String(gt.to_string()),
                    context: Some([("gt", gt)].into_py_dict(py)?.into()),
                },
                input,
            ));
        }

        Ok(decimal.into())
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}

pub(crate) fn create_decimal<'py>(arg: &Bound<'py, PyAny>, input: impl ToErrorValue) -> ValResult<Bound<'py, PyAny>> {
    let py = arg.py();
    get_decimal_type(py).call1((arg,)).map_err(|e| {
        let decimal_exception = match py
            .import("decimal")
            .and_then(|decimal_module| decimal_module.getattr("DecimalException"))
        {
            Ok(decimal_exception) => decimal_exception,
            Err(e) => return ValError::InternalErr(e),
        };
        handle_decimal_new_error(input, e, decimal_exception)
    })
}

fn handle_decimal_new_error(input: impl ToErrorValue, error: PyErr, decimal_exception: Bound<'_, PyAny>) -> ValError {
    let py = decimal_exception.py();
    if error.matches(py, decimal_exception).unwrap_or(false) {
        ValError::new(ErrorTypeDefaults::DecimalParsing, input)
    } else if error.matches(py, PyTypeError::type_object(py)).unwrap_or(false) {
        ValError::new(ErrorTypeDefaults::DecimalType, input)
    } else {
        ValError::InternalErr(error)
    }
}
