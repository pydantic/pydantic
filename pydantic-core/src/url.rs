use std::borrow::Cow;
use std::collections::hash_map::DefaultHasher;
use std::fmt::{self, Formatter, Write};
use std::hash::{Hash, Hasher};
use std::sync::OnceLock;

use idna::punycode::{decode_to_string, encode_str};
use jiter::{PartialMode, StringCacheMode};
use percent_encoding::{AsciiSet, CONTROLS, percent_encode};
use pyo3::exceptions::PyValueError;
use pyo3::pyclass::CompareOp;
use pyo3::sync::OnceLockExt;
use pyo3::types::{PyDict, PyType};
use pyo3::{IntoPyObjectExt, intern, prelude::*};
use url::Url;

use crate::ValidationError;
use crate::input::InputType;
use crate::recursion_guard::RecursionState;
use crate::tools::SchemaDict;
use crate::validators::url::{MultiHostUrlValidator, UrlValidator};
use crate::validators::{Extra, ValidationState, Validator};

#[pyclass(name = "Url", module = "pydantic_core._pydantic_core", subclass, frozen)]
#[derive(Clone)]
#[cfg_attr(debug_assertions, derive(Debug))]
pub struct PyUrl {
    lib_url: Url,
    /// Override to treat the path as empty when it is `/`. The `url` crate always normalizes an empty path to `/`,
    /// but users may want to preserve the empty path when round-tripping.
    path_is_empty: bool,
    /// Cache for the serialized representation where this diverges from `lib_url.as_str()`
    /// (i.e. when trailing slash was added to the empty path, but user didn't want that)
    serialized: OnceLock<String>,
}

impl Hash for PyUrl {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.lib_url.hash(state);
        self.path_is_empty.hash(state);
        // no need to hash `serialized` as it's derived from the other two fields
    }
}

impl PyUrl {
    pub fn new(lib_url: Url, path_is_empty: bool) -> Self {
        Self {
            lib_url,
            path_is_empty,
            serialized: OnceLock::new(),
        }
    }

    pub fn url(&self) -> &Url {
        &self.lib_url
    }

    pub fn url_mut(&mut self) -> &mut Url {
        &mut self.lib_url
    }

    fn serialized(&self, py: Python<'_>) -> &str {
        if self.path_is_empty {
            self.serialized
                .get_or_init_py_attached(py, || serialize_url_without_path_slash(&self.lib_url))
        } else {
            self.lib_url.as_str()
        }
    }
}

#[pymethods]
impl PyUrl {
    #[new]
    #[pyo3(signature = (url, *, preserve_empty_path=false))]
    pub fn py_new(py: Python, url: &Bound<'_, PyAny>, preserve_empty_path: bool) -> PyResult<Self> {
        let validator = UrlValidator::get_simple(false, preserve_empty_path);
        let url_obj = validator
            .validate(
                py,
                url,
                &mut ValidationState::new(
                    Extra::new(
                        None,
                        None,
                        None,
                        None,
                        None,
                        InputType::Python,
                        StringCacheMode::None,
                        None,
                        None,
                    ),
                    &mut RecursionState::default(),
                    PartialMode::Off,
                ),
            )
            .map_err(|e| {
                let name = match validator.get_name().into_py_any(py) {
                    Ok(name) => name,
                    Err(e) => return e,
                };
                ValidationError::from_val_error(py, name, InputType::Python, e, None, false, false)
            })?
            .cast_bound::<Self>(py)?
            .get()
            .clone(); // FIXME: avoid the clone, would need to make `validate` be aware of what URL subclass to create
        Ok(url_obj)
    }

    #[getter]
    pub fn scheme(&self) -> &str {
        self.lib_url.scheme()
    }

    #[getter]
    pub fn username(&self) -> Option<&str> {
        match self.lib_url.username() {
            "" => None,
            user => Some(user),
        }
    }

    #[getter]
    pub fn password(&self) -> Option<&str> {
        self.lib_url.password()
    }

    #[getter]
    pub fn host(&self) -> Option<&str> {
        self.lib_url.host_str()
    }

