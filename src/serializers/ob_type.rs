use pyo3::once_cell::GILOnceCell;
use pyo3::prelude::*;
use pyo3::types::{
    PyBool, PyByteArray, PyBytes, PyDate, PyDateTime, PyDelta, PyDict, PyFloat, PyFrozenSet, PyInt, PyIterator, PyList,
    PySet, PyString, PyTime, PyTuple, PyType,
};
use pyo3::{intern, AsPyPointer, PyTypeInfo};

use strum::Display;
use strum_macros::EnumString;

use crate::url::{PyMultiHostUrl, PyUrl};

#[derive(Debug, Clone)]
pub struct ObTypeLookup {
    // valid JSON types
    none: usize,
    int: usize,
    bool: usize,
    float: usize,
    string: usize,
    list: usize,
    dict: usize,
    // other numeric types
    decimal_object: PyObject,
    // other string types
    bytes: usize,
    bytearray: usize,
    // other sequence types
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
    // enum type
    enum_object: PyObject,
    // generator
    generator_object: PyObject,
    // path
    path_object: PyObject,
    // uuid type
    uuid_object: PyObject,
}

static TYPE_LOOKUP: GILOnceCell<ObTypeLookup> = GILOnceCell::new();

#[derive(Debug)]
pub enum IsType {
    Exact,
    Subclass,
    False,
}

impl ObTypeLookup {
    fn new(py: Python) -> Self {
        Self {
            none: py.None().as_ref(py).get_type_ptr() as usize,
            int: PyInt::type_object_raw(py) as usize,
            bool: PyBool::type_object_raw(py) as usize,
            float: PyFloat::type_object_raw(py) as usize,
            list: PyList::type_object_raw(py) as usize,
            dict: PyDict::type_object_raw(py) as usize,
            decimal_object: py.import("decimal").unwrap().getattr("Decimal").unwrap().to_object(py),
            string: PyString::type_object_raw(py) as usize,
            bytes: PyBytes::type_object_raw(py) as usize,
            bytearray: PyByteArray::type_object_raw(py) as usize,
            tuple: PyTuple::type_object_raw(py) as usize,
            set: PySet::type_object_raw(py) as usize,
            frozenset: PyFrozenSet::type_object_raw(py) as usize,
            datetime: PyDateTime::type_object_raw(py) as usize,
            date: PyDate::type_object_raw(py) as usize,
            time: PyTime::type_object_raw(py) as usize,
            timedelta: PyDelta::type_object_raw(py) as usize,
            url: PyUrl::type_object_raw(py) as usize,
            multi_host_url: PyMultiHostUrl::type_object_raw(py) as usize,
            enum_object: py.import("enum").unwrap().getattr("Enum").unwrap().to_object(py),
            generator_object: py
                .import("types")
                .unwrap()
                .getattr("GeneratorType")
                .unwrap()
                .to_object(py),
            path_object: py.import("pathlib").unwrap().getattr("Path").unwrap().to_object(py),
            uuid_object: py.import("uuid").unwrap().getattr("UUID").unwrap().to_object(py),
        }
    }

    pub fn cached(py: Python<'_>) -> &Self {
        TYPE_LOOKUP.get_or_init(py, || Self::new(py))
    }

    pub fn is_type(&self, value: &PyAny, expected_ob_type: ObType) -> IsType {
        match self.ob_type_is_expected(Some(value), value.get_type(), &expected_ob_type) {
            IsType::False => {
                if expected_ob_type == self.fallback_isinstance(value) {
                    IsType::Subclass
                } else {
                    IsType::False
                }
            }
            is_type => is_type,
        }
    }

