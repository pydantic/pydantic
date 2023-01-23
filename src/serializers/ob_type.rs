use pyo3::ffi::PyTypeObject;
use pyo3::intern;
use pyo3::once_cell::GILOnceCell;
use pyo3::prelude::*;
use pyo3::types::{
    PyByteArray, PyBytes, PyDate, PyDateTime, PyDelta, PyDict, PyFrozenSet, PyList, PySet, PyString, PyTime, PyTuple,
};

use strum::Display;
use strum_macros::EnumString;

use crate::url::{PyMultiHostUrl, PyUrl};

#[derive(Debug, Clone)]
pub struct ObTypeLookup {
    none: usize,
    // numeric types
    int: usize,
    bool: usize,
    float: usize,
    // string types
    string: usize,
    bytes: usize,
    bytearray: usize,
    // mapping types
    dict: usize,
    // sequence types
    list: usize,
    tuple: usize,
    set: usize,
    frozenset: usize,
    // datetime types
    datetime: usize,
    date: usize,
    time: usize,
    timedelta: usize,
    // types from this package
    url: usize,
    multi_host_url: usize,
}

static TYPE_LOOKUP: GILOnceCell<ObTypeLookup> = GILOnceCell::new();

pub enum IsType {
    Exact,
    Subclass,
    False,
}

impl ObTypeLookup {
    fn new(py: Python) -> Self {
        let lib_url = url::Url::parse("https://example.com").unwrap();
        Self {
            none: py.None().as_ref(py).get_type_ptr() as usize,
            // numeric types
            int: 0i32.into_py(py).as_ref(py).get_type_ptr() as usize,
            bool: true.into_py(py).as_ref(py).get_type_ptr() as usize,
            float: 0f32.into_py(py).as_ref(py).get_type_ptr() as usize,
            // string types
            string: PyString::new(py, "s").get_type_ptr() as usize,
            bytes: PyBytes::new(py, b"s").get_type_ptr() as usize,
            bytearray: PyByteArray::new(py, b"s").get_type_ptr() as usize,
            // sequence types
            list: PyList::empty(py).get_type_ptr() as usize,
            tuple: PyTuple::empty(py).get_type_ptr() as usize,
            set: PySet::empty(py).unwrap().get_type_ptr() as usize,
            frozenset: PyFrozenSet::empty(py).unwrap().get_type_ptr() as usize,
            // mapping types
            dict: PyDict::new(py).get_type_ptr() as usize,
            // datetime types
            datetime: PyDateTime::new(py, 2000, 1, 1, 0, 0, 0, 0, None)
                .unwrap()
                .get_type_ptr() as usize,
            date: PyDate::new(py, 2000, 1, 1).unwrap().get_type_ptr() as usize,
            time: PyTime::new(py, 0, 0, 0, 0, None).unwrap().get_type_ptr() as usize,
            timedelta: PyDelta::new(py, 0, 0, 0, false).unwrap().get_type_ptr() as usize,
            // types from this package
            url: PyUrl::new(lib_url.clone()).into_py(py).as_ref(py).get_type_ptr() as usize,
            multi_host_url: PyMultiHostUrl::new(lib_url, None).into_py(py).as_ref(py).get_type_ptr() as usize,
        }
    }

    pub fn cached(py: Python<'_>) -> &Self {
        TYPE_LOOKUP.get_or_init(py, || Self::new(py))
    }

    pub fn is_type(&self, value: &PyAny, expected_ob_type: ObType) -> IsType {
        self.ob_type_is_expected(Some(value), value.get_type_ptr(), expected_ob_type)
    }

    fn ob_type_is_expected(
        &self,
        op_value: Option<&PyAny>,
        type_ptr: *mut PyTypeObject,
        expected_ob_type: ObType,
    ) -> IsType {
        let ob_type = type_ptr as usize;
        let ans = match expected_ob_type {
            ObType::None => self.none == ob_type,
            ObType::Int => self.int == ob_type,
            // op_value is None on recursive calls
            ObType::IntSubclass => self.int == ob_type && op_value.is_none(),
            ObType::Bool => self.bool == ob_type,
            ObType::Float => self.float == ob_type,
            ObType::FloatSubclass => self.float == ob_type && op_value.is_none(),
            ObType::Str => self.string == ob_type,
            ObType::StrSubclass => self.string == ob_type && op_value.is_none(),
            ObType::Dict => self.dict == ob_type,
            ObType::List => self.list == ob_type,
            ObType::Tuple => self.tuple == ob_type,
            ObType::Set => self.set == ob_type,
            ObType::Frozenset => self.frozenset == ob_type,
            ObType::Bytes => self.bytes == ob_type,
            ObType::Datetime => self.datetime == ob_type,
            ObType::Date => self.date == ob_type,
            ObType::Time => self.time == ob_type,
            ObType::Timedelta => self.timedelta == ob_type,
            ObType::Bytearray => self.bytearray == ob_type,
            ObType::Url => self.url == ob_type,
            ObType::MultiHostUrl => self.multi_host_url == ob_type,
            ObType::Dataclass => is_dataclass(op_value),
            ObType::PydanticModel => is_pydantic_model(op_value),
            ObType::Unknown => false,
        };

        if ans {
            IsType::Exact
        } else {
            // this allows for subtypes of the supported class types,
            // if we didn't successfully confirm the type, we try again with the next base type pointer provided
            // it's not null
            let base_type_ptr = unsafe { (*type_ptr).tp_base };
            if base_type_ptr.is_null() {
                IsType::False
            } else {
                // as bellow, we don't want to tests for dataclass etc. again, so we pass None as op_value
                match self.ob_type_is_expected(None, base_type_ptr, expected_ob_type) {
                    IsType::False => IsType::False,
                    _ => IsType::Subclass,
                }
            }
        }
    }

