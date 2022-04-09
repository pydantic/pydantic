use std::fmt::Debug;

use pyo3::exceptions::{PyKeyError, PyTypeError};
use pyo3::prelude::*;
use pyo3::types::{IntoPyDict, PyAny, PyBool, PyDict, PyString};
use pyo3::ToPyObject;

use crate::utils::{dict_get, py_error, RegexPattern};
use crate::validator_functions::validate_str;

trait TypeValidator: Send + Debug {
    fn is_match(type_: &str, dict_: &PyDict) -> bool
    where
        Self: Sized;

    fn build(dict: &PyDict) -> PyResult<Self>
    where
        Self: Sized;

    fn validate(&self, py: Python, obj: PyObject) -> PyResult<PyObject>;

    fn clone_dyn(&self) -> Box<dyn TypeValidator>;
}

#[derive(Debug, Clone)]
struct NullValidator;

impl TypeValidator for NullValidator {
    fn is_match(type_: &str, _dict: &PyDict) -> bool {
        type_ == "null"
    }

    fn build(_dict: &PyDict) -> PyResult<Self> {
        Ok(Self)
    }

    fn validate(&self, py: Python, _obj: PyObject) -> PyResult<PyObject> {
        Ok(py.None())
    }

    fn clone_dyn(&self) -> Box<dyn TypeValidator> {
        Box::new(self.clone())
    }
}

#[derive(Debug, Clone)]
struct BoolValidator;

impl TypeValidator for BoolValidator {
    fn is_match(type_: &str, _dict: &PyDict) -> bool {
        type_ == "boolean"
    }

    fn build(_dict: &PyDict) -> PyResult<Self> {
        Ok(Self)
    }

    fn validate(&self, py: Python, obj: PyObject) -> PyResult<PyObject> {
        let obj: &PyBool = obj.extract(py)?;
        Ok(obj.to_object(py))
    }

    fn clone_dyn(&self) -> Box<dyn TypeValidator> {
        Box::new(self.clone())
    }
}

#[derive(Debug, Clone)]
struct SimpleStringValidator;

impl TypeValidator for SimpleStringValidator {
    fn is_match(type_: &str, dict: &PyDict) -> bool {
        type_ == "string"
            && dict.get_item("pattern").is_none()
            && dict.get_item("min_length").is_none()
            && dict.get_item("max_length").is_none()
            && dict.get_item("strip_whitespace").is_none()
            && dict.get_item("to_lower").is_none()
            && dict.get_item("to_upper").is_none()
    }

    fn build(_dict: &PyDict) -> PyResult<Self> {
        Ok(Self)
    }

    fn validate(&self, py: Python, obj: PyObject) -> PyResult<PyObject> {
        let obj: &PyAny = obj.extract(py)?;
        let s = validate_str(obj)?;
        Ok(s.to_object(py))
    }

    fn clone_dyn(&self) -> Box<dyn TypeValidator> {
        Box::new(self.clone())
    }
}

#[derive(Debug, Clone)]
struct FullStringValidator {
    pattern: Option<RegexPattern>,
    max_length: Option<usize>,
    min_length: Option<usize>,
    strip_whitespace: bool,
    to_lower: bool,
    to_upper: bool,
}

impl TypeValidator for FullStringValidator {
    fn is_match(type_: &str, _dict: &PyDict) -> bool {
        type_ == "string"
    }

    fn build(dict: &PyDict) -> PyResult<Self> {
        let pattern = match dict.get_item("pattern") {
            Some(s) => Some(RegexPattern::py_new(s)?.into()),
            None => None,
        };
        let min_length = dict_get!(dict, "min_length", usize);
        let max_length = dict_get!(dict, "max_length", usize);
        let strip_whitespace = dict_get!(dict, "strip_whitespace", bool);
        let to_lower = dict_get!(dict, "to_lower", bool);
        let to_upper = dict_get!(dict, "to_upper", bool);

        Ok(Self {
            pattern,
            min_length,
            max_length,
            strip_whitespace: strip_whitespace.unwrap_or(false),
            to_lower: to_lower.unwrap_or(false),
            to_upper: to_upper.unwrap_or(false),
        })
    }

