use std::cell::RefCell;
use std::iter::Peekable;
use std::str::Chars;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use ahash::AHashSet;
use url::{ParseError, SyntaxViolation, Url};

use crate::build_tools::{is_strict, py_schema_err};
use crate::errors::{ErrorType, ErrorTypeDefaults, ValError, ValResult};
use crate::input::Input;
use crate::tools::SchemaDict;
use crate::url::{schema_is_special, PyMultiHostUrl, PyUrl};

use super::literal::expected_repr_name;
use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};

type AllowedSchemas = Option<(AHashSet<String>, String)>;

#[derive(Debug, Clone)]
pub struct UrlValidator {
    strict: bool,
    max_length: Option<usize>,
    allowed_schemes: AllowedSchemas,
    host_required: bool,
    default_host: Option<String>,
    default_port: Option<u16>,
    default_path: Option<String>,
    name: String,
}

impl BuildValidator for UrlValidator {
    const EXPECTED_TYPE: &'static str = "url";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        _definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let (allowed_schemes, name) = get_allowed_schemas(schema, Self::EXPECTED_TYPE)?;

        Ok(Self {
            strict: is_strict(schema, config)?,
            max_length: schema.get_as(intern!(schema.py(), "max_length"))?,
            host_required: schema.get_as(intern!(schema.py(), "host_required"))?.unwrap_or(false),
            default_host: schema.get_as(intern!(schema.py(), "default_host"))?,
            default_port: schema.get_as(intern!(schema.py(), "default_port"))?,
            default_path: schema.get_as(intern!(schema.py(), "default_path"))?,
            allowed_schemes,
            name,
        }
        .into())
    }
}

impl_py_gc_traverse!(UrlValidator {});

impl Validator for UrlValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        let mut lib_url = self.get_url(input, state.strict_or(self.strict))?;

        if let Some((ref allowed_schemes, ref expected_schemes_repr)) = self.allowed_schemes {
            if !allowed_schemes.contains(lib_url.scheme()) {
                let expected_schemes = expected_schemes_repr.clone();
                return Err(ValError::new(
                    ErrorType::UrlScheme {
                        expected_schemes,
                        context: None,
                    },
                    input,
                ));
            }
        }

        match check_sub_defaults(
            &mut lib_url,
            self.host_required,
            &self.default_host,
            self.default_port,
            &self.default_path,
        ) {
            Ok(()) => Ok(PyUrl::new(lib_url).into_py(py)),
            Err(error_type) => return Err(ValError::new(error_type, input)),
        }
    }

    fn different_strict_behavior(&self, ultra_strict: bool) -> bool {
        !ultra_strict
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&self) -> PyResult<()> {
        Ok(())
    }
}

impl UrlValidator {
    fn get_url<'s, 'data>(&'s self, input: &'data impl Input<'data>, strict: bool) -> ValResult<'data, Url> {
        match input.validate_str(strict, false) {
            Ok(either_str) => {
                let cow = either_str.as_cow()?;
                let url_str = cow.as_ref();

                self.check_length(input, url_str)?;

                parse_url(url_str, input, strict)
            }
            Err(_) => {
                // we don't need to worry about whether the url was parsed in strict mode before,
                // even if it was, any syntax errors would have been fixed by the first validation
                if let Some(py_url) = input.input_as_url() {
                    let lib_url = py_url.into_url();
                    self.check_length(input, lib_url.as_str())?;
                    Ok(lib_url)
                } else if let Some(multi_host_url) = input.input_as_multi_host_url() {
                    let url_str = multi_host_url.__str__();
                    self.check_length(input, &url_str)?;

                    parse_url(&url_str, input, strict)
                } else {
                    Err(ValError::new(ErrorTypeDefaults::UrlType, input))
                }
            }
        }
    }

    fn check_length<'s, 'data>(&self, input: &'data impl Input<'data>, url_str: &str) -> ValResult<'data, ()> {
        if let Some(max_length) = self.max_length {
            if url_str.len() > max_length {
                return Err(ValError::new(
                    ErrorType::UrlTooLong {
                        max_length,
                        context: None,
                    },
                    input,
                ));
            }
        }
        Ok(())
    }
}

