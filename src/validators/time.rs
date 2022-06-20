use pyo3::prelude::*;
use pyo3::types::{PyDict, PyTime};
use speedate::Time;

use crate::build_tools::{is_strict, SchemaDict};
use crate::errors::{as_internal, context, err_val_error, ErrorKind, ValResult};
use crate::input::{pytime_as_time, EitherTime, Input};

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
                ($constraint:ident, $error:path, $key:literal) => {
                    if let Some(constraint) = &constraints.$constraint {
                        if !raw_time.$constraint(constraint) {
                            return err_val_error!(
                                input_value = input.as_error_value(),
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
        time.try_into_py(py).map_err(as_internal)
    }
}

fn convert_pytime(schema: &PyDict, field: &str) -> PyResult<Option<Time>> {
    let py_time: Option<&PyTime> = schema.get_as(field)?;
    match py_time {
        Some(py_time) => Ok(Some(pytime_as_time!(py_time))),
        None => Ok(None),
    }
}
