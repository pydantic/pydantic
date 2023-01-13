use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDelta, PyDict, PyString};
use speedate::Duration;

use crate::build_tools::{is_strict, SchemaDict};
use crate::errors::{ErrorType, ValError, ValResult};
use crate::input::{EitherTimedelta, Input};
use crate::recursion_guard::RecursionGuard;

use super::{BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct TimeDeltaValidator {
    strict: bool,
    constraints: Option<TimedeltaConstraints>,
}

#[derive(Debug, Clone)]
struct TimedeltaConstraints {
    le: Option<Duration>,
    lt: Option<Duration>,
    ge: Option<Duration>,
    gt: Option<Duration>,
}
impl BuildValidator for TimeDeltaValidator {
    const EXPECTED_TYPE: &'static str = "timedelta";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        _build_context: &mut BuildContext<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let has_constraints = schema.get_item(intern!(py, "le")).is_some()
            || schema.get_item(intern!(py, "lt")).is_some()
            || schema.get_item(intern!(py, "ge")).is_some()
            || schema.get_item(intern!(py, "gt")).is_some();

        Ok(Self {
            strict: is_strict(schema, config)?,
            constraints: match has_constraints {
                true => Some(TimedeltaConstraints {
                    le: py_timedelta_as_timedelta(schema, intern!(py, "le"))?,
                    lt: py_timedelta_as_timedelta(schema, intern!(py, "lt"))?,
                    ge: py_timedelta_as_timedelta(schema, intern!(py, "ge"))?,
                    gt: py_timedelta_as_timedelta(schema, intern!(py, "gt"))?,
                }),
                false => None,
            },
        }
        .into())
    }
}

impl Validator for TimeDeltaValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let timedelta = input.validate_timedelta(extra.strict.unwrap_or(self.strict))?;
        if let Some(constraints) = &self.constraints {
            let raw_timedelta = timedelta.as_raw();

            macro_rules! check_constraint {
                ($constraint:ident, $error:ident) => {
                    if let Some(constraint) = &constraints.$constraint {
                        if !raw_timedelta.$constraint(constraint) {
                            return Err(ValError::new(
                                ErrorType::$error {
                                    $constraint: constraint.to_string().into(),
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
        Ok(timedelta.try_into_py(py)?)
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}

fn py_timedelta_as_timedelta(schema: &PyDict, field: &PyString) -> PyResult<Option<Duration>> {
    match schema.get_as::<&PyDelta>(field)? {
        Some(timedelta) => Ok(Some(EitherTimedelta::Py(timedelta).as_raw())),
        None => Ok(None),
    }
}
