use std::fmt;

use pyo3::prelude::*;
use pyo3::types::PyDict;
use strum::EnumMessage;

use super::kinds::ErrorKind;

/// Used to store individual items of the error location, e.g. a string for key/field names
/// or a number for array indices.
/// Note: ints are also used for keys of `Dict[int, ...]`
#[derive(Debug, Clone)]
pub enum LocItem {
    S(String),
    I(usize),
}
// we could use the From trait to make creating Location's much easier, would it be worth it?

impl fmt::Display for LocItem {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            LocItem::S(s) => write!(f, "{}", s),
            LocItem::I(i) => write!(f, "{}", i),
        }
    }
}

/// Error locations are represented by a vector of `LocItem`s.
/// e.g. if the error occurred in the third member of a list called `foo`,
/// the location would be `["foo", 2]`.
pub type Location = Vec<LocItem>;

/// A `ValLineError` is a single error that occurred during validation which
/// combine to eventually form a `ValidationError`. I don't like the name `ValLineError`,
/// but it's the best I could come up with (for now).
/// `#[pyclass]` is required to allow `ValidationError::new_err((line_errors, name))` - the lines are converted to
/// a python type to create the validation error.
#[pyclass]
#[derive(Debug, Default, Clone)]
pub struct ValLineError {
    pub kind: ErrorKind,
    pub location: Location,
    pub message: Option<String>,
    pub input_value: Option<PyObject>,
    pub context: Option<Context>,
}

impl fmt::Display for ValLineError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.format_pretty(f, None)
    }
}

impl ValLineError {
    fn format_pretty(&self, f: &mut fmt::Formatter<'_>, py: Option<Python>) -> fmt::Result {
        if !self.location.is_empty() {
            let loc = self
                .location
                .iter()
                .map(|i| i.to_string())
                .collect::<Vec<String>>()
                .join(" -> ");
            writeln!(f, "{}", loc)?;
        }
        write!(f, "  {} [kind={}", self.message(), self.kind())?;
        if let Some(ctx) = &self.context {
            write!(f, ", context={}", ctx)?;
        }
        if let Some(input_value) = &self.input_value {
            write!(f, ", input_value={}", input_value)?;
            if let Some(py) = py {
                if let Ok(type_) = input_value.as_ref(py).get_type().name() {
                    write!(f, ", input_type={}", type_)?;
                }
            }
        }
        write!(f, "]")
    }

    pub fn pretty(&self, py: Option<Python>) -> String {
        format!("{}", Fmt(|f| self.format_pretty(f, py)))
    }
}

// hack from https://users.rust-lang.org/t/reusing-an-fmt-formatter/8531/4
struct Fmt<F>(pub F)
where
    F: Fn(&mut fmt::Formatter) -> fmt::Result;

impl<F> fmt::Display for Fmt<F>
where
    F: Fn(&mut fmt::Formatter) -> fmt::Result,
{
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        (self.0)(f)
    }
}

impl ValLineError {
    // TODO in theory we could mutate the error since it won't be used again, but I
    // couldn't get mut to work where this is called
    pub fn prefix_location(&self, location: &Location) -> ValLineError {
        let mut new = self.clone();
        if self.location.is_empty() {
            new.location = location.clone();
        } else {
            new.location = [location.clone(), new.location].concat();
        }
        new
    }

    pub fn as_dict(&self, py: Python) -> PyResult<PyObject> {
        let dict = PyDict::new(py);
        dict.set_item("kind", self.kind())?;
        dict.set_item("loc", self.location(py))?;
        dict.set_item("message", self.message())?;
        if let Some(input_value) = &self.input_value {
            dict.set_item("input_value", input_value)?;
        }
        if let Some(context) = &self.context {
            dict.set_item("context", context)?;
        }
        Ok(dict.into_py(py))
    }

    fn kind(&self) -> String {
        self.kind.to_string()
    }

    fn location(&self, py: Python) -> PyObject {
        let mut loc: Vec<PyObject> = Vec::with_capacity(self.location.len());
        for location in &self.location {
            let item: PyObject = match location {
                LocItem::S(key) => key.into_py(py),
                LocItem::I(index) => index.into_py(py),
            };
            loc.push(item);
        }
        loc.into_py(py)
    }

    fn message(&self) -> String {
        let raw = self.raw_message();
        match self.context {
            Some(ref context) => context.render(raw),
            None => raw,
        }
    }

    fn raw_message(&self) -> String {
        // TODO string substitution
        if let Some(ref message) = self.message {
            message.to_string()
        } else {
            match self.kind.get_message() {
                Some(message) => message.to_string(),
                None => self.kind(),
            }
        }
    }
}

#[derive(Debug, Clone)]
pub struct Context(Vec<(String, ContextValue)>);

impl Context {
    pub fn new<K: Into<String>, V: Into<ContextValue>, I: IntoIterator<Item = (K, V)>>(raw: I) -> Self {
        Self(raw.into_iter().map(|(k, v)| (k.into(), v.into())).collect())
    }

    pub fn render(&self, template: String) -> String {
        let mut rendered = template;
        for (key, value) in &self.0 {
            rendered = rendered.replace(&format!("{{{}}}", key), &value.to_string());
        }
        rendered
    }
}

impl fmt::Display for Context {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let loc = self
            .0
            .iter()
            .map(|(k, v)| format!("{}: {}", k, v))
            .collect::<Vec<String>>()
            .join(", ");
        write!(f, "{{{}}}", loc)
    }
}

// maybe this is overkill and we should just use fmt::Display an convert to string when creating Context?
#[derive(Debug, Clone)]
pub enum ContextValue {
    S(String),
    I(i64),
    F(f64),
}

impl fmt::Display for ContextValue {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ContextValue::S(v) => write!(f, "{}", v),
            ContextValue::I(v) => write!(f, "{}", v),
            ContextValue::F(v) => write!(f, "{}", v),
        }
    }
}

impl From<String> for ContextValue {
    fn from(str: String) -> Self {
        Self::S(str)
    }
}

impl From<i64> for ContextValue {
    fn from(int: i64) -> Self {
        Self::I(int)
    }
}

impl From<usize> for ContextValue {
    fn from(u: usize) -> Self {
        Self::I(u as i64)
    }
}

impl From<f64> for ContextValue {
    fn from(f: f64) -> Self {
        Self::F(f)
    }
}

impl ToPyObject for ContextValue {
    fn to_object(&self, py: Python) -> PyObject {
        match self {
            ContextValue::S(v) => v.into_py(py),
            ContextValue::I(v) => v.into_py(py),
            ContextValue::F(v) => v.into_py(py),
        }
    }
}

impl ToPyObject for Context {
    fn to_object(&self, py: Python) -> PyObject {
        let dict = PyDict::new(py);
        for (key, value) in &self.0 {
            dict.set_item(key, value).unwrap();
        }
        dict.into_py(py)
    }
}
