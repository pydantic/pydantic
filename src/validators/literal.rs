// Validator for things inside of a typing.Literal[]
// which can be an int, a string, bytes or an Enum value (including `class Foo(str, Enum)` type enums)

use ahash::AHashSet;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use crate::build_tools::{py_err, py_error_type, SchemaDict};
use crate::errors::{ErrorType, ValError, ValResult};
use crate::input::Input;
use crate::recursion_guard::RecursionGuard;

use super::{BuildValidator, CombinedValidator, Definitions, DefinitionsBuilder, Extra, Validator};

#[derive(Debug, Clone)]
pub struct LiteralValidator {
    // Specialized lookups for ints and strings because they
    // (1) are easy to convert between Rust and Python
    // (2) hashing them in Rust is very fast
    // (3) are the most commonly used things in Literal[...]
    expected_int: Option<AHashSet<i64>>,
    expected_str: Option<AHashSet<String>>,
    // Catch all for Enum and bytes (the latter only because it is seldom used)
    expected_py: Option<Py<PyDict>>,
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
            return py_err!(r#""expected" should have length > 0"#);
        }
        let py = expected.py();
        // Literal[...] only supports int, str, bytes or enums, all of which can be hashed
        let mut expected_int = AHashSet::new();
        let mut expected_str = AHashSet::new();
        let expected_py = PyDict::new(py);
        let mut repr_args: Vec<String> = Vec::new();
        for item in expected.iter() {
            repr_args.push(item.repr()?.extract()?);
            if let Ok(either_int) = item.strict_int() {
                let int = either_int
                    .try_into()
                    .map_err(|_| py_error_type!("error extracting int {:?}", item))?;
                expected_int.insert(int);
            } else if let Ok(either_str) = item.strict_str() {
                let str = either_str
                    .as_cow()
                    .map_err(|_| py_error_type!("error extracting str {:?}", item))?;
                expected_str.insert(str.to_string());
            } else {
                expected_py.set_item(item, item)?;
            }
        }
        let (expected_repr, name) = expected_repr_name(repr_args, "literal");
        Ok(CombinedValidator::Literal(Self {
            expected_int: (!expected_int.is_empty()).then_some(expected_int),
            expected_str: (!expected_str.is_empty()).then_some(expected_str),
            expected_py: (!expected_py.is_empty()).then_some(expected_py.into()),
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
        if let Some(expected_ints) = &self.expected_int {
            if let Ok(either_int) = input.strict_int() {
                let int = either_int.try_into()?;
                if expected_ints.contains(&int) {
                    return Ok(input.to_object(py));
                }
            }
        }
        if let Some(expected_strings) = &self.expected_str {
            if let Ok(either_str) = input.strict_str() {
                let cow = either_str.as_cow()?;
                if expected_strings.contains(cow.as_ref()) {
                    return Ok(input.to_object(py));
                }
            }
        }
        // must be an enum or bytes
        if let Some(expected_py) = &self.expected_py {
            if let Some(v) = expected_py.as_ref(py).get_item(input) {
                return Ok(v.into());
            }
        };
        Err(ValError::new(
            ErrorType::LiteralError {
                expected: self.expected_repr.clone(),
            },
            input,
        ))
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