    fn ob_type_is_expected(&self, op_value: Option<&PyAny>, py_type: &PyType, expected_ob_type: &ObType) -> IsType {
        let type_ptr = py_type.as_ptr();
        let ob_type = type_ptr as usize;
        let ans = match expected_ob_type {
            ObType::None => self.none == ob_type,
            ObType::Int => self.int == ob_type,
            // op_value is None on recursive calls
            ObType::IntSubclass => self.int == ob_type && op_value.is_none(),
            ObType::Bool => self.bool == ob_type,
            ObType::Float => {
                if self.float == ob_type {
                    true
                } else if self.int == ob_type {
                    // special case for int as the input to float serializer,
                    // https://github.com/pydantic/pydantic-core/pull/866
                    return IsType::Subclass;
                } else {
                    false
                }
            }
            ObType::FloatSubclass => self.float == ob_type && op_value.is_none(),
            ObType::Str => self.string == ob_type,
            ObType::List => self.list == ob_type,
            ObType::Dict => self.dict == ob_type,
            ObType::Decimal => self.decimal_object.as_ptr() as usize == ob_type,
            ObType::StrSubclass => self.string == ob_type && op_value.is_none(),
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
            ObType::PydanticSerializable => is_pydantic_serializable(op_value),
            ObType::Enum => self.enum_object.as_ptr() as usize == ob_type,
            ObType::Generator => self.generator_object.as_ptr() as usize == ob_type,
            ObType::Path => self.path_object.as_ptr() as usize == ob_type,
            ObType::Uuid => self.uuid_object.as_ptr() as usize == ob_type,
            ObType::Unknown => false,
        };

        if ans {
            IsType::Exact
        } else {
            // this allows for subtypes of the supported class types,
            // if we didn't successfully confirm the type, we try again with the next base type pointer provided
            // it's not null
            match get_base_type(py_type) {
                // as below, we don't want to tests for dataclass etc. again, so we pass None as op_value
                Some(base_type) => match self.ob_type_is_expected(None, base_type, expected_ob_type) {
                    IsType::False => IsType::False,
                    _ => IsType::Subclass,
                },
                None => IsType::False,
            }
        }
    }

    pub fn get_type(&self, value: &PyAny) -> ObType {
        match self.lookup_by_ob_type(Some(value), value.get_type()) {
            ObType::Unknown => self.fallback_isinstance(value),
            ob_type => ob_type,
        }
    }

    fn lookup_by_ob_type(&self, op_value: Option<&PyAny>, py_type: &PyType) -> ObType {
        let ob_type = py_type.as_ptr() as usize;
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
        } else if ob_type == self.list {
            ObType::List
        } else if ob_type == self.dict {
            ObType::Dict
        } else if ob_type == self.decimal_object.as_ptr() as usize {
            ObType::Decimal
        } else if ob_type == self.bytes {
            ObType::Bytes
        } else if ob_type == self.tuple {
            ObType::Tuple
        } else if ob_type == self.set {
            ObType::Set
        } else if ob_type == self.frozenset {
            ObType::Frozenset
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
        } else if ob_type == self.uuid_object.as_ptr() as usize {
            ObType::Uuid
        } else if is_pydantic_serializable(op_value) {
            ObType::PydanticSerializable
        } else if is_dataclass(op_value) {
            ObType::Dataclass
        } else if self.is_enum(op_value, py_type) {
            ObType::Enum
        } else if ob_type == self.generator_object.as_ptr() as usize || is_generator(op_value) {
            ObType::Generator
        } else if ob_type == self.path_object.as_ptr() as usize {
            ObType::Path
        } else {
            // this allows for subtypes of the supported class types,
            // if `ob_type` didn't match any member of self, we try again with the next base type pointer
            match get_base_type(py_type) {
                // we don't want to tests for dataclass etc. again, so we pass None as op_value
                Some(base_type) => self.lookup_by_ob_type(None, base_type),
                None => ObType::Unknown,
            }
        }
    }

    fn is_enum(&self, op_value: Option<&PyAny>, py_type: &PyType) -> bool {
        // only test on the type itself, not base types
        if op_value.is_some() {
            let enum_meta_type = self.enum_object.as_ref(py_type.py()).get_type();
            let meta_type = py_type.get_type();
            meta_type.is(enum_meta_type)
        } else {
            false
        }
    }

    /// If our logic for finding types by recursively checking `tp_base` fails, we fallback to this which
    /// uses `isinstance` thus supporting both mixins and classes that implement `__instancecheck__`.
    /// We care about order here since:
    /// 1. we pay a price for each `isinstance` call
    /// 2. some types are subclasses of others, e.g. `bool` is a subclass of `int`
    /// hence we put common types first
    /// In addition, some types have inheritance set as a bitflag on the type object:
    /// https://github.com/python/cpython/blob/v3.12.0rc1/Include/object.h#L546-L553
    /// Hence they come first
    fn fallback_isinstance(&self, value: &PyAny) -> ObType {
        let py = value.py();
        if PyInt::is_type_of(value) {
            ObType::IntSubclass
        } else if PyString::is_type_of(value) {
            ObType::StrSubclass
        } else if PyBytes::is_type_of(value) {
            ObType::Bytes
        } else if PyList::is_type_of(value) {
            ObType::List
        } else if PyTuple::is_type_of(value) {
            ObType::Tuple
        } else if PyDict::is_type_of(value) {
            ObType::Dict
        } else if PyBool::is_type_of(value) {
            ObType::Bool
        } else if PyFloat::is_type_of(value) {
            ObType::FloatSubclass
        } else if PyByteArray::is_type_of(value) {
            ObType::Bytearray
        } else if PySet::is_type_of(value) {
            ObType::Set
        } else if PyFrozenSet::is_type_of(value) {
            ObType::Frozenset
        } else if PyDateTime::is_type_of(value) {
            ObType::Datetime
        } else if PyDate::is_type_of(value) {
            ObType::Date
        } else if PyTime::is_type_of(value) {
            ObType::Time
        } else if PyDelta::is_type_of(value) {
            ObType::Timedelta
        } else if PyUrl::is_type_of(value) {
            ObType::Url
        } else if PyMultiHostUrl::is_type_of(value) {
            ObType::MultiHostUrl
        } else if value.is_instance(self.decimal_object.as_ref(py)).unwrap_or(false) {
            ObType::Decimal
        } else if value.is_instance(self.uuid_object.as_ref(py)).unwrap_or(false) {
            ObType::Uuid
        } else if value.is_instance(self.enum_object.as_ref(py)).unwrap_or(false) {
            ObType::Enum
        } else if value.is_instance(self.generator_object.as_ref(py)).unwrap_or(false) {
            ObType::Generator
        } else if value.is_instance(self.path_object.as_ref(py)).unwrap_or(false) {
            ObType::Path
        } else {
            ObType::Unknown
        }
    }
}

