use idna::punycode::decode_to_string;
use pyo3::once_cell::GILOnceCell;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use url::Url;

use crate::SchemaValidator;

static SCHEMA_DEFINITION_URL: GILOnceCell<SchemaValidator> = GILOnceCell::new();

#[pyclass(name = "Url", module = "pydantic_core._pydantic_core")]
#[derive(Clone)]
#[cfg_attr(debug_assertions, derive(Debug))]
pub struct PyUrl {
    lib_url: Url,
}

impl PyUrl {
    pub fn new(lib_url: Url) -> Self {
        Self { lib_url }
    }

    pub fn into_url(self) -> Url {
        self.lib_url
    }
}

fn build_schema_validator(py: Python, schema_type: &str) -> SchemaValidator {
    let schema: &PyDict = PyDict::new(py);
    schema.set_item("type", schema_type).unwrap();
    SchemaValidator::py_new(py, schema, None).unwrap()
}

#[pymethods]
impl PyUrl {
    #[new]
    pub fn py_new(py: Python, url: &PyAny) -> PyResult<Self> {
        let schema_obj = SCHEMA_DEFINITION_URL
            .get_or_init(py, || build_schema_validator(py, "url"))
            .validate_python(py, url, None, None)?;
        schema_obj.extract(py)
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
            _ => self.lib_url.host_str().map(|h| h.to_string()),
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
            path => Some(path),
        }
    }

    #[getter]
    pub fn query(&self) -> Option<&str> {
        self.lib_url.query()
    }

    pub fn query_params(&self, py: Python) -> PyObject {
        // `query_pairs` is a pure iterator, so can't implement `ExactSizeIterator`, hence we need the temporary `Vec`
        self.lib_url
            .query_pairs()
            .map(|(key, value)| (key, value).into_py(py))
            .collect::<Vec<PyObject>>()
            .into_py(py)
    }

    #[getter]
    pub fn fragment(&self) -> Option<&str> {
        self.lib_url.fragment()
    }

    // string representation of the URL, with punycode decoded when appropriate
    pub fn unicode_string(&self) -> String {
        unicode_url(&self.lib_url)
    }

    pub fn __str__(&self) -> &str {
        self.lib_url.as_str()
    }

    pub fn __repr__(&self) -> String {
        format!("Url('{}')", self.lib_url)
    }
}

#[pyclass(name = "MultiHostUrl", module = "pydantic_core._pydantic_core")]
#[derive(Clone)]
#[cfg_attr(debug_assertions, derive(Debug))]
pub struct PyMultiHostUrl {
    ref_url: PyUrl,
    extra_urls: Option<Vec<Url>>,
}

impl PyMultiHostUrl {
    pub fn new(ref_url: Url, extra_urls: Option<Vec<Url>>) -> Self {
        Self {
            ref_url: PyUrl::new(ref_url),
            extra_urls,
        }
    }

    pub fn mut_lib_url(&mut self) -> &mut Url {
        &mut self.ref_url.lib_url
    }
}

static SCHEMA_DEFINITION_MULTI_HOST_URL: GILOnceCell<SchemaValidator> = GILOnceCell::new();

#[pymethods]
impl PyMultiHostUrl {
    #[new]
    pub fn py_new(py: Python, url: &PyAny) -> PyResult<Self> {
        let schema_obj = SCHEMA_DEFINITION_MULTI_HOST_URL
            .get_or_init(py, || build_schema_validator(py, "multi-host-url"))
            .validate_python(py, url, None, None)?;
        schema_obj.extract(py)
    }

    #[getter]
    pub fn scheme(&self) -> &str {
        self.ref_url.scheme()
    }

    pub fn hosts<'py>(&self, py: Python<'py>) -> PyResult<Vec<&'py PyDict>> {
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

    pub fn query_params(&self, py: Python) -> PyObject {
        self.ref_url.query_params(py)
    }

    #[getter]
    pub fn fragment(&self) -> Option<&str> {
        self.ref_url.fragment()
    }

    // string representation of the URL, with punycode decoded when appropriate
    pub fn unicode_string(&self) -> String {
        if let Some(extra_urls) = &self.extra_urls {
            let schema = self.ref_url.lib_url.scheme();
            let host_offset = schema.len() + 3;

            let mut full_url = self.ref_url.unicode_string();
            full_url.insert(host_offset, ',');

            // special urls will have had a trailing slash added, non-special urls will not
            // hence we need to remove the last char if the schema is special
            #[allow(clippy::bool_to_int_with_if)]
            let sub = if schema_is_special(schema) { 1 } else { 0 };

            let hosts = extra_urls
                .iter()
                .map(|url| {
                    let str = unicode_url(url);
                    str[host_offset..str.len() - sub].to_string()
                })
                .collect::<Vec<String>>()
                .join(",");
            full_url.insert_str(host_offset, &hosts);
            full_url
        } else {
            self.ref_url.unicode_string()
        }
    }

    pub fn __str__(&self) -> String {
        if let Some(extra_urls) = &self.extra_urls {
            let schema = self.ref_url.lib_url.scheme();
            let host_offset = schema.len() + 3;

            let mut full_url = self.ref_url.lib_url.to_string();
            full_url.insert(host_offset, ',');

            // special urls will have had a trailing slash added, non-special urls will not
            // hence we need to remove the last char if the schema is special
            #[allow(clippy::bool_to_int_with_if)]
            let sub = if schema_is_special(schema) { 1 } else { 0 };

            let hosts = extra_urls
                .iter()
                .map(|url| {
                    let str = url.as_str();
                    &str[host_offset..str.len() - sub]
                })
                .collect::<Vec<&str>>()
                .join(",");
            full_url.insert_str(host_offset, &hosts);
            full_url
        } else {
            self.ref_url.__str__().to_string()
        }
    }

    pub fn __repr__(&self) -> String {
        format!("Url('{}')", self.__str__())
    }
}

fn host_to_dict<'a>(py: Python<'a>, lib_url: &Url) -> PyResult<&'a PyDict> {
    let dict = PyDict::new(py);
    dict.set_item(
        "username",
        match lib_url.username() {
            "" => py.None(),
            user => user.into_py(py),
        },
    )?;
    dict.set_item("password", lib_url.password())?;
    dict.set_item("host", lib_url.host_str())?;
    dict.set_item("port", lib_url.port_or_known_default())?;

    Ok(dict)
}

fn unicode_url(lib_url: &Url) -> String {
    let mut s = lib_url.to_string();

    match lib_url.host() {
        Some(url::Host::Domain(domain)) if is_punnycode_domain(lib_url, domain) => {
            if let Some(decoded) = decode_punycode(domain) {
                // replace the range containing the punycode domain with the decoded domain
                let start = lib_url.scheme().len() + 3;
                s.replace_range(start..start + domain.len(), &decoded)
            }
            s
        }
        _ => s,
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
    schema_is_special(lib_url.scheme()) && domain.split('.').any(|part| part.starts_with(PUNYCODE_PREFIX))
}

// based on https://github.com/servo/rust-url/blob/1c1e406874b3d2aa6f36c5d2f3a5c2ea74af9efb/url/src/parser.rs#L161-L167
pub fn schema_is_special(schema: &str) -> bool {
    matches!(schema, "http" | "https" | "ws" | "wss" | "ftp" | "file")
}
