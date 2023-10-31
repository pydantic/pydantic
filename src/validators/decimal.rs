use pyo3::exceptions::{PyTypeError, PyValueError};
use pyo3::intern;
use pyo3::sync::GILOnceCell;
use pyo3::types::{IntoPyDict, PyDict, PyTuple, PyType};
use pyo3::{prelude::*, PyTypeInfo};

use crate::build_tools::{is_strict, schema_or_config_same};
use crate::errors::ValError;
use crate::errors::ValResult;
use crate::errors::{ErrorType, InputValue};
use crate::errors::{ErrorTypeDefaults, Number};
use crate::input::Input;
use crate::tools::SchemaDict;

use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

static DECIMAL_TYPE: GILOnceCell<Py<PyType>> = GILOnceCell::new();

pub fn get_decimal_type(py: Python) -> Py<PyType> {
    DECIMAL_TYPE
        .get_or_init(py, || {
            py.import("decimal")
                .and_then(|decimal_module| decimal_module.getattr("Decimal"))
                .unwrap()
                .extract::<&PyType>()
                .unwrap()
                .into()
        })
        .clone()
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
        schema: &PyDict,
        config: Option<&PyDict>,
        _definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let allow_inf_nan = schema_or_config_same(schema, config, intern!(py, "allow_inf_nan"))?.unwrap_or(false);
        let decimal_places = schema.get_as(intern!(py, "decimal_places"))?;
        let max_digits = schema.get_as(intern!(py, "max_digits"))?;
        if allow_inf_nan && (decimal_places.is_some() || max_digits.is_some()) {
            return Err(PyValueError::new_err(
                "allow_inf_nan=True cannot be used with max_digits or decimal_places",
            ));
        }
        Ok(Self {
            strict: is_strict(schema, config)?,
            allow_inf_nan,
            check_digits: decimal_places.is_some() || max_digits.is_some(),
            decimal_places,
            multiple_of: schema.get_as(intern!(py, "multiple_of"))?,
            le: schema.get_as(intern!(py, "le"))?,
            lt: schema.get_as(intern!(py, "lt"))?,
            ge: schema.get_as(intern!(py, "ge"))?,
            gt: schema.get_as(intern!(py, "gt"))?,
            max_digits,
        }
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

fn extract_decimal_digits_info<'data>(
    decimal: &PyAny,
    normalized: bool,
    py: Python<'data>,
) -> ValResult<'data, (u64, u64)> {
    let mut normalized_decimal: Option<&PyAny> = None;
    if normalized {
        normalized_decimal = Some(decimal.call_method0(intern!(py, "normalize")).unwrap_or(decimal));
    }
    let (_, digit_tuple, exponent): (&PyAny, &PyTuple, &PyAny) = normalized_decimal
        .unwrap_or(decimal)
        .call_method0(intern!(py, "as_tuple"))?
        .extract()?;

    // finite values have numeric exponent, we checked is_finite above
    let exponent: i64 = exponent.extract()?;
    let mut digits: u64 = u64::try_from(digit_tuple.len()).map_err(|e| ValError::InternalErr(e.into()))?;
    let decimals;
    if exponent >= 0 {
        // A positive exponent adds that many trailing zeros.
        digits += exponent as u64;
        decimals = 0;
    } else {
        // If the absolute value of the negative exponent is larger than the
        // number of digits, then it's the same as the number of digits,
        // because it'll consume all the digits in digit_tuple and then
        // add abs(exponent) - len(digit_tuple) leading zeros after the
        // decimal point.
        decimals = exponent.unsigned_abs();
        digits = digits.max(decimals);
    }

    Ok((decimals, digits))
}

