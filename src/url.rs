use idna::punycode::decode_to_string;
use pyo3::prelude::*;

#[pyclass(name = "Url", module = "pydantic_core._pydantic_core")]
#[derive(Clone)]
#[cfg_attr(debug_assertions, derive(Debug))]
pub struct PyUrl {
    lib_url: url::Url,
}

static PUNYCODE_PREFIX: &str = "xn--";

impl PyUrl {
    pub fn new(lib_url: url::Url) -> Self {
        Self { lib_url }
    }

    pub fn into_url(self) -> url::Url {
        self.lib_url
    }

    fn decode_punycode(&self, domain: &str) -> Option<String> {
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

    fn is_punnycode_domain(&self, domain: &str) -> bool {
        self.is_special() && domain.split('.').any(|part| part.starts_with(PUNYCODE_PREFIX))
    }

    // based on https://github.com/servo/rust-url/blob/1c1e406874b3d2aa6f36c5d2f3a5c2ea74af9efb/url/src/parser.rs#L161-L167
    fn is_special(&self) -> bool {
        matches!(self.lib_url.scheme(), "http" | "https" | "ws" | "wss" | "ftp" | "file")
    }
}

#[pymethods]
impl PyUrl {
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
            Some(url::Host::Domain(domain)) if self.is_punnycode_domain(domain) => self.decode_punycode(domain),
            _ => self.lib_url.host_str().map(|h| h.to_string()),
        }
    }

    #[getter]
    pub fn host_type(&self) -> Option<&'static str> {
        match self.lib_url.host() {
            Some(url::Host::Domain(domain)) if self.is_punnycode_domain(domain) => Some("punycode_domain"),
            Some(url::Host::Domain(_)) => Some("domain"),
            Some(url::Host::Ipv4(_)) => Some("ipv4"),
            Some(url::Host::Ipv6(_)) => Some("ipv6"),
            None => None,
        }
    }

    #[getter]
    pub fn port(&self) -> Option<u16> {
        self.lib_url.port()
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
        let s = self.lib_url.to_string();

        match self.lib_url.host() {
            Some(url::Host::Domain(domain)) if self.is_punnycode_domain(domain) => {
                // we know here that we have a punycode domain, so we simply replace the first instance
                // of the punycode domain with the decoded domain
                // this is ugly, but since `slice()`, `host_start` and `host_end` are all private to `Url`,
                // we have no better option, since the `schema` has to be `https`, `http` etc, (see `is_special` above),
                // we can safely assume that the first match for the domain, is the domain
                match self.decode_punycode(domain) {
                    Some(decoded) => s.replacen(domain, &decoded, 1),
                    None => s,
                }
            }
            _ => s,
        }
    }

    pub fn __str__(&self) -> String {
        self.lib_url.to_string()
    }

    pub fn __repr__(&self) -> String {
        format!("Url('{}')", self.lib_url)
    }
}