    fn validate(&self, py: Python, obj: PyObject) -> PyResult<PyObject> {
        let obj: &PyAny = obj.extract(py)?;
        let mut str = validate_str(obj)?;
        if let Some(min_length) = self.min_length {
            if str.len() < min_length {
                return py_error!("{} is shorter than {}", str, min_length);
            }
        }
        if let Some(max_length) = self.max_length {
            if str.len() > max_length {
                return py_error!("{} is longer than {}", str, max_length);
            }
        }
        if let Some(pattern) = &self.pattern {
            if !pattern.is_match(&str) {
                return py_error!("{} does not match {}", str, pattern);
            }
        }

        if self.strip_whitespace {
            str = str.trim().to_string();
        }

        if self.to_lower {
            str = str.to_lowercase()
        } else if self.to_upper {
            str = str.to_uppercase()
        }
        let py_str = PyString::new(py, &str);
        Ok(py_str.to_object(py))
    }

    fn clone_dyn(&self) -> Box<dyn TypeValidator> {
        Box::new(self.clone())
    }
}

fn find_type_validator(dict: &PyDict) -> PyResult<Box<dyn TypeValidator>> {
    let type_: String = dict_get!(dict, "type", String).ok_or(PyKeyError::new_err("'type' is required"))?;

    macro_rules! if_else {
        ($validator:ident else $else:tt) => {
            if $validator::is_match(&type_, dict) {
                let val = $validator::build(dict)?;
                return Ok(Box::new(val));
            } else {
                $else
            }
        };
    }

    macro_rules! all_validators {
        ($validator:ident) => {
            if_else!($validator else {
                return py_error!("unknown type: '{}'", type_);
            })
        };
        ($validator:ident, $($validators:ident),+) => {
            if_else!($validator else {
                all_validators!($($validators),+)
            })
        };
    }

    // order matters here!
    // e.g. SimpleStringValidator must come before FullStringValidator
    all_validators!(NullValidator, BoolValidator, SimpleStringValidator, FullStringValidator)
}

impl Clone for Box<dyn TypeValidator> {
    fn clone(&self) -> Self {
        self.clone_dyn()
    }
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct Validator {
    type_validator: Box<dyn TypeValidator>,
    external_validator: Option<PyObject>,
}

#[pymethods]
impl Validator {
    #[new]
    pub fn py_new(pattern: &PyAny) -> PyResult<Self> {
        let dict: &PyDict = pattern.extract()?;
        let type_validator = find_type_validator(dict)?;
        let external_validator = match dict.get_item("external_validator") {
            Some(obj) => {
                if !obj.is_callable() {
                    return py_error!(PyTypeError; "'external_validator' must be callable");
                }
                Some(obj.to_object(obj.py()))
            }
            None => None,
        };
        Ok(Self {
            type_validator,
            external_validator,
        })
    }

    fn validate(&self, py: Python, obj: PyObject) -> PyResult<PyObject> {
        if let Some(external_validator) = &self.external_validator {
            let validator_kwarg = ValidatorCallable::new(self.type_validator.clone());
            let kwargs = [("validator", validator_kwarg.into_py(py))];
            let result = external_validator.call(py, (), Some(kwargs.into_py_dict(py)))?;
            Ok(result)
        } else {
            self.type_validator.validate(py, obj)
        }
    }

    fn __repr__(&self) -> PyResult<String> {
        Ok(format!("Validator({:?})", self))
    }
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct ValidatorCallable {
    type_validator: Box<dyn TypeValidator>,
}

impl ValidatorCallable {
    fn new(type_validator: Box<dyn TypeValidator>) -> Self {
        Self { type_validator }
    }
}

#[pymethods]
impl ValidatorCallable {
    fn __call__(&self, py: Python, arg: PyObject) -> PyResult<PyObject> {
        self.type_validator.validate(py, arg)
    }

    fn __repr__(&self) -> PyResult<String> {
        Ok(format!("ValidatorCallable({:?})", self))
    }
}