    // string representation of the host, with punycode decoded when appropriate
    pub fn unicode_host(&self) -> Option<String> {
        match self.lib_url.host() {
            Some(url::Host::Domain(domain)) if is_punnycode_domain(&self.lib_url, domain) => decode_punycode(domain),
            _ => self.lib_url.host_str().map(ToString::to_string),
        }
    }

    #[getter]
    pub fn port(&self) -> Option<u16> {
        self.lib_url.port_or_known_default()
    }

    #[getter]
    pub fn path(&self) -> Option<&str> {
        match self.lib_url.path() {
            "" => None,
            "/" if self.path_is_empty => None,
            path => Some(path),
        }
    }

    #[getter]
    pub fn query(&self) -> Option<&str> {
        self.lib_url.query()
    }

    pub fn query_params<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        // `query_pairs` is a pure iterator, so can't implement `ExactSizeIterator`, hence we need the temporary `Vec`
        self.lib_url
            .query_pairs()
            .map(|(key, value)| (key, value).into_pyobject(py))
            .collect::<PyResult<Vec<_>>>()?
            .into_pyobject(py)
    }

    #[getter]
    pub fn fragment(&self) -> Option<&str> {
        self.lib_url.fragment()
    }

    // string representation of the URL, with punycode decoded when appropriate
    pub fn unicode_string(&self, py: Python<'_>) -> Cow<'_, str> {
        unicode_url(self.serialized(py), &self.lib_url)
    }

    pub fn __str__(&self, py: Python<'_>) -> &str {
        self.serialized(py)
    }

    pub fn __repr__(&self, py: Python<'_>) -> String {
        format!("Url('{}')", self.serialized(py))
    }

    fn __richcmp__(&self, other: &Self, op: CompareOp) -> PyResult<bool> {
        match op {
            CompareOp::Lt => Ok(self.lib_url < other.lib_url),
            CompareOp::Le => Ok(self.lib_url <= other.lib_url),
            CompareOp::Eq => Ok(self.lib_url == other.lib_url),
            CompareOp::Ne => Ok(self.lib_url != other.lib_url),
            CompareOp::Gt => Ok(self.lib_url > other.lib_url),
            CompareOp::Ge => Ok(self.lib_url >= other.lib_url),
        }
    }

    fn __hash__(&self) -> u64 {
        let mut s = DefaultHasher::new();
        self.hash(&mut s);
        s.finish()
    }

    fn __bool__(&self) -> bool {
        true // an empty string is not a valid URL
    }

    #[pyo3(signature = (_memo, /))]
    pub fn __deepcopy__(&self, py: Python, _memo: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        self.clone().into_py_any(py)
    }

    fn __getnewargs__(&self, py: Python<'_>) -> (&str,) {
        (self.__str__(py),)
    }

    #[classmethod]
    #[pyo3(signature=(*, scheme, host, username=None, password=None, port=None, path=None, query=None, fragment=None, encode_components=false))]
    #[allow(clippy::too_many_arguments)]
    pub fn build<'py>(
        cls: &Bound<'py, PyType>,
        scheme: &str,
        host: &str,
        username: Option<&str>,
        password: Option<&str>,
        port: Option<u16>,
        path: Option<&str>,
        query: Option<&str>,
        fragment: Option<&str>,
        encode_components: bool,
    ) -> PyResult<Bound<'py, PyAny>> {
        let url_host = UrlHostParts {
            username: username.map(Into::into),
            password: password.map(Into::into),
            host: Some(host.into()),
            port,
        };
        let mut url = String::new();
        write_url(&mut url, scheme, &[url_host], path, query, fragment, encode_components)
            .expect("writing to string should not fail");
        cls.call1((url,))
    }
}