#[derive(Debug, Clone)]
pub struct MultiHostUrlValidator {
    strict: bool,
    max_length: Option<usize>,
    allowed_schemes: AllowedSchemas,
    host_required: bool,
    default_host: Option<String>,
    default_port: Option<u16>,
    default_path: Option<String>,
    name: String,
}

impl BuildValidator for MultiHostUrlValidator {
    const EXPECTED_TYPE: &'static str = "multi-host-url";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        _definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let (allowed_schemes, name) = get_allowed_schemas(schema, Self::EXPECTED_TYPE)?;

        let default_host: Option<String> = schema.get_as(intern!(schema.py(), "default_host"))?;
        if let Some(ref default_host) = default_host {
            if default_host.contains(',') {
                return py_schema_err!("default_host cannot contain a comma, see pydantic-core#326");
            }
        }
        Ok(Self {
            strict: is_strict(schema, config)?,
            max_length: schema.get_as(intern!(schema.py(), "max_length"))?,
            allowed_schemes,
            host_required: schema.get_as(intern!(schema.py(), "host_required"))?.unwrap_or(false),
            default_host,
            default_port: schema.get_as(intern!(schema.py(), "default_port"))?,
            default_path: schema.get_as(intern!(schema.py(), "default_path"))?,
            name,
        }
        .into())
    }
}

impl_py_gc_traverse!(MultiHostUrlValidator {});

impl Validator for MultiHostUrlValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        let mut multi_url = self.get_url(input, state.strict_or(self.strict))?;

        if let Some((ref allowed_schemes, ref expected_schemes_repr)) = self.allowed_schemes {
            if !allowed_schemes.contains(multi_url.scheme()) {
                let expected_schemes = expected_schemes_repr.clone();
                return Err(ValError::new(
                    ErrorType::UrlScheme {
                        expected_schemes,
                        context: None,
                    },
                    input,
                ));
            }
        }
        match check_sub_defaults(
            multi_url.mut_lib_url(),
            self.host_required,
            &self.default_host,
            self.default_port,
            &self.default_path,
        ) {
            Ok(()) => Ok(multi_url.into_py(py)),
            Err(error_type) => return Err(ValError::new(error_type, input)),
        }
    }

    fn different_strict_behavior(&self, ultra_strict: bool) -> bool {
        !ultra_strict
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&self) -> PyResult<()> {
        Ok(())
    }
}

impl MultiHostUrlValidator {
    fn get_url<'s, 'data>(&'s self, input: &'data impl Input<'data>, strict: bool) -> ValResult<'data, PyMultiHostUrl> {
        match input.validate_str(strict, false) {
            Ok(either_str) => {
                let cow = either_str.as_cow()?;
                let url_str = cow.as_ref();

                self.check_length(input, || url_str.len())?;

                parse_multihost_url(url_str, input, strict)
            }
            Err(_) => {
                // we don't need to worry about whether the url was parsed in strict mode before,
                // even if it was, any syntax errors would have been fixed by the first validation
                if let Some(multi_url) = input.input_as_multi_host_url() {
                    self.check_length(input, || multi_url.__str__().len())?;
                    Ok(multi_url)
                } else if let Some(py_url) = input.input_as_url() {
                    let lib_url = py_url.into_url();
                    self.check_length(input, || lib_url.as_str().len())?;
                    Ok(PyMultiHostUrl::new(lib_url, None))
                } else {
                    Err(ValError::new(ErrorTypeDefaults::UrlType, input))
                }
            }
        }
    }

    fn check_length<'s, 'data, F>(&self, input: &'data impl Input<'data>, func: F) -> ValResult<'data, ()>
    where
        F: FnOnce() -> usize,
    {
        if let Some(max_length) = self.max_length {
            if func() > max_length {
                return Err(ValError::new(
                    ErrorType::UrlTooLong {
                        max_length,
                        context: None,
                    },
                    input,
                ));
            }
        }
        Ok(())
    }
}

fn parse_multihost_url<'url, 'input>(
    url_str: &'url str,
    input: &'input impl Input<'input>,
    strict: bool,
) -> ValResult<'input, PyMultiHostUrl> {
    macro_rules! parsing_err {
        ($parse_error:expr) => {
            Err(ValError::new(
                ErrorType::UrlParsing {
                    error: $parse_error.to_string(),
                    context: None,
                },
                input,
            ))
        };
    }

