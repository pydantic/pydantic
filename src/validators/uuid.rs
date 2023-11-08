use std::str::from_utf8;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::sync::GILOnceCell;
use pyo3::types::{PyDict, PyType};
use uuid::Uuid;

use crate::build_tools::is_strict;
use crate::errors::{ErrorType, ErrorTypeDefaults, ValError, ValResult};
use crate::input::Input;
use crate::tools::SchemaDict;

use super::model::create_class;
use super::model::force_setattr;
use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, Exactness, ValidationState, Validator};

const UUID_INT: &str = "int";
const UUID_IS_SAFE: &str = "is_safe";

static UUID_TYPE: GILOnceCell<Py<PyType>> = GILOnceCell::new();

fn import_type(py: Python, module: &str, attr: &str) -> PyResult<Py<PyType>> {
    py.import(module)?.getattr(attr)?.extract()
}

fn get_uuid_type(py: Python) -> PyResult<&PyType> {
    Ok(UUID_TYPE
        .get_or_init(py, || import_type(py, "uuid", "UUID").unwrap())
        .as_ref(py))
}

#[derive(Debug, Clone, Copy)]
enum Version {
    UUIDv1 = 1,
    UUIDv3 = 3,
    UUIDv4 = 4,
    UUIDv5 = 5,
}

impl From<Version> for usize {
    fn from(v: Version) -> Self {
        v as usize
    }
}

impl From<u8> for Version {
    fn from(u: u8) -> Self {
        match u {
            1 => Version::UUIDv1,
            3 => Version::UUIDv3,
            4 => Version::UUIDv4,
            5 => Version::UUIDv5,
            _ => unreachable!(),
        }
    }
}

#[derive(Debug, Clone)]
pub struct UuidValidator {
    strict: bool,
    version: Option<usize>,
}

impl BuildValidator for UuidValidator {
    const EXPECTED_TYPE: &'static str = "uuid";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        _definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        // Note(lig): let's keep this conversion through the Version enum just for the sake of validation
        let version = schema.get_as::<u8>(intern!(py, "version"))?.map(Version::from);
        Ok(Self {
            strict: is_strict(schema, config)?,
            version: version.map(usize::from),
        }
        .into())
    }
}

impl_py_gc_traverse!(UuidValidator {});

impl Validator for UuidValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<'data, PyObject> {
        let class = get_uuid_type(py)?;
        if let Some(py_input) = input.input_is_instance(class) {
            if let Some(expected_version) = self.version {
                let py_input_version: Option<usize> = py_input.getattr(intern!(py, "version"))?.extract()?;
                if !match py_input_version {
                    Some(py_input_version) => py_input_version == expected_version,
                    None => false,
                } {
                    return Err(ValError::new(
                        ErrorType::UuidVersion {
                            expected_version,
                            context: None,
                        },
                        input,
                    ));
                }
            }
            Ok(py_input.to_object(py))
        } else if state.strict_or(self.strict) && input.is_python() {
            Err(ValError::new(
                ErrorType::IsInstanceOf {
                    class: class.name().unwrap_or("UUID").to_string(),
                    context: None,
                },
                input,
            ))
        } else {
            // In python mode this is a coercion, in JSON mode we treat a UUID string as an
            // exact match
            if input.is_python() {
                state.floor_exactness(Exactness::Lax);
            }
            let uuid = self.get_uuid(input)?;
            self.create_py_uuid(py, class, &uuid)
        }
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}

impl UuidValidator {
    fn get_uuid<'s, 'data>(&'s self, input: &'data impl Input<'data>) -> ValResult<'data, Uuid> {
        let uuid = match input.exact_str().ok() {
            Some(either_string) => {
                let cow = either_string.as_cow()?;
                let uuid_str = cow.as_ref();
                Uuid::parse_str(uuid_str).map_err(|e| {
                    ValError::new(
                        ErrorType::UuidParsing {
                            error: e.to_string(),
                            context: None,
                        },
                        input,
                    )
                })?
            }
            None => {
                let either_bytes = input
                    .validate_bytes(true)
                    .map_err(|_| ValError::new(ErrorTypeDefaults::UuidType, input))?
                    .into_inner();
                let bytes_slice = either_bytes.as_slice();
                'parse: {
                    // Try parsing as utf8, but don't care if it fails
                    if let Ok(utf8_str) = from_utf8(bytes_slice) {
                        if let Ok(uuid) = Uuid::parse_str(utf8_str) {
                            break 'parse uuid;
                        }
                    }
                    Uuid::from_slice(bytes_slice).map_err(|e| {
                        ValError::new(
                            ErrorType::UuidParsing {
                                error: e.to_string(),
                                context: None,
                            },
                            input,
                        )
                    })?
                }
            }
        };

        if let Some(expected_version) = self.version {
            let v1 = uuid.get_version_num();
            if v1 != expected_version {
                return Err(ValError::new(
                    ErrorType::UuidVersion {
                        expected_version,
                        context: None,
                    },
                    input,
                ));
            }
        };
        Ok(uuid)
    }

    /// Sets the attributes in a Python type object (`py_type`) to represent a UUID class.
    /// The function creates the python class and converts the UUID to a u128 integer and
    /// sets the corresponding attributes in the dictionary object to the converted value
    /// and a 'safe' flag.
    ///
    /// This implementation does not use the Python `__init__` function to speed up the process,
    /// as the `__init__` function in the Python `uuid` module performs extensive checks.
    fn create_py_uuid<'py>(&self, py: Python<'py>, py_type: &PyType, uuid: &Uuid) -> ValResult<'py, Py<PyAny>> {
        let class = create_class(py_type)?;
        let dc = class.as_ref(py);
        let int = uuid.as_u128();
        let safe = py
            .import(intern!(py, "uuid"))?
            .getattr(intern!(py, "SafeUUID"))?
            .get_item("safe")?;
        force_setattr(py, dc, intern!(py, UUID_INT), int)?;
        force_setattr(py, dc, intern!(py, UUID_IS_SAFE), safe)?;
        Ok(dc.to_object(py))
    }
}
