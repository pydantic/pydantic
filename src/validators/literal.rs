// Validator for things inside of a typing.Literal[]
// which can be an int, a string, bytes or an Enum value (including `class Foo(str, Enum)` type enums)
use core::fmt::Debug;

use ahash::AHashMap;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use crate::build_tools::{py_schema_err, py_schema_error_type};
use crate::errors::{ErrorType, ValError, ValResult};
use crate::input::Input;
use crate::recursion_guard::RecursionGuard;
use crate::tools::SchemaDict;

use super::{BuildValidator, CombinedValidator, Definitions, DefinitionsBuilder, Extra, Validator};

#[derive(Debug, Clone)]
pub struct LiteralLookup<T: Clone + Debug> {
    // Specialized lookups for ints and strings because they
    // (1) are easy to convert between Rust and Python
    // (2) hashing them in Rust is very fast
    // (3) are the most commonly used things in Literal[...]
    expected_int: Option<AHashMap<i64, usize>>,
    expected_str: Option<AHashMap<String, usize>>,
    // Catch all for Enum and bytes (the latter only because it is seldom used)
    expected_py: Option<Py<PyDict>>,
    pub values: Vec<T>,
}

impl<T: Clone + Debug> LiteralLookup<T> {
    pub fn new<'py>(py: Python<'py>, expected: impl Iterator<Item = (&'py PyAny, T)>) -> PyResult<Self> {
        let mut expected_int = AHashMap::new();
        let mut expected_str = AHashMap::new();
        let expected_py = PyDict::new(py);
        let mut values = Vec::new();
        for (k, v) in expected {
            let id = values.len();
            values.push(v);
            if let Ok(either_int) = k.exact_int() {
                let int = either_int
                    .into_i64(py)
                    .map_err(|_| py_schema_error_type!("error extracting int {:?}", k))?;
                expected_int.insert(int, id);
            } else if let Ok(either_str) = k.exact_str() {
                let str = either_str
                    .as_cow()
                    .map_err(|_| py_schema_error_type!("error extracting str {:?}", k))?;
                expected_str.insert(str.to_string(), id);
            } else {
                expected_py.set_item(k, id)?;
            }
        }

        Ok(Self {
            expected_int: match expected_int.is_empty() {
                true => None,
                false => Some(expected_int),
            },
            expected_str: match expected_str.is_empty() {
                true => None,
                false => Some(expected_str),
            },
            expected_py: match expected_py.is_empty() {
                true => None,
                false => Some(expected_py.into()),
            },
            values,
        })
    }

    pub fn validate<'data, I: Input<'data>>(
        &self,
        py: Python<'data>,
        input: &'data I,
    ) -> ValResult<'data, Option<(&'data I, &T)>> {
        // dbg!(input.to_object(py).as_ref(py).repr().unwrap());
        if let Some(expected_ints) = &self.expected_int {
            if let Ok(either_int) = input.exact_int() {
                let int = either_int.into_i64(py)?;
                if let Some(id) = expected_ints.get(&int) {
                    return Ok(Some((input, &self.values[*id])));
                }
            }
        }
        if let Some(expected_strings) = &self.expected_str {
            // dbg!(expected_strings);
            if let Ok(either_str) = input.exact_str() {
                let cow = either_str.as_cow()?;
                if let Some(id) = expected_strings.get(cow.as_ref()) {
                    return Ok(Some((input, &self.values[*id])));
                }
            }
        }
        // must be an enum or bytes
        if let Some(expected_py) = &self.expected_py {
            if let Some(v) = expected_py.as_ref(py).get_item(input) {
                let id: usize = v.extract().unwrap();
                return Ok(Some((input, &self.values[id])));
            }
        };
        Ok(None)
    }
}

#[derive(Debug, Clone)]
pub struct LiteralValidator {
    lookup: LiteralLookup<PyObject>,
    expected_repr: String,
    name: String,
}

impl BuildValidator for LiteralValidator {
    const EXPECTED_TYPE: &'static str = "literal";

    fn build(
        schema: &PyDict,
        _config: Option<&PyDict>,
        _definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let expected: &PyList = schema.get_as_req(intern!(schema.py(), "expected"))?;
        if expected.is_empty() {
            return py_schema_err!("`expected` should have length > 0");
        }
        let py = expected.py();
        let mut repr_args: Vec<String> = Vec::new();
        for item in expected.iter() {
            repr_args.push(item.repr()?.extract()?);
        }
        let (expected_repr, name) = expected_repr_name(repr_args, "literal");
        let lookup = LiteralLookup::new(py, expected.iter().map(|v| (v, v.to_object(py))))?;
        Ok(CombinedValidator::Literal(Self {
            lookup,
            expected_repr,
            name,
        }))
    }
}

impl Validator for LiteralValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        _extra: &Extra,
        _definitions: &'data Definitions<CombinedValidator>,
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        match self.lookup.validate(py, input)? {
            Some((_, v)) => Ok(v.clone()),
            None => Err(ValError::new(
                ErrorType::LiteralError {
                    expected: self.expected_repr.clone(),
                },
                input,
            )),
        }
    }

    fn different_strict_behavior(
        &self,
        _definitions: Option<&DefinitionsBuilder<CombinedValidator>>,
        ultra_strict: bool,
    ) -> bool {
        !ultra_strict
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, _definitions: &DefinitionsBuilder<CombinedValidator>) -> PyResult<()> {
        Ok(())
    }
}

pub fn expected_repr_name(mut repr_args: Vec<String>, base_name: &'static str) -> (String, String) {
    let name = format!("{base_name}[{}]", repr_args.join(","));
    // unwrap is okay since we check the length in build at the top of this file
    let last_repr = repr_args.pop().unwrap();
    let repr = if repr_args.is_empty() {
        last_repr
    } else {
        format!("{} or {last_repr}", repr_args.join(", "))
    };
    (repr, name)
}
