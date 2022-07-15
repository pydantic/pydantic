use pyo3::prelude::*;
use pyo3::types::PyDict;
use speedate::DateTime;

use crate::build_tools::{is_strict, SchemaDict, SchemaError};
use crate::errors::{py_err_string, ErrorKind, ValError, ValResult};
use crate::input::Input;
use crate::recursion_guard::RecursionGuard;

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
        input: &'data impl Input<'data>,
        extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let datetime = input.validate_datetime(extra.strict.unwrap_or(self.strict))?;
        if let Some(constraints) = &self.constraints {
            // if we get an error from as_speedate, it's probably because the input datetime was invalid
            // specifically had an invalid tzinfo, hence here we return a validation error
            let speedate_dt = match datetime.as_raw() {
                Ok(dt) => dt,
                Err(err) => {
                    let error = py_err_string(py, err);
                    return Err(ValError::new(ErrorKind::DateTimeObjectInvalid { error }, input));
                }
            };
            macro_rules! check_constraint {
                ($constraint:ident, $error:ident) => {
                    if let Some(constraint) = &constraints.$constraint {
                        if !speedate_dt.$constraint(constraint) {
                            return Err(ValError::new(
                                ErrorKind::$error {
                                    $constraint: constraint.to_string(),
                                },
                                input,
                            ));
                        }
                    }
                };
            }

            check_constraint!(le, LessThanEqual);
            check_constraint!(lt, LessThan);
            check_constraint!(ge, GreaterThanEqual);
            check_constraint!(gt, GreaterThan);
        }
        Ok(datetime.try_into_py(py)?)
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}

fn py_datetime_as_datetime(schema: &PyDict, field: &str) -> PyResult<Option<DateTime>> {
    match schema.get_as::<&PyAny>(field)? {
        Some(obj) => {
            let prefix = format!(r#"Invalid "{}" constraint for datetime"#, field);
            let date = obj
                .validate_datetime(false)
                .map_err(|e| SchemaError::from_val_error(obj.py(), &prefix, e))?;
            Ok(Some(date.as_raw()?))
        }
        None => Ok(None),
    }
}
