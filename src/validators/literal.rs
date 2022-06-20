use std::collections::HashSet;

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use crate::build_tools::{py_error, SchemaDict};
use crate::errors::{as_internal, context, err_val_error, ErrorKind, ValResult};
use crate::input::Input;

use super::{BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug)]
pub struct LiteralBuilder;

impl BuildValidator for LiteralBuilder {
    const EXPECTED_TYPE: &'static str = "literal";

    fn build(
        schema: &PyDict,
        _config: Option<&PyDict>,
        _build_context: &mut BuildContext,
    ) -> PyResult<CombinedValidator> {
        let expected: &PyList = schema.get_as_req("expected")?;
        if expected.is_empty() {
            return py_error!(r#""expected" must have length > 0"#);
        } else if expected.len() == 1 {
            let first = expected.get_item(0)?;
            if let Ok(str) = first.extract::<String>() {
                return Ok(LiteralSingleStringValidator::new(str).into());
            }
            if let Ok(int) = first.extract::<i64>() {
                return Ok(LiteralSingleIntValidator::new(int).into());
            }
        }

        if let Some(v) = LiteralMultipleStringsValidator::new(expected) {
            Ok(v.into())
        } else if let Some(v) = LiteralMultipleIntsValidator::new(expected) {
            Ok(v.into())
        } else {
            Ok(LiteralGeneralValidator::new(expected)?.into())
        }
    }
}

#[derive(Debug, Clone)]
pub struct LiteralSingleStringValidator {
    expected: String,
    repr: String,
}

impl LiteralSingleStringValidator {
    fn new(expected: String) -> Self {
        let repr = format!("'{}'", expected);
        Self { expected, repr }
    }
}

impl Validator for LiteralSingleStringValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        let str = input.strict_str()?;
        if str == self.expected {
            Ok(input.to_object(py))
        } else {
            err_val_error!(
                input_value = input.as_error_value(),
                kind = ErrorKind::LiteralSingleError,
                context = context!("expected" => self.repr.clone()),
            )
        }
    }

    fn get_name(&self, _py: Python) -> String {
        "literal-single-string".to_string()
    }
}

#[derive(Debug, Clone)]
pub struct LiteralSingleIntValidator {
    expected: i64,
}

impl LiteralSingleIntValidator {
    fn new(expected: i64) -> Self {
        Self { expected }
    }
}

impl Validator for LiteralSingleIntValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        let str = input.strict_int()?;
        if str == self.expected {
            Ok(input.to_object(py))
        } else {
            err_val_error!(
                input_value = input.as_error_value(),
                kind = ErrorKind::LiteralSingleError,
                context = context!("expected" => self.expected)
            )
        }
    }

    fn get_name(&self, _py: Python) -> String {
        "literal-single-int".to_string()
    }
}

#[derive(Debug, Clone)]
pub struct LiteralMultipleStringsValidator {
    expected: HashSet<String>,
    repr: String,
}

impl LiteralMultipleStringsValidator {
    fn new(expected_list: &PyList) -> Option<Self> {
        let mut expected: HashSet<String> = HashSet::new();
        let mut repr_args = Vec::new();
        for item in expected_list.iter() {
            if let Ok(str) = item.extract() {
                repr_args.push(format!("'{}'", str));
                expected.insert(str);
            } else {
                return None;
            }
        }

        Some(Self {
            expected,
            repr: repr_args.join(", "),
        })
    }
}

impl Validator for LiteralMultipleStringsValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        let str = input.strict_str()?;
        if self.expected.contains(&str) {
            Ok(input.to_object(py))
        } else {
            err_val_error!(
                input_value = input.as_error_value(),
                kind = ErrorKind::LiteralMultipleError,
                context = context!("expected" => self.repr.clone()),
            )
        }
    }

    fn get_name(&self, _py: Python) -> String {
        "literal-multiple-strings".to_string()
    }
}

#[derive(Debug, Clone)]
pub struct LiteralMultipleIntsValidator {
    expected: HashSet<i64>,
    repr: String,
}

impl LiteralMultipleIntsValidator {
    fn new(expected_list: &PyList) -> Option<Self> {
        let mut expected: HashSet<i64> = HashSet::new();
        let mut repr_args = Vec::new();
        for item in expected_list.iter() {
            if let Ok(str) = item.extract() {
                expected.insert(str);
                repr_args.push(str.to_string());
            } else {
                return None;
            }
        }

        Some(Self {
            expected,
            repr: repr_args.join(", "),
        })
    }
}

impl Validator for LiteralMultipleIntsValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        let int = input.strict_int()?;
        if self.expected.contains(&int) {
            Ok(input.to_object(py))
        } else {
            err_val_error!(
                input_value = input.as_error_value(),
                kind = ErrorKind::LiteralMultipleError,
                context = context!("expected" => self.repr.clone())
            )
        }
    }

    fn get_name(&self, _py: Python) -> String {
        "literal-multiple-ints".to_string()
    }
}

#[derive(Debug, Clone)]
pub struct LiteralGeneralValidator {
    expected_int: HashSet<i64>,
    expected_str: HashSet<String>,
    expected_py: Py<PyList>,
    repr: String,
}

impl LiteralGeneralValidator {
    fn new(expected: &PyList) -> PyResult<Self> {
        let mut expected_int = HashSet::new();
        let mut expected_str = HashSet::new();
        let py = expected.py();
        let expected_py = PyList::empty(py);
        let mut repr_args: Vec<String> = Vec::new();
        for item in expected.iter() {
            repr_args.push(item.repr()?.extract()?);
            if let Ok(int) = item.extract::<i64>() {
                expected_int.insert(int);
            } else if let Ok(str) = item.extract::<String>() {
                expected_str.insert(str);
            } else {
                expected_py.append(item)?;
            }
        }
        Ok(Self {
            expected_int,
            expected_str,
            expected_py: expected_py.into_py(py),
            repr: repr_args.join(", "),
        })
    }
}

impl Validator for LiteralGeneralValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
    ) -> ValResult<'data, PyObject> {
        if !self.expected_int.is_empty() {
            if let Ok(int) = input.strict_int() {
                if self.expected_int.contains(&int) {
                    return Ok(input.to_object(py));
                }
            }
        }
        if !self.expected_str.is_empty() {
            if let Ok(str) = input.strict_str() {
                if self.expected_str.contains(&str) {
                    return Ok(input.to_object(py));
                }
            }
        }

        let py_value = input.to_object(py);

        let expected_py = self.expected_py.as_ref(py);
        if !expected_py.is_empty() && expected_py.contains(&py_value).map_err(as_internal)? {
            return Ok(py_value);
        }

        err_val_error!(
            input_value = input.as_error_value(),
            kind = ErrorKind::LiteralMultipleError,
            context = context!("expected" => self.repr.clone())
        )
    }

    fn get_name(&self, _py: Python) -> String {
        "literal-general".to_string()
    }
}
