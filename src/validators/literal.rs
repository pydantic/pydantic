use std::hash::BuildHasherDefault;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyString};

use ahash::AHashSet;

use crate::build_tools::{py_error, SchemaDict};
use crate::errors::{ErrorKind, ValError, ValResult};
use crate::input::Input;
use crate::recursion_guard::{NoHashSet, RecursionGuard};

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
        let expected: &PyList = schema.get_as_req(intern!(schema.py(), "expected"))?;
        if expected.is_empty() {
            return py_error!(r#""expected" should have length > 0"#);
        } else if expected.len() == 1 {
            let first = expected.get_item(0)?;
            if let Ok(py_str) = first.cast_as::<PyString>() {
                return Ok(LiteralSingleStringValidator::new(py_str.to_str()?.to_string()).into());
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
    name: String,
}

impl LiteralSingleStringValidator {
    fn new(expected: String) -> Self {
        let repr = format!("'{}'", expected);
        let name = format!("literal[{}]", repr);
        Self { expected, repr, name }
    }
}

impl Validator for LiteralSingleStringValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let either_str = input.strict_str()?;
        if either_str.as_cow()?.as_ref() == self.expected.as_str() {
            Ok(input.to_object(py))
        } else {
            Err(ValError::new(
                ErrorKind::LiteralSingleError {
                    expected: self.repr.clone(),
                },
                input,
            ))
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}

#[derive(Debug, Clone)]
pub struct LiteralSingleIntValidator {
    expected: i64,
    name: String,
}

impl LiteralSingleIntValidator {
    fn new(expected: i64) -> Self {
        Self {
            expected,
            name: format!("literal[{}]", expected),
        }
    }
}

impl Validator for LiteralSingleIntValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let str = input.strict_int()?;
        if str == self.expected {
            Ok(input.to_object(py))
        } else {
            Err(ValError::new(
                ErrorKind::LiteralSingleError {
                    expected: self.expected.to_string(),
                },
                input,
            ))
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}

#[derive(Debug, Clone)]
pub struct LiteralMultipleStringsValidator {
    expected: AHashSet<String>,
    repr: String,
    name: String,
}

impl LiteralMultipleStringsValidator {
    fn new(expected_list: &PyList) -> Option<Self> {
        let mut expected: AHashSet<String> = AHashSet::new();
        let mut repr_args = Vec::new();
        for item in expected_list.iter() {
            if let Ok(str) = item.extract() {
                repr_args.push(format!("'{}'", str));
                expected.insert(str);
            } else {
                return None;
            }
        }
        let repr = repr_args.join(", ");
        let name = format!("literal[{}]", repr);
        Some(Self { expected, repr, name })
    }
}

impl Validator for LiteralMultipleStringsValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let either_str = input.strict_str()?;
        if self.expected.contains(either_str.as_cow()?.as_ref()) {
            Ok(input.to_object(py))
        } else {
            Err(ValError::new(
                ErrorKind::LiteralMultipleError {
                    expected: self.repr.clone(),
                },
                input,
            ))
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}

#[derive(Debug, Clone)]
pub struct LiteralMultipleIntsValidator {
    expected: NoHashSet<i64>,
    repr: String,
    name: String,
}

impl LiteralMultipleIntsValidator {
    fn new(expected_list: &PyList) -> Option<Self> {
        let mut expected: NoHashSet<i64> = NoHashSet::with_hasher(BuildHasherDefault::default());
        let mut repr_args = Vec::new();
        for item in expected_list.iter() {
            if let Ok(str) = item.extract() {
                expected.insert(str);
                repr_args.push(str.to_string());
            } else {
                return None;
            }
        }
        let repr = repr_args.join(", ");
        let name = format!("literal[{}]", repr);
        Some(Self { expected, repr, name })
    }
}

impl Validator for LiteralMultipleIntsValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let int = input.strict_int()?;
        if self.expected.contains(&int) {
            Ok(input.to_object(py))
        } else {
            Err(ValError::new(
                ErrorKind::LiteralMultipleError {
                    expected: self.repr.clone(),
                },
                input,
            ))
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}

#[derive(Debug, Clone)]
pub struct LiteralGeneralValidator {
    expected_int: AHashSet<i64>,
    expected_str: AHashSet<String>,
    expected_py: Py<PyList>,
    repr: String,
    name: String,
}

impl LiteralGeneralValidator {
    fn new(expected: &PyList) -> PyResult<Self> {
        let mut expected_int = AHashSet::new();
        let mut expected_str = AHashSet::new();
        let py = expected.py();
        let expected_py = PyList::empty(py);
        let mut repr_args: Vec<String> = Vec::new();
        for item in expected.iter() {
            repr_args.push(item.repr()?.extract()?);
            if let Ok(int) = item.extract::<i64>() {
                expected_int.insert(int);
            } else if let Ok(py_str) = item.cast_as::<PyString>() {
                expected_str.insert(py_str.to_str()?.to_string());
            } else {
                expected_py.append(item)?;
            }
        }
        let repr = repr_args.join(", ");
        let name = format!("literal[{}]", repr);
        Ok(Self {
            expected_int,
            expected_str,
            expected_py: expected_py.into_py(py),
            repr,
            name,
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
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        if !self.expected_int.is_empty() {
            if let Ok(int) = input.strict_int() {
                if self.expected_int.contains(&int) {
                    return Ok(input.to_object(py));
                }
            }
        }
        if !self.expected_str.is_empty() {
            if let Ok(either_str) = input.strict_str() {
                if self.expected_str.contains(either_str.as_cow()?.as_ref()) {
                    return Ok(input.to_object(py));
                }
            }
        }

        let py_value = input.to_object(py);

        let expected_py = self.expected_py.as_ref(py);
        if !expected_py.is_empty() && expected_py.contains(&py_value)? {
            return Ok(py_value);
        }

        Err(ValError::new(
            ErrorKind::LiteralMultipleError {
                expected: self.repr.clone(),
            },
            input,
        ))
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}