impl Validator for DecimalValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        let decimal = input.validate_decimal(state.strict_or(self.strict), py)?;

        if !self.allow_inf_nan || self.check_digits {
            if !decimal.call_method0(intern!(py, "is_finite"))?.extract()? {
                return Err(ValError::new(ErrorTypeDefaults::FiniteNumber, input));
            }

            if self.check_digits {
                if let Ok((normalized_decimals, normalized_digits)) = extract_decimal_digits_info(decimal, true, py) {
                    if let Ok((decimals, digits)) = extract_decimal_digits_info(decimal, false, py) {
                        if let Some(max_digits) = self.max_digits {
                            if (digits > max_digits) & (normalized_digits > max_digits) {
                                return Err(ValError::new(
                                    ErrorType::DecimalMaxDigits {
                                        max_digits,
                                        context: None,
                                    },
                                    input,
                                ));
                            }
                        }

                        if let Some(decimal_places) = self.decimal_places {
                            if (decimals > decimal_places) & (normalized_decimals > decimal_places) {
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

                                if (whole_digits > max_whole_digits)
                                    & (normalized_whole_digits > normalized_max_whole_digits)
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
                };
            }
        }

        if let Some(multiple_of) = &self.multiple_of {
            // fraction = (decimal / multiple_of) % 1
            let fraction: &PyAny = unsafe {
                let division = PyObject::from_owned_ptr_or_err(
                    py,
                    pyo3::ffi::PyNumber_TrueDivide(decimal.as_ptr(), multiple_of.as_ptr()),
                )?;
                let one = 1.to_object(py);
                py.from_owned_ptr_or_err(pyo3::ffi::PyNumber_Remainder(division.as_ptr(), one.as_ptr()))?
            };
            let zero = 0.to_object(py);
            if !fraction.eq(&zero)? {
                return Err(ValError::new(
                    ErrorType::MultipleOf {
                        multiple_of: multiple_of.to_string().into(),
                        context: Some([("multiple_of", multiple_of)].into_py_dict(py).into()),
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

        if let Some(le) = &self.le {
            if is_nan()? || !decimal.le(le)? {
                return Err(ValError::new(
                    ErrorType::LessThanEqual {
                        le: Number::String(le.to_string()),
                        context: Some([("le", le)].into_py_dict(py).into()),
                    },
                    input,
                ));
            }
        }
        if let Some(lt) = &self.lt {
            if is_nan()? || !decimal.lt(lt)? {
                return Err(ValError::new(
                    ErrorType::LessThan {
                        lt: Number::String(lt.to_string()),
                        context: Some([("lt", lt)].into_py_dict(py).into()),
                    },
                    input,
                ));
            }
        }
        if let Some(ge) = &self.ge {
            if is_nan()? || !decimal.ge(ge)? {
                return Err(ValError::new(
                    ErrorType::GreaterThanEqual {
                        ge: Number::String(ge.to_string()),
                        context: Some([("ge", ge)].into_py_dict(py).into()),
                    },
                    input,
                ));
            }
        }
        if let Some(gt) = &self.gt {
            if is_nan()? || !decimal.gt(gt)? {
                return Err(ValError::new(
                    ErrorType::GreaterThan {
                        gt: Number::String(gt.to_string()),
                        context: Some([("gt", gt)].into_py_dict(py).into()),
                    },
                    input,
                ));
            }
        }

        Ok(decimal.into())
    }

    fn different_strict_behavior(&self, _ultra_strict: bool) -> bool {
        true
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }

    fn complete(&self) -> PyResult<()> {
        Ok(())
    }
}

pub(crate) fn create_decimal<'a>(
    arg: &'a PyAny,
    input: &'a impl Input<'a>,
    py: Python<'a>,
) -> ValResult<'a, &'a PyAny> {
    let decimal_type_obj: Py<PyType> = get_decimal_type(py);
    decimal_type_obj
        .call1(py, (arg,))
        .map_err(|e| {
            let decimal_exception = match arg
                .py()
                .import("decimal")
                .and_then(|decimal_module| decimal_module.getattr("DecimalException"))
            {
                Ok(decimal_exception) => decimal_exception,
                Err(e) => return ValError::InternalErr(e),
            };
            handle_decimal_new_error(arg.py(), input.as_error_value(), e, decimal_exception)
        })
        .map(|v| v.into_ref(py))
}

fn handle_decimal_new_error<'a>(
    py: Python<'a>,
    input: InputValue<'a>,
    error: PyErr,
    decimal_exception: &'a PyAny,
) -> ValError<'a> {
    if error.matches(py, decimal_exception) {
        ValError::new_custom_input(ErrorTypeDefaults::DecimalParsing, input)
    } else if error.matches(py, PyTypeError::type_object(py)) {
        ValError::new_custom_input(ErrorTypeDefaults::DecimalType, input)
    } else {
        ValError::InternalErr(error)
    }
}
