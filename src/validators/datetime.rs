use pyo3::prelude::*;
use pyo3::types::{PyDateTime, PyDict};
use speedate::DateTime;

use crate::build_tools::{is_strict, SchemaDict};
use crate::errors::{as_internal, context, err_val_error, ErrorKind, InputValue, ValResult};
use crate::input::{pydatetime_as_datetime, EitherDateTime, Input};

use super::{BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct DateTimeValidator {
    strict: bool,
    constraints: Option<DateTimeConstraints>,
}

#[derive(Debug, Clone)]
struct DateTimeConstraints {
    le: Option<DateTime>,
    lt: Option<DateTime>,
    ge: Option<DateTime>,
    gt: Option<DateTime>,
}

impl BuildValidator for DateTimeValidator {
    const EXPECTED_TYPE: &'static str = "datetime";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        _build_context: &mut BuildContext,
    ) -> PyResult<CombinedValidator> {
        let has_constraints = schema.get_item("le").is_some()
            || schema.get_item("lt").is_some()
            || schema.get_item("ge").is_some()
            || schema.get_item("gt").is_some();

        Ok(Self {
            strict: is_strict(schema, config)?,
            constraints: match has_constraints {
                true => Some(DateTimeConstraints {
                    le: py_datetime_as_datetime(schema, "le")?,
                    lt: py_datetime_as_datetime(schema, "lt")?,
                    ge: py_datetime_as_datetime(schema, "ge")?,
                    gt: py_datetime_as_datetime(schema, "gt")?,
                }),
                false => None,
            },
        }
        .into())
    }
}

impl Validator for DateTimeValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        let date = match self.strict {
            true => input.strict_datetime()?,
            false => input.lax_datetime()?,
        };
        self.validation_comparison(py, input, date)
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        self.validation_comparison(py, input, input.strict_datetime()?)
    }

    fn get_name(&self, _py: Python) -> String {
        Self::EXPECTED_TYPE.to_string()
    }
}

impl DateTimeValidator {
    fn validation_comparison<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        datetime: EitherDateTime,
    ) -> ValResult<'data, PyObject> {
        if let Some(constraints) = &self.constraints {
            // if we get an error from as_speedate, it's probably because the input datetime was invalid
            // specifically had an invalid tzinfo, hence here we return a validation error
            let speedate_dt = match datetime.as_raw() {
                Ok(dt) => dt,
                Err(err) => {
                    let error_name = err.get_type(py).name().map_err(as_internal)?;
                    return err_val_error!(
                        input_value = InputValue::InputRef(input),
                        kind = ErrorKind::DateTimeObjectInvalid,
                        context = context!("processing_error" => error_name)
                    );
                }
            };
            macro_rules! check_constraint {
                ($constraint:ident, $error:path, $key:literal) => {
                    if let Some(constraint) = &constraints.$constraint {
                        if !speedate_dt.$constraint(constraint) {
                            return err_val_error!(
                                input_value = InputValue::InputRef(input),
                                kind = $error,
                                context = context!($key => constraint.to_string())
                            );
                        }
                    }
                };
            }

            check_constraint!(le, ErrorKind::LessThanEqual, "le");
            check_constraint!(lt, ErrorKind::LessThan, "lt");
            check_constraint!(ge, ErrorKind::GreaterThanEqual, "ge");
            check_constraint!(gt, ErrorKind::GreaterThan, "gt");
        }
        datetime.try_into_py(py).map_err(as_internal)
    }
}

fn py_datetime_as_datetime(schema: &PyDict, field: &str) -> PyResult<Option<DateTime>> {
    let py_dt: Option<&PyDateTime> = schema.get_as(field)?;
    match py_dt {
        Some(py_dt) => pydatetime_as_datetime(py_dt).map(Some),
        None => Ok(None),
    }
}