fn write_url(
    writer: &mut impl Write,
    scheme: &str,
    host_parts: &[UrlHostParts],
    path: Option<&str>,
    query: Option<&str>,
    fragment: Option<&str>,
    encode_components: bool,
) -> fmt::Result {
    write!(writer, "{scheme}://")?;
    let mut first = true;
    for single_host in host_parts {
        if first {
            first = false;
        } else {
            writer.write_char(',')?;
        }
        single_host.to_writer(writer, encode_components)?;
    }
    if let Some(path) = path {
        let path_encoding = encode_components.then_some(&PATH_ENCODE_SET);
        writer.write_char('/')?;
        write!(writer, "{}", MaybeEncoded(path, path_encoding))?;
    }
    if let Some(query) = query {
        let query_encoding = encode_components.then(|| {
            if scheme_is_special(scheme) {
                &SPECIAL_QUERY_ENCODE_SET
            } else {
                &QUERY_ENCODE_SET
            }
        });
        writer.write_char('?')?;
        write!(writer, "{}", MaybeEncoded(query, query_encoding))?;
    }
    if let Some(fragment) = fragment {
        let fragment_encoding = encode_components.then_some(&FRAGMENT_ENCODE_SET);
        writer.write_char('#')?;
        write!(writer, "{}", MaybeEncoded(fragment, fragment_encoding))?;
    }
    Ok(())
}

#[pyclass(name = "MultiHostUrl", module = "pydantic_core._pydantic_core", subclass, frozen)]
#[derive(Clone, Hash)]
#[cfg_attr(debug_assertions, derive(Debug))]
pub struct PyMultiHostUrl {
    ref_url: PyUrl,
    extra_urls: Option<Vec<Url>>,
}

impl PyMultiHostUrl {
    pub fn new(ref_url: PyUrl, extra_urls: Option<Vec<Url>>) -> Self {
        Self { ref_url, extra_urls }
    }

    pub fn lib_url(&self) -> &Url {
        &self.ref_url.lib_url
    }

    pub fn mut_lib_url(&mut self) -> &mut Url {
        &mut self.ref_url.lib_url
    }
}

#[pymethods]
impl PyMultiHostUrl {
    #[new]
    #[pyo3(signature = (url, *, preserve_empty_path=false))]
    pub fn py_new(py: Python, url: &Bound<'_, PyAny>, preserve_empty_path: bool) -> PyResult<Self> {
        let validator = MultiHostUrlValidator::get_simple(false, preserve_empty_path);
        let url_obj = validator
            .validate(
                py,
                url,
                &mut ValidationState::new(
                    Extra::new(
                        None,
                        None,
                        None,
                        None,
                        None,
                        InputType::Python,
                        StringCacheMode::None,
                        None,
                        None,
                    ),
                    &mut RecursionState::default(),
                    PartialMode::Off,
                ),
            )
            .map_err(|e| {
                let name = match validator.get_name().into_py_any(py) {
                    Ok(name) => name,
                    Err(e) => return e,
                };
                ValidationError::from_val_error(py, name, InputType::Python, e, None, false, false)
            })?
            .cast_bound::<Self>(py)?
            .get()
            .clone(); // FIXME: avoid the clone, would need to make `validate` be aware of what URL subclass to create
        Ok(url_obj)
    }

    #[getter]
    pub fn scheme(&self) -> &str {
        self.ref_url.scheme()
    }