    if url_str.is_empty() {
        return parsing_err!(EMPTY_INPUT);
    }

    let mut chars = PositionedPeekable::new(url_str);
    // consume whitespace, taken from `with_log`
    // https://github.com/servo/rust-url/blob/v2.3.1/url/src/parser.rs#L213-L226
    loop {
        let peek = chars.peek();
        if let Some(c) = peek {
            match c {
                '\t' | '\n' | '\r' => (),
                c if c <= &' ' => (),
                _ => break,
            };
            chars.next();
        } else {
            break;
        }
    }

    // consume the url schema, some logic from `parse_scheme`
    // https://github.com/servo/rust-url/blob/v2.3.1/url/src/parser.rs#L387-L411
    let schema_start = chars.position;
    let schema_end = loop {
        match chars.next() {
            Some('a'..='z' | 'A'..='Z' | '0'..='9' | '+' | '-' | '.') => continue,
            Some(':') => {
                // require the schema to be non-empty
                let schema_end = chars.position - ':'.len_utf8();
                if schema_end > schema_start {
                    break schema_end;
                }
            }
            _ => {}
        }
        return parsing_err!(ParseError::RelativeUrlWithoutBase);
    };
    let schema = url_str[schema_start..schema_end].to_ascii_lowercase();

    // consume the double slash, or any number of slashes, including backslashes, taken from `parse_with_scheme`
    // https://github.com/servo/rust-url/blob/v2.3.1/url/src/parser.rs#L413-L456
    loop {
        let peek = chars.peek();
        match peek {
            Some(&'/' | &'\\') => {
                chars.next();
            }
            _ => break,
        }
    }
    let prefix = &url_str[..chars.position];

    // process host and port, splitting based on `,`, some logic taken from `parse_host`
    // https://github.com/servo/rust-url/blob/v2.3.1/url/src/parser.rs#L971-L1026
    let mut hosts: Vec<&str> = Vec::with_capacity(3);
    let mut start = chars.position;
    while let Some(c) = chars.next() {
        match c {
            '\\' if schema_is_special(&schema) => break,
            '/' | '?' | '#' => break,
            ',' => {
                // minus 1 because we know that the last char was a `,` with length 1
                let end = chars.position - ','.len_utf8();
                if start == end {
                    return parsing_err!(ParseError::EmptyHost);
                }
                hosts.push(&url_str[start..end]);
                start = chars.position;
            }
            _ => (),
        }
    }
    // with just one host, for consistent behaviour, we parse the URL the same as with multiple hosts

    let reconstructed_url = format!("{prefix}{}", &url_str[start..]);
    let ref_url = parse_url(&reconstructed_url, input, strict)?;

    if hosts.is_empty() {
        // if there's no one host (e.g. no `,`), we allow it to be empty to allow for default hosts
        Ok(PyMultiHostUrl::new(ref_url, None))
    } else {
        // with more than one host, none of them can be empty
        if !ref_url.has_host() {
            return parsing_err!(ParseError::EmptyHost);
        }
        let extra_urls: Vec<Url> = hosts
            .iter()
            .map(|host| {
                let reconstructed_url = format!("{prefix}{host}");
                parse_url(&reconstructed_url, input, strict)
            })
            .collect::<ValResult<_>>()?;

        if extra_urls.iter().any(|url| !url.has_host()) {
            return parsing_err!(ParseError::EmptyHost);
        }

        Ok(PyMultiHostUrl::new(ref_url, Some(extra_urls)))
    }
}

