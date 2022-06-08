use pyo3::{PyAny, PyResult};

use super::parse_json::JsonInput;
use crate::errors::LocItem;

pub trait ToLocItem {
    fn to_loc(&self) -> LocItem;
}

impl ToLocItem for String {
    fn to_loc(&self) -> LocItem {
        LocItem::S(self.clone())
    }
}

impl ToLocItem for &str {
    fn to_loc(&self) -> LocItem {
        LocItem::S(self.to_string())
    }
}

/// This is required by since JSON object keys are always strings, I don't think it can be called
impl ToLocItem for JsonInput {
    #[no_coverage]
    fn to_loc(&self) -> LocItem {
        match self {
            JsonInput::Int(i) => LocItem::I(*i as usize),
            JsonInput::String(s) => LocItem::S(s.to_string()),
            v => LocItem::S(format!("{:?}", v)),
        }
    }
}

impl ToLocItem for PyAny {
    fn to_loc(&self) -> LocItem {
        if let Ok(key_str) = self.extract::<String>() {
            LocItem::S(key_str)
        } else if let Ok(key_int) = self.extract::<usize>() {
            LocItem::I(key_int)
        } else {
            // best effort is to use repr
            match repr_string(self) {
                Ok(s) => LocItem::S(s),
                Err(_) => LocItem::S(format!("{:?}", self)),
            }
        }
    }
}

fn repr_string(py_any: &PyAny) -> PyResult<String> {
    let repr_result = py_any.repr()?;
    let repr: String = repr_result.extract()?;
    Ok(repr)
}