    pub fn get_type(&self, value: &PyAny) -> ObType {
        self.lookup_by_ob_type(Some(value), value.get_type_ptr())
    }

    fn lookup_by_ob_type(&self, op_value: Option<&PyAny>, type_ptr: *mut PyTypeObject) -> ObType {
        let ob_type = type_ptr as usize;
        // this should be pretty fast, but still order is a bit important, so the most common types should come first
        // thus we don't follow the order of ObType
        if ob_type == self.none {
            ObType::None
        } else if ob_type == self.int {
            // op_value is None on recursive calls, e.g. hence the original value would be a subclass
            match op_value {
                Some(_) => ObType::Int,
                None => ObType::IntSubclass,
            }
        } else if ob_type == self.bool {
            ObType::Bool
        } else if ob_type == self.float {
            match op_value {
                Some(_) => ObType::Float,
                None => ObType::FloatSubclass,
            }
        } else if ob_type == self.string {
            match op_value {
                Some(_) => ObType::Str,
                None => ObType::StrSubclass,
            }
        } else if ob_type == self.dict {
            ObType::Dict
        } else if ob_type == self.list {
            ObType::List
        } else if ob_type == self.tuple {
            ObType::Tuple
        } else if ob_type == self.set {
            ObType::Set
        } else if ob_type == self.frozenset {
            ObType::Frozenset
        } else if ob_type == self.bytes {
            ObType::Bytes
        } else if ob_type == self.datetime {
            ObType::Datetime
        } else if ob_type == self.date {
            ObType::Date
        } else if ob_type == self.time {
            ObType::Time
        } else if ob_type == self.timedelta {
            ObType::Timedelta
        } else if ob_type == self.bytearray {
            ObType::Bytearray
        } else if ob_type == self.url {
            ObType::Url
        } else if ob_type == self.multi_host_url {
            ObType::MultiHostUrl
        } else if is_dataclass(op_value) {
            ObType::Dataclass
        } else if is_pydantic_model(op_value) {
            ObType::PydanticModel
        } else {
            // this allows for subtypes of the supported class types,
            // if `ob_type` didn't match any member of self, we try again with the next base type pointer
            let base_type_ptr = unsafe { (*type_ptr).tp_base };
            if base_type_ptr.is_null() {
                ObType::Unknown
            } else {
                // we don't want to tests for dataclass etc. again, so we pass None as op_value
                self.lookup_by_ob_type(None, base_type_ptr)
            }
        }
    }
}

fn is_dataclass(op_value: Option<&PyAny>) -> bool {
    if let Some(value) = op_value {
        value
            .hasattr(intern!(value.py(), "__dataclass_fields__"))
            .unwrap_or(false)
    } else {
        false
    }
}

fn is_pydantic_model(op_value: Option<&PyAny>) -> bool {
    if let Some(value) = op_value {
        value
            .hasattr(intern!(value.py(), "__pydantic_validator__"))
            .unwrap_or(false)
    } else {
        false
    }
}

#[derive(Debug, Clone, EnumString, Display)]
#[strum(serialize_all = "snake_case")]
pub enum ObType {
    None,
    // numeric types
    Int,
    IntSubclass,
    Bool,
    Float,
    FloatSubclass,
    // string types
    Str,
    StrSubclass,
    Bytes,
    Bytearray,
    // sequence types
    List,
    Tuple,
    Set,
    Frozenset,
    // mapping types
    Dict,
    // datetime types
    Datetime,
    Date,
    Time,
    Timedelta,
    // types from this package
    Url,
    MultiHostUrl,
    // dataclasses and pydantic models
    Dataclass,
    PydanticModel,
    // unknown type
    Unknown,
}