fn is_dataclass(op_value: Option<&PyAny>) -> bool {
    if let Some(value) = op_value {
        value
            .hasattr(intern!(value.py(), "__dataclass_fields__"))
            .unwrap_or(false)
            && !value.is_instance_of::<PyType>()
    } else {
        false
    }
}

fn is_pydantic_serializable(op_value: Option<&PyAny>) -> bool {
    if let Some(value) = op_value {
        value
            .hasattr(intern!(value.py(), "__pydantic_serializer__"))
            .unwrap_or(false)
            && !value.is_instance_of::<PyType>()
    } else {
        false
    }
}

fn is_generator(op_value: Option<&PyAny>) -> bool {
    if let Some(value) = op_value {
        value.downcast::<PyIterator>().is_ok()
    } else {
        false
    }
}

#[derive(Debug, Clone, Copy, EnumString, Display)]
#[strum(serialize_all = "snake_case")]
pub enum ObType {
    None,
    // numeric types
    Int,
    IntSubclass,
    Bool,
    Float,
    FloatSubclass,
    Decimal,
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
    // anything with __pydantic_serializer__, including BaseModel and pydantic dataclasses
    PydanticSerializable,
    // vanilla dataclasses
    Dataclass,
    // enum type
    Enum,
    // generator type
    Generator,
    // Path
    Path,
    // Uuid
    Uuid,
    // unknown type
    Unknown,
}

impl PartialEq for ObType {
    fn eq(&self, other: &Self) -> bool {
        if ((*self) as u8) == ((*other) as u8) {
            // everything is equal to itself except for Unknown, which is never equal to anything
            !matches!(self, Self::Unknown)
        } else {
            match (self, other) {
                // special cases for subclasses
                (Self::IntSubclass, Self::Int) => true,
                (Self::Int, Self::IntSubclass) => true,
                (Self::FloatSubclass, Self::Float) => true,
                (Self::Float, Self::FloatSubclass) => true,
                (Self::StrSubclass, Self::Str) => true,
                (Self::Str, Self::StrSubclass) => true,
                _ => false,
            }
        }
    }
}

fn get_base_type(py_type: &PyType) -> Option<&PyType> {
    let base_type_ptr = unsafe { (*py_type.as_type_ptr()).tp_base };
    // Safety: `base_type_ptr` must be a valid pointer to a Python type object, or null.
    unsafe { py_type.py().from_borrowed_ptr_or_opt(base_type_ptr.cast()) }
}