    pub fn hosts<'py>(&self, py: Python<'py>) -> PyResult<Vec<Bound<'py, PyDict>>> {
        if let Some(extra_urls) = &self.extra_urls {
            let mut hosts = Vec::with_capacity(extra_urls.len() + 1);
            for url in extra_urls {
                hosts.push(host_to_dict(py, url)?);
            }
            hosts.push(host_to_dict(py, &self.ref_url.lib_url)?);
            Ok(hosts)
        } else if self.ref_url.lib_url.has_host() {
            Ok(vec![host_to_dict(py, &self.ref_url.lib_url)?])
        } else {
            Ok(vec![])
        }
    }

    #[getter]
    pub fn path(&self) -> Option<&str> {
        self.ref_url.path()
    }

    #[getter]
    pub fn query(&self) -> Option<&str> {
        self.ref_url.query()
    }

    pub fn query_params<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        self.ref_url.query_params(py)
    }

    #[getter]
    pub fn fragment(&self) -> Option<&str> {
        self.ref_url.fragment()
    }

    // string representation of the URL, with punycode decoded when appropriate
    pub fn unicode_string(&self, py: Python<'_>) -> Cow<'_, str> {
        if let Some(extra_urls) = &self.extra_urls {
            let scheme = self.ref_url.lib_url.scheme();
            let host_offset = scheme.len() + 3;

            let mut full_url = self.ref_url.unicode_string(py).into_owned();
            let mut extra_hosts = String::new();

            // special urls will have had a trailing slash added, non-special urls will not
            // hence we need to remove the last char if the scheme is special
            #[allow(clippy::bool_to_int_with_if)]
            let sub = if scheme_is_special(scheme) { 1 } else { 0 };

            for url in extra_urls {
                let str = unicode_url(url.as_str(), url);
                extra_hosts.push_str(&str[host_offset..str.len() - sub]);
                extra_hosts.push(',');
            }

            full_url.insert_str(host_offset, &extra_hosts);
            Cow::Owned(full_url)
        } else {
            self.ref_url.unicode_string(py)
        }
    }

    pub fn __str__(&self, py: Python<'_>) -> Cow<'_, str> {
        if let Some(extra_urls) = &self.extra_urls {
            let scheme = self.ref_url.lib_url.scheme();
            let host_offset = scheme.len() + 3;

            let mut full_url = self.ref_url.serialized(py).to_string();
            let mut extra_hosts = String::new();

            // special urls will have had a trailing slash added, non-special urls will not
            // hence we need to remove the last char if the scheme is special
            #[allow(clippy::bool_to_int_with_if)]
            let sub = if scheme_is_special(scheme) { 1 } else { 0 };

            for url in extra_urls {
                let str = url.as_str();
                extra_hosts.push_str(&str[host_offset..str.len() - sub]);
                extra_hosts.push(',');
            }

            full_url.insert_str(host_offset, &extra_hosts);
            Cow::Owned(full_url)
        } else {
            Cow::Borrowed(self.ref_url.__str__(py))
        }
    }

    pub fn __repr__(&self, py: Python<'_>) -> String {
        format!("MultiHostUrl('{}')", self.__str__(py))
    }

    fn __richcmp__(&self, other: &Self, op: CompareOp, py: Python<'_>) -> PyResult<bool> {
        match op {
            CompareOp::Lt => Ok(self.unicode_string(py) < other.unicode_string(py)),
            CompareOp::Le => Ok(self.unicode_string(py) <= other.unicode_string(py)),
            CompareOp::Eq => Ok(self.unicode_string(py) == other.unicode_string(py)),
            CompareOp::Ne => Ok(self.unicode_string(py) != other.unicode_string(py)),
            CompareOp::Gt => Ok(self.unicode_string(py) > other.unicode_string(py)),
            CompareOp::Ge => Ok(self.unicode_string(py) >= other.unicode_string(py)),
        }
    }

    fn __hash__(&self) -> u64 {
        let mut s = DefaultHasher::new();
        self.hash(&mut s);
        s.finish()
    }

    fn __bool__(&self) -> bool {
        true // an empty string is not a valid URL
    }

    pub fn __deepcopy__(&self, py: Python, _memo: &Bound<'_, PyDict>) -> PyResult<Py<PyAny>> {
        self.clone().into_py_any(py)
    }

    fn __getnewargs__(&self, py: Python<'_>) -> (Cow<'_, str>,) {
        (self.__str__(py),)
    }

    #[classmethod]
    #[pyo3(signature=(*, scheme, hosts=None, path=None, query=None, fragment=None, host=None, username=None, password=None, port=None, encode_components=false))]
    #[allow(clippy::too_many_arguments)]
    fn build<'py>(
        cls: &Bound<'py, PyType>,
        scheme: &str,
        hosts: Option<Vec<UrlHostParts>>,
        path: Option<&str>,
        query: Option<&str>,
        fragment: Option<&str>,
        // convenience parameters to build with a single host
        host: Option<&str>,
        username: Option<&str>,
        password: Option<&str>,
        port: Option<u16>,
        encode_components: bool,
    ) -> PyResult<Bound<'py, PyAny>> {
        let single_host;
        let hosts = if hosts.is_some() && (host.is_some() || username.is_some() || password.is_some() || port.is_some())
        {
            return Err(PyValueError::new_err(
                "expected one of `hosts` or singular values to be set.",
            ));
        } else if let Some(hosts) = &hosts {
            // check all of host / user / password / port empty
            for host in hosts {
                if host.is_empty() {
                    return Err(PyValueError::new_err(
                        "expected one of 'host', 'username', 'password' or 'port' to be set",
                    ));
                }
            }
            hosts
        } else if host.is_some() {
            single_host = [UrlHostParts {
                username: username.map(Into::into),
                password: password.map(Into::into),
                host: host.map(Into::into),
                port,
            }];
            &single_host[..]
        } else {
            return Err(PyValueError::new_err("expected either `host` or `hosts` to be set"));
        };

        let mut url = String::new();
        write_url(&mut url, scheme, hosts, path, query, fragment, encode_components)
            .expect("writing to string should not fail");
        cls.call1((url,))
    }
}