fn parse_url<'url, 'input>(
    url_str: &'url str,
    input: &'input impl Input<'input>,
    strict: bool,
) -> ValResult<'input, Url> {
    if url_str.is_empty() {
        return Err(ValError::new(
            ErrorType::UrlParsing {
                error: EMPTY_INPUT.into(),
                context: None,
            },
            input,
        ));
    }

    // if we're in strict mode, we collect consider a syntax violation as an error
    if strict {
        // we could build a vec of syntax violations and return them all, but that seems like overkill
        // and unlike other parser style validators
        let vios: RefCell<Option<SyntaxViolation>> = RefCell::new(None);
        let r = Url::options()
            .syntax_violation_callback(Some(&|v| {
                match v {
                    // telling users offer about credentials in URLs doesn't really make sense in this context
                    SyntaxViolation::EmbeddedCredentials => (),
                    _ => *vios.borrow_mut() = Some(v),
                }
            }))
            .parse(url_str);

        match r {
            Ok(url) => {
                if let Some(vio) = vios.into_inner() {
                    Err(ValError::new(
                        ErrorType::UrlSyntaxViolation {
                            error: vio.description().into(),
                            context: None,
                        },
                        input,
                    ))
                } else {
                    Ok(url)
                }
            }
            Err(e) => Err(ValError::new(
                ErrorType::UrlParsing {
                    error: e.to_string(),
                    context: None,
                },
                input,
            )),
        }
    } else {
        Url::parse(url_str).map_err(move |e| {
            ValError::new(
                ErrorType::UrlParsing {
                    error: e.to_string(),
                    context: None,
                },
                input,
            )
        })
    }
}

/// check host_required and substitute `default_host`, `default_port` & `default_path` if they aren't set
fn check_sub_defaults(
    lib_url: &mut Url,
    host_required: bool,
    default_host: &Option<String>,
    default_port: Option<u16>,
    default_path: &Option<String>,
) -> Result<(), ErrorType> {
    let map_parse_err = |e: ParseError| ErrorType::UrlParsing {
        error: e.to_string(),
        context: None,
    };
    if !lib_url.has_host() {
        if let Some(ref default_host) = default_host {
            lib_url.set_host(Some(default_host)).map_err(map_parse_err)?;
        } else if host_required {
            return Err(ErrorType::UrlParsing {
                error: ParseError::EmptyHost.to_string(),
                context: None,
            });
        }
    }
    if lib_url.port().is_none() {
        if let Some(default_port) = default_port {
            lib_url
                .set_port(Some(default_port))
                .map_err(|()| map_parse_err(ParseError::EmptyHost))?;
        }
    }
    if let Some(ref default_path) = default_path {
        let path = lib_url.path();
        if path.is_empty() || path == "/" {
            lib_url.set_path(default_path);
        }
    }
    Ok(())
}

fn get_allowed_schemas(schema: &PyDict, name: &'static str) -> PyResult<(AllowedSchemas, String)> {
    match schema.get_as::<&PyList>(intern!(schema.py(), "allowed_schemes"))? {
        Some(list) => {
            if list.is_empty() {
                return py_schema_err!("`allowed_schemes` should have length > 0");
            }

            let mut expected: AHashSet<String> = AHashSet::new();
            let mut repr_args = Vec::new();
            for item in list {
                let str = item.extract()?;
                repr_args.push(format!("'{str}'"));
                expected.insert(str);
            }
            let (repr, name) = expected_repr_name(repr_args, name);
            Ok((Some((expected, repr)), name))
        }
        None => Ok((None, name.to_string())),
    }
}

#[cfg_attr(debug_assertions, derive(Debug))]
struct PositionedPeekable<'a> {
    peekable: Peekable<Chars<'a>>,
    position: usize,
}

impl<'a> PositionedPeekable<'a> {
    fn new(input: &'a str) -> Self {
        Self {
            peekable: input.chars().peekable(),
            position: 0,
        }
    }

    fn next(&mut self) -> Option<char> {
        let c = self.peekable.next();
        if let Some(c) = c {
            self.position += c.len_utf8();
        }
        c
    }

    fn peek(&mut self) -> Option<&char> {
        self.peekable.peek()
    }
}

const EMPTY_INPUT: &str = "input is empty";
