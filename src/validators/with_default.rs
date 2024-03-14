use pyo3::intern;
use pyo3::prelude::*;
use pyo3::sync::GILOnceCell;
use pyo3::types::PyDict;
use pyo3::types::PyString;
use pyo3::PyTraverseError;
use pyo3::PyVisit;

use super::{build_validator, BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator};
use crate::build_tools::py_schema_err;
use crate::build_tools::schema_or_config_same;
use crate::errors::{LocItem, ValError, ValResult};
use crate::input::Input;
use crate::py_gc::PyGcTraverse;
use crate::tools::SchemaDict;
use crate::PydanticUndefinedType;

static COPY_DEEPCOPY: GILOnceCell<PyObject> = GILOnceCell::new();

fn get_deepcopy(py: Python) -> PyResult<PyObject> {
    Ok(py.import_bound("copy")?.getattr("deepcopy")?.into_py(py))
}

#[derive(Debug, Clone)]
pub enum DefaultType {
    None,
    Default(PyObject),
    DefaultFactory(PyObject),
}

impl DefaultType {
    pub fn new(schema: &Bound<'_, PyDict>) -> PyResult<Self> {
        let py = schema.py();
        match (
            schema.get_as(intern!(py, "default"))?,
            schema.get_as(intern!(py, "default_factory"))?,
        ) {
            (Some(_), Some(_)) => py_schema_err!("'default' and 'default_factory' cannot be used together"),
            (Some(default), None) => Ok(Self::Default(default)),
            (None, Some(default_factory)) => Ok(Self::DefaultFactory(default_factory)),
            (None, None) => Ok(Self::None),
        }
    }

    pub fn default_value(&self, py: Python) -> PyResult<Option<PyObject>> {
        match self {
            Self::Default(ref default) => Ok(Some(default.clone_ref(py))),
            Self::DefaultFactory(ref default_factory) => Ok(Some(default_factory.call0(py)?)),
            Self::None => Ok(None),
        }
    }
}

impl PyGcTraverse for DefaultType {
    fn py_gc_traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        if let Self::Default(obj) | Self::DefaultFactory(obj) = self {
            visit.call(obj)?;
        }
        Ok(())
    }
}

#[derive(Debug, Clone)]
enum OnError {
    Raise,
    Omit,
    Default,
}

#[derive(Debug)]
pub struct WithDefaultValidator {
    default: DefaultType,
    on_error: OnError,
    validator: Box<CombinedValidator>,
    validate_default: bool,
    copy_default: bool,
    name: String,
    undefined: PyObject,
}

impl BuildValidator for WithDefaultValidator {
    const EXPECTED_TYPE: &'static str = "default";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let default = DefaultType::new(schema)?;
        let on_error = match schema
            .get_as::<Bound<'_, PyString>>(intern!(py, "on_error"))?
            .as_ref()
            .map(|s| s.to_str())
            .transpose()?
        {
            Some("raise") => OnError::Raise,
            Some("omit") => OnError::Omit,
            Some("default") => {
                if matches!(default, DefaultType::None) {
                    return py_schema_err!("'on_error = default' requires a `default` or `default_factory`");
                }
                OnError::Default
            }
            None => OnError::Raise,
            // schema validation means other values are impossible
            _ => unreachable!(),
        };

        let sub_schema = schema.get_as_req(intern!(schema.py(), "schema"))?;
        let validator = Box::new(build_validator(&sub_schema, config, definitions)?);

        let copy_default = if let DefaultType::Default(default_obj) = &default {
            default_obj.bind(py).hash().is_err()
        } else {
            false
        };

        let name = format!("{}[{}]", Self::EXPECTED_TYPE, validator.get_name());

        Ok(Self {
            default,
            on_error,
            validator,
            validate_default: schema_or_config_same(schema, config, intern!(py, "validate_default"))?.unwrap_or(false),
            copy_default,
            name,
            undefined: PydanticUndefinedType::new(py).to_object(py),
        }
        .into())
    }
}

impl_py_gc_traverse!(WithDefaultValidator { default, validator });

impl Validator for WithDefaultValidator {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &impl Input<'py>,
        state: &mut ValidationState,
    ) -> ValResult<PyObject> {
        if input.to_object(py).is(&self.undefined) {
            Ok(self.default_value(py, None::<usize>, state)?.unwrap())
        } else {
            match self.validator.validate(py, input, state) {
                Ok(v) => Ok(v),
                Err(e) => match e {
                    ValError::UseDefault => Ok(self.default_value(py, None::<usize>, state)?.ok_or(e)?),
                    e => match self.on_error {
                        OnError::Raise => Err(e),
                        OnError::Default => Ok(self.default_value(py, None::<usize>, state)?.ok_or(e)?),
                        OnError::Omit => Err(ValError::Omit),
                    },
                },
            }
        }
    }

    fn default_value(
        &self,
        py: Python<'_>,
        outer_loc: Option<impl Into<LocItem>>,
        state: &mut ValidationState,
    ) -> ValResult<Option<PyObject>> {
        match self.default.default_value(py)? {
            Some(stored_dft) => {
                let dft: Py<PyAny> = if self.copy_default {
                    let deepcopy_func = COPY_DEEPCOPY.get_or_init(py, || get_deepcopy(py).unwrap());
                    deepcopy_func.call1(py, (&stored_dft,))?.into_py(py)
                } else {
                    stored_dft
                };
                if self.validate_default {
                    match self.validate(py, dft.bind(py), state) {
                        Ok(v) => Ok(Some(v)),
                        Err(e) => {
                            if let Some(outer_loc) = outer_loc {
                                Err(e.with_outer_location(outer_loc))
                            } else {
                                Err(e)
                            }
                        }
                    }
                } else {
                    Ok(Some(dft))
                }
            }
            None => Ok(None),
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}

impl WithDefaultValidator {
    pub fn has_default(&self) -> bool {
        !matches!(self.default, DefaultType::None)
    }

    pub fn omit_on_error(&self) -> bool {
        matches!(self.on_error, OnError::Omit)
    }
}
