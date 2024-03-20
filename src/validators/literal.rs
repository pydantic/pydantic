// Validator for things inside of a typing.Literal[]
// which can be an int, a string, bytes or an Enum value (including `class Foo(str, Enum)` type enums)
use core::fmt::Debug;
use std::cmp::Ordering;

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use pyo3::{intern, PyTraverseError, PyVisit};

use ahash::AHashMap;

use crate::build_tools::{py_schema_err, py_schema_error_type};
use crate::errors::{ErrorType, ValError, ValResult};
use crate::input::{Input, ValidationMatch};
use crate::py_gc::PyGcTraverse;
use crate::tools::SchemaDict;

use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

#[derive(Debug, Clone, Default)]
struct BoolLiteral {
    pub true_id: Option<usize>,
    pub false_id: Option<usize>,
}

#[derive(Debug, Clone)]
pub struct LiteralLookup<T: Debug> {
    // Specialized lookups for ints, bools and strings because they
    // (1) are easy to convert between Rust and Python
    // (2) hashing them in Rust is very fast
    // (3) are the most commonly used things in Literal[...]
    expected_bool: Option<BoolLiteral>,
    expected_int: Option<AHashMap<i64, usize>>,
    expected_str: Option<AHashMap<String, usize>>,
    // Catch all for hashable types like Enum and bytes (the latter only because it is seldom used)
    expected_py_dict: Option<Py<PyDict>>,
    // Catch all for unhashable types like list
    expected_py_list: Option<Py<PyList>>,

    pub values: Vec<T>,
}

impl<T: Debug> LiteralLookup<T> {
    pub fn new<'py>(py: Python<'py>, expected: impl Iterator<Item = (Bound<'py, PyAny>, T)>) -> PyResult<Self> {
        let mut expected_bool = BoolLiteral::default();
        let mut expected_int = AHashMap::new();
        let mut expected_str: AHashMap<String, usize> = AHashMap::new();
        let expected_py_dict = PyDict::new_bound(py);
        let expected_py_list = PyList::empty_bound(py);
        let mut values = Vec::new();
        for (k, v) in expected {
            let id = values.len();
            values.push(v);
            if let Ok(bool) = k.validate_bool(true) {
                if bool.into_inner() {
                    expected_bool.true_id = Some(id);
                } else {
                    expected_bool.false_id = Some(id);
                }
            }
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
            } else if expected_py_dict.set_item(&k, id).is_err() {
                expected_py_list.append((&k, id))?;
            }
        }

