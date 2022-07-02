use pyo3::prelude::*;
use pyo3::types::PyDict;
use speedate::Time;

use crate::build_tools::{is_strict, SchemaDict, SchemaError};
use crate::errors::{as_internal, ErrorKind, ValError, ValResult};
use crate::input::{EitherTime, Input};
use crate::recursion_guard::RecursionGuard;

use super::{BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct TimeValidator {
    strict: bool,
    constraints: Option<TimeConstraints>,
}

#[derive(Debug, Clone)]
struct TimeConstraints {
    le: Option<Time>,
    lt: Option<Time>,
    ge: Option<Time>,
    gt: Option<Time>,
}

impl BuildValidator for TimeValidator {
    const EXPECTED_TYPE: &'static str = "time";

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
                true => Some(TimeConstraints {
                    le: convert_pytime(schema, "le")?,
                    lt: convert_pytime(schema, "lt")?,
                    ge: convert_pytime(schema, "ge")?,
                    gt: convert_pytime(schema, "gt")?,
                }),
                false => None,
            },
        }
        .into())
    }
}

impl Validator for TimeValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let time = match self.strict {
            true => input.strict_time()?,
            false => input.lax_time()?,
        };
        self.validation_comparison(py, input, time)
    }

    fn validate_strict<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        self.validation_comparison(py, input, input.strict_time()?)
    }

    fn get_name(&self, _py: Python) -> String {
        Self::EXPECTED_TYPE.to_string()
    }
}

impl TimeValidator {
    fn validation_comparison<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        time: EitherTime<'data>,
    ) -> ValResult<'data, PyObject> {
        if let Some(constraints) = &self.constraints {
            let raw_time = time.as_raw().map_err(as_internal)?;

            macro_rules! check_constraint {
                ($constraint:ident, $error:ident) => {
                    if let Some(constraint) = &constraints.$constraint {
                        if !raw_time.$constraint(constraint) {
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
        time.try_into_py(py).map_err(as_internal)
    }
}

fn convert_pytime(schema: &PyDict, field: &str) -> PyResult<Option<Time>> {
    match schema.get_as::<&PyAny>(field)? {
        Some(obj) => {
            let prefix = format!(r#"Invalid "{}" constraint for time"#, field);
            let date = obj
                .lax_time()
                .map_err(|e| SchemaError::from_val_error(obj.py(), &prefix, e))?;
            Ok(Some(date.as_raw()?))
        }
        None => Ok(None),
    }
}
