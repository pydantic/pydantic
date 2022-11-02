use ahash::AHashSet;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use url::Url;

use crate::build_tools::{is_strict, py_err, SchemaDict};
use crate::errors::{ErrorType, ValError, ValResult};
use crate::input::Input;
use crate::recursion_guard::RecursionGuard;
use crate::PyUrl;

use super::literal::expected_repr_name;
use super::{BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct UrlValidator {
    strict: bool,
    host_required: bool,
    max_length: Option<usize>,
    allowed_schemes: Option<AHashSet<String>>,
    expected_repr: Option<String>,
    name: String,
}

impl BuildValidator for UrlValidator {
    const EXPECTED_TYPE: &'static str = "url";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        _build_context: &mut BuildContext,
    ) -> PyResult<CombinedValidator> {
        let (allowed_schemes, expected_repr, name): (Option<AHashSet<String>>, Option<String>, String) =
            match schema.get_as::<&PyList>(intern!(schema.py(), "allowed_schemes"))? {
                Some(list) => {
                    if list.is_empty() {
                        return py_err!(r#""allowed_schemes" should have length > 0"#);
                    }

                    let mut expected: AHashSet<String> = AHashSet::new();
                    let mut repr_args = Vec::new();
                    for item in list.iter() {
                        let str = item.extract()?;
                        repr_args.push(format!("'{str}'"));
                        expected.insert(str);
                    }
                    let (repr, name) = expected_repr_name(repr_args, "literal");
                    (Some(expected), Some(repr), name)
                }
                None => (None, None, Self::EXPECTED_TYPE.to_string()),
            };

        Ok(Self {
            strict: is_strict(schema, config)?,
            host_required: schema.get_as(intern!(schema.py(), "host_required"))?.unwrap_or(false),
            max_length: schema.get_as(intern!(schema.py(), "max_length"))?,
            allowed_schemes,
            expected_repr,
            name,
        }
        .into())
    }
}

impl Validator for UrlValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        _slots: &'data [CombinedValidator],
        _recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let lib_url = self.get_url(input, extra.strict.unwrap_or(self.strict))?;

        if let Some(ref allowed_schemes) = self.allowed_schemes {
            if !allowed_schemes.contains(lib_url.scheme()) {
                let expected_schemas = self.expected_repr.as_ref().unwrap().clone();
                return Err(ValError::new(ErrorType::UrlSchema { expected_schemas }, input));
            }
        }
        if self.host_required && !lib_url.has_host() {
            return Err(ValError::new(ErrorType::UrlHostRequired, input));
        }
        Ok(PyUrl::new(lib_url).into_py(py))
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}

impl UrlValidator {
    fn get_url<'s, 'data>(&'s self, input: &'data impl Input<'data>, strict: bool) -> ValResult<'data, Url> {
        match input.validate_str(strict) {
            Ok(either_str) => {
                let cow = either_str.as_cow()?;
                let str = cow.as_ref();

                if let Some(max_length) = self.max_length {
                    if str.len() > max_length {
                        return Err(ValError::new(ErrorType::UrlTooLong { max_length }, input));
                    }
                }

                Url::parse(str).map_err(move |e| ValError::new(ErrorType::UrlError { error: e.to_string() }, input))
            }
            Err(e) => {
                let lib_url = match input.input_as_url() {
                    Some(url) => url.into_url(),
                    None => return Err(e),
                };
                if let Some(max_length) = self.max_length {
                    if lib_url.as_str().len() > max_length {
                        return Err(ValError::new(ErrorType::UrlTooLong { max_length }, input));
                    }
                }
                Ok(lib_url)
            }
        }
    }
}