        Ok(Self {
            expected_bool: match expected_bool.true_id.is_some() || expected_bool.false_id.is_some() {
                true => Some(expected_bool),
                false => None,
            },
            expected_int: match expected_int.is_empty() {
                true => None,
                false => Some(expected_int),
            },
            expected_str: match expected_str.is_empty() {
                true => None,
                false => Some(expected_str),
            },
            expected_py_dict: match expected_py_dict.is_empty() {
                true => None,
                false => Some(expected_py_dict.into()),
            },
            expected_py_list: match expected_py_list.is_empty() {
                true => None,
                false => Some(expected_py_list.into()),
            },
            values,
        })
    }

    pub fn validate<'a, 'py, I: Input<'py> + ?Sized>(
        &self,
        py: Python<'py>,
        input: &'a I,
    ) -> ValResult<Option<(&'a I, &T)>> {
        if let Some(expected_bool) = &self.expected_bool {
            if let Ok(bool_value) = input.validate_bool(true) {
                if bool_value.into_inner() {
                    if let Some(true_value) = &expected_bool.true_id {
                        return Ok(Some((input, &self.values[*true_value])));
                    }
                } else if let Some(false_value) = &expected_bool.false_id {
                    return Ok(Some((input, &self.values[*false_value])));
                }
            }
        }
        if let Some(expected_ints) = &self.expected_int {
            if let Ok(either_int) = input.exact_int() {
                let int = either_int.into_i64(py)?;
                if let Some(id) = expected_ints.get(&int) {
                    return Ok(Some((input, &self.values[*id])));
                }
            }
        }
        if let Some(expected_strings) = &self.expected_str {
            let validation_result = if input.is_python() {
                input.exact_str()
            } else {
                // Strings coming from JSON are treated as "strict" but not "exact" for reasons
                // of parsing types like UUID; see the implementation of `validate_str` for Json
                // inputs for justification. We might change that eventually, but for now we need
                // to work around this when loading from JSON
                // V3 TODO: revisit making this "exact" for JSON inputs
                input.validate_str(true, false).map(ValidationMatch::into_inner)
            };

            if let Ok(either_str) = validation_result {
                let cow = either_str.as_cow()?;
                if let Some(id) = expected_strings.get(cow.as_ref()) {
                    return Ok(Some((input, &self.values[*id])));
                }
            }
        }
        if let Some(expected_py_dict) = &self.expected_py_dict {
            // We don't use ? to unpack the result of `get_item` in the next line because unhashable
            // inputs will produce a TypeError, which in this case we just want to treat equivalently
            // to a failed lookup
            if let Ok(Some(v)) = expected_py_dict.bind(py).get_item(input) {
                let id: usize = v.extract().unwrap();
                return Ok(Some((input, &self.values[id])));
            }
        };
        if let Some(expected_py_list) = &self.expected_py_list {
            for item in expected_py_list.bind(py) {
                let (k, id): (Bound<PyAny>, usize) = item.extract()?;
                if k.compare(input.to_object(py).bind(py))
                    .unwrap_or(Ordering::Less)
                    .is_eq()
                {
                    return Ok(Some((input, &self.values[id])));
                }
            }
        };
        Ok(None)
    }

    /// Used by int enums
    pub fn validate_int<'a, 'py, I: Input<'py> + ?Sized>(
        &self,
        py: Python<'py>,
        input: &'a I,
        strict: bool,
    ) -> ValResult<Option<&T>> {
        if let Some(expected_ints) = &self.expected_int {
            if let Ok(either_int) = input.validate_int(strict) {
                let int = either_int.into_inner().into_i64(py)?;
                if let Some(id) = expected_ints.get(&int) {
                    return Ok(Some(&self.values[*id]));
                }
            }
        }
        Ok(None)
    }

    /// Used by str enums
    pub fn validate_str<'a, 'py, I: Input<'py> + ?Sized>(&self, input: &'a I, strict: bool) -> ValResult<Option<&T>> {
        if let Some(expected_strings) = &self.expected_str {
            if let Ok(either_str) = input.validate_str(strict, false) {
                let s = either_str.into_inner();
                if let Some(id) = expected_strings.get(s.as_cow()?.as_ref()) {
                    return Ok(Some(&self.values[*id]));
                }
            }
        }
        Ok(None)
    }

    /// Used by float enums
    pub fn validate_float<'a, 'py, I: Input<'py> + ?Sized>(
        &self,
        py: Python<'py>,
        input: &'a I,
        strict: bool,
    ) -> ValResult<Option<&T>> {
        if let Some(expected_py) = &self.expected_py_dict {
            if let Ok(either_float) = input.validate_float(strict) {
                let f = either_float.into_inner().as_f64();
                let py_float = f.to_object(py);
                if let Ok(Some(v)) = expected_py.bind(py).get_item(py_float.bind(py)) {
                    let id: usize = v.extract().unwrap();
                    return Ok(Some(&self.values[id]));
                }
            }
        }
        Ok(None)
    }
}

impl<T: PyGcTraverse + Debug> PyGcTraverse for LiteralLookup<T> {
    fn py_gc_traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        self.expected_py_dict.py_gc_traverse(visit)?;
        self.values.py_gc_traverse(visit)?;
        Ok(())
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
        schema: &Bound<'_, PyDict>,
        _config: Option<&Bound<'_, PyDict>>,
        _definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let expected: Bound<PyList> = schema.get_as_req(intern!(schema.py(), "expected"))?;
        if expected.is_empty() {
            return py_schema_err!("`expected` should have length > 0");
        }
        let py = expected.py();
        let mut repr_args: Vec<String> = Vec::new();
        for item in expected.iter() {
            repr_args.push(item.repr()?.extract()?);
        }
        let (expected_repr, name) = expected_repr_name(repr_args, "literal");
        let lookup = LiteralLookup::new(py, expected.into_iter().map(|v| (v.clone(), v.into())))?;
        Ok(CombinedValidator::Literal(Self {
            lookup,
            expected_repr,
            name,
        }))
    }
}

impl_py_gc_traverse!(LiteralValidator { lookup });

impl Validator for LiteralValidator {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        _state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<PyObject> {
        match self.lookup.validate(py, input)? {
            Some((_, v)) => Ok(v.clone()),
            None => Err(ValError::new(
                ErrorType::LiteralError {
                    expected: self.expected_repr.clone(),
                    context: None,
                },
                input,
            )),
        }
    }

    fn get_name(&self) -> &str {
        &self.name
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
