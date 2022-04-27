use std::collections::HashSet;

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use crate::build_tools::{py_error, SchemaDict};
use crate::errors::{as_internal, context, err_val_error, ErrorKind, InputValue, ValResult};
use crate::input::Input;

use super::{unused_validator, validator_boilerplate, Extra, Validator};

#[derive(Debug)]
pub struct LiteralValidator;

impl LiteralValidator {
    pub const EXPECTED_TYPE: &'static str = "literal";
}

impl Validator for LiteralValidator {
    fn build(schema: &PyDict, _config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        let expected: &PyList = schema.get_as_req("expected")?;
        if expected.is_empty() {
            return py_error!(r#""expected" must have length > 0"#);
        } else if expected.len() == 1 {
            let first = expected.get_item(0)?;
            if let Ok(str) = first.extract::<String>() {
                return Ok(Box::new(SingleStringValidator::new(str)));
            }
            if let Ok(int) = first.extract::<i64>() {
                return Ok(Box::new(SingleIntValidator::new(int)));
            }
        }

        if let Some(v) = MultipleStringsValidator::new(expected) {
            Ok(Box::new(v))
        } else if let Some(v) = MultipleIntsValidator::new(expected) {
            Ok(Box::new(v))
        } else {
            Ok(Box::new(GeneralValidator::new(expected)?))
        }
    }

    unused_validator!("LiteralValidator");
}

#[derive(Debug, Clone)]
struct SingleStringValidator {
    expected: String,
    repr: String,
}

impl SingleStringValidator {
    fn new(expected: String) -> Self {
        let repr = format!("'{}'", expected);
        Self { expected, repr }
    }
}

impl Validator for SingleStringValidator {
    #[no_coverage]
    fn build(_schema: &PyDict, _config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        unimplemented!("use ::new(value) instead")
    }

    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        let str = input.strict_str(py)?;
        if str == self.expected {
            Ok(input.to_py(py))
        } else {
            err_val_error!(
                input_value = InputValue::InputRef(input),
                kind = ErrorKind::LiteralSingleError,
                context = context!("expected" => self.repr.clone()),
            )
        }
    }

    validator_boilerplate!("literal-single-string");
}

#[derive(Debug, Clone)]
struct SingleIntValidator {
    expected: i64,
}

impl SingleIntValidator {
    fn new(expected: i64) -> Self {
        Self { expected }
    }
}

impl Validator for SingleIntValidator {
    #[no_coverage]
    fn build(_schema: &PyDict, _config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        unimplemented!("use ::new(value) instead")
    }

    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        let str = input.strict_int(py)?;
        if str == self.expected {
            Ok(input.to_py(py))
        } else {
            err_val_error!(
                input_value = InputValue::InputRef(input),
                kind = ErrorKind::LiteralSingleError,
                context = context!("expected" => self.expected)
            )
        }
    }

    validator_boilerplate!("literal-single-int");
}

#[derive(Debug, Clone)]
struct MultipleStringsValidator {
    expected: HashSet<String>,
    repr: String,
}

impl MultipleStringsValidator {
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

impl Validator for MultipleStringsValidator {
    #[no_coverage]
    fn build(_schema: &PyDict, _config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        unimplemented!("use ::new(value) instead")
    }

    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        let str = input.strict_str(py)?;
        if self.expected.contains(&str) {
            Ok(input.to_py(py))
        } else {
            err_val_error!(
                input_value = InputValue::InputRef(input),
                kind = ErrorKind::LiteralMultipleError,
                context = context!("expected" => self.repr.clone()),
            )
        }
    }

    validator_boilerplate!("literal-multiple-strings");
}

#[derive(Debug, Clone)]
struct MultipleIntsValidator {
    expected: HashSet<i64>,
    repr: String,
}

impl MultipleIntsValidator {
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

impl Validator for MultipleIntsValidator {
    #[no_coverage]
    fn build(_schema: &PyDict, _config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        unimplemented!("use ::new(value) instead")
    }

    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        let int = input.strict_int(py)?;
        if self.expected.contains(&int) {
            Ok(input.to_py(py))
        } else {
            err_val_error!(
                input_value = InputValue::InputRef(input),
                kind = ErrorKind::LiteralMultipleError,
                context = context!("expected" => self.repr.clone())
            )
        }
    }

    validator_boilerplate!("literal-multiple-ints");
}

#[derive(Debug, Clone)]
struct GeneralValidator {
    expected_int: HashSet<i64>,
    expected_str: HashSet<String>,
    expected_py: Py<PyList>,
    repr: String,
}

impl GeneralValidator {
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

impl Validator for GeneralValidator {
    #[no_coverage]
    fn build(_schema: &PyDict, _config: Option<&PyDict>) -> PyResult<Box<dyn Validator>> {
        unimplemented!("use ::new(value) instead")
    }

    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data dyn Input,
        _extra: &Extra,
    ) -> ValResult<'data, PyObject> {
        if !self.expected_int.is_empty() {
            if let Ok(int) = input.strict_int(py) {
                if self.expected_int.contains(&int) {
                    return Ok(input.to_py(py));
                }
            }
        }
        if !self.expected_str.is_empty() {
            if let Ok(str) = input.strict_str(py) {
                if self.expected_str.contains(&str) {
                    return Ok(input.to_py(py));
                }
            }
        }

        let py_value = input.to_py(py);

        let expected_py = self.expected_py.as_ref(py);
        if !expected_py.is_empty() && expected_py.contains(&py_value).map_err(as_internal)? {
            return Ok(py_value);
        }

        err_val_error!(
            input_value = InputValue::PyObject(py_value),
            kind = ErrorKind::LiteralMultipleError,
            context = context!("expected" => self.repr.clone())
        )
    }

    validator_boilerplate!("literal-general");
}