struct UrlHostParts {
    username: Option<String>,
    password: Option<String>,
    host: Option<String>,
    port: Option<u16>,
}

struct MaybeEncoded<'a>(&'a str, Option<&'static AsciiSet>);

impl fmt::Display for MaybeEncoded<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        if let Some(encode_set) = self.1 {
            write!(f, "{}", percent_encode(self.0.as_bytes(), encode_set))
        } else {
            write!(f, "{}", self.0)
        }
    }
}

impl UrlHostParts {
    fn is_empty(&self) -> bool {
        self.host.is_none() && self.password.is_none() && self.host.is_none() && self.port.is_none()
    }

    fn to_writer(&self, w: &mut impl Write, encode_components: bool) -> fmt::Result {
        let encode_userinfo = encode_components.then_some(&USERINFO_ENCODE_SET);
        match (&self.username, &self.password) {
            (Some(username), None) => write!(w, "{}@", MaybeEncoded(username, encode_userinfo))?,
            (None, Some(password)) => write!(w, ":{}@", MaybeEncoded(password, encode_userinfo))?,
            (Some(username), Some(password)) => write!(
                w,
                "{}:{}@",
                MaybeEncoded(username, encode_userinfo),
                MaybeEncoded(password, encode_userinfo)
            )?,
            (None, None) => {}
        }
        if let Some(host) = &self.host {
            // host might need punycode encoding
            if encode_components && let Some(encoded) = encode_str(host) {
                write!(w, "{encoded}")?;
            } else {
                write!(w, "{host}")?;
            }
        }
        // port does not need encoding
        if let Some(port) = self.port {
            write!(w, ":{port}")?;
        }
        Ok(())
    }
}

impl FromPyObject<'_, '_> for UrlHostParts {
    type Error = PyErr;
    fn extract(ob: Borrowed<'_, '_, PyAny>) -> PyResult<Self> {
        let py = ob.py();
        let dict = ob.cast::<PyDict>()?;
        Ok(UrlHostParts {
            username: dict.get_as(intern!(py, "username"))?,
            password: dict.get_as(intern!(py, "password"))?,
            host: dict.get_as(intern!(py, "host"))?,
            port: dict.get_as(intern!(py, "port"))?,
        })
    }
}

fn host_to_dict<'a>(py: Python<'a>, lib_url: &Url) -> PyResult<Bound<'a, PyDict>> {
    let dict = PyDict::new(py);
    dict.set_item("username", Some(lib_url.username()).filter(|s| !s.is_empty()))?;
    dict.set_item("password", lib_url.password())?;
    dict.set_item("host", lib_url.host_str())?;
    dict.set_item("port", lib_url.port_or_known_default())?;

    Ok(dict)
}

fn unicode_url<'s>(serialized: &'s str, lib_url: &Url) -> Cow<'s, str> {
    match lib_url.host() {
        Some(url::Host::Domain(domain)) if is_punnycode_domain(lib_url, domain) => {
            let mut s = serialized.to_string();
            if let Some(decoded) = decode_punycode(domain) {
                // replace the range containing the punycode domain with the decoded domain
                let start = lib_url.scheme().len() + 3;
                s.replace_range(start..start + domain.len(), &decoded);
            }
            Cow::Owned(s)
        }
        _ => Cow::Borrowed(serialized),
    }
}

fn decode_punycode(domain: &str) -> Option<String> {
    let mut result = String::with_capacity(domain.len());
    for chunk in domain.split('.') {
        if let Some(stripped) = chunk.strip_prefix(PUNYCODE_PREFIX) {
            result.push_str(&decode_to_string(stripped)?);
        } else {
            result.push_str(chunk);
        }
        result.push('.');
    }
    result.pop();
    Some(result)
}

static PUNYCODE_PREFIX: &str = "xn--";

fn is_punnycode_domain(lib_url: &Url, domain: &str) -> bool {
    scheme_is_special(lib_url.scheme()) && domain.split('.').any(|part| part.starts_with(PUNYCODE_PREFIX))
}

// https://datatracker.ietf.org/doc/html/rfc3986.html#section-2.4
// we must also percent-encode '%'
// const not static because it's only used to build the other sets
const BASE_ENCODE_SET: AsciiSet = CONTROLS.add(b'%');

/// See <https://url.spec.whatwg.org/#fragment-percent-encode-set>
static FRAGMENT_ENCODE_SET: AsciiSet = BASE_ENCODE_SET.add(b' ').add(b'"').add(b'<').add(b'>').add(b'`');

/// See <https://url.spec.whatwg.org/#query-percent-encode-set>
static QUERY_ENCODE_SET: AsciiSet = BASE_ENCODE_SET.add(b' ').add(b'"').add(b'#').add(b'<').add(b'>');

/// See <https://url.spec.whatwg.org/#special-query-percent-encode-set>
static SPECIAL_QUERY_ENCODE_SET: AsciiSet = QUERY_ENCODE_SET.add(b'\'');

/// See <https://url.spec.whatwg.org/#path-percent-encode-set>
static PATH_ENCODE_SET: AsciiSet = QUERY_ENCODE_SET.add(b'?').add(b'^').add(b'`').add(b'{').add(b'}');

/// See <https://url.spec.whatwg.org/#userinfo-percent-encode-set>
static USERINFO_ENCODE_SET: AsciiSet = PATH_ENCODE_SET
    .add(b'/')
    .add(b':')
    .add(b';')
    .add(b'=')
    .add(b'@')
    .add(b'[')
    .add(b'\\')
    .add(b']')
    .add(b'|');

// based on https://github.com/servo/rust-url/blob/1c1e406874b3d2aa6f36c5d2f3a5c2ea74af9efb/url/src/parser.rs#L161-L167
pub fn scheme_is_special(scheme: &str) -> bool {
    matches!(scheme, "http" | "https" | "ws" | "wss" | "ftp" | "file")
}

fn serialize_url_without_path_slash(url: &Url) -> String {
    // use pointer arithmetic to find the pieces we need to build the string
    let s = url.as_str();
    let path = url.path();
    assert_eq!(path, "/", "`path_is_empty` expected to be set only when path is '/'");

    assert!(
        // Safety for the below: `s` and `path` should be from the same text slice, so
        // we can pull out the slices of `s` that don't include `path`.
        s.as_ptr() <= path.as_ptr() && unsafe { s.as_ptr().add(s.len()) } >= unsafe { path.as_ptr().add(path.len()) }
    );

    let prefix_len = path.as_ptr() as usize - s.as_ptr() as usize;
    let suffix_len = s.len() - (prefix_len + path.len());

    // Safety: prefix is the slice of `s` leading to `path`, protected by the assert above.
    let prefix = unsafe { std::str::from_utf8_unchecked(std::slice::from_raw_parts(s.as_ptr(), prefix_len)) };
    // Safety: suffix is the slice of `s` after `path`, protected by the assert above.
    let suffix =
        unsafe { std::str::from_utf8_unchecked(std::slice::from_raw_parts(path.as_ptr().add(path.len()), suffix_len)) };

    format!("{prefix}{suffix}")
}
