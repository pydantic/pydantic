use pyo3::intern;
use pyo3::once_cell::GILOnceCell;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use super::{build_validator, BuildValidator, CombinedValidator, Definitions, DefinitionsBuilder, Extra, Validator};
use crate::build_tools::py_schema_err;
use crate::build_tools::schema_or_config_same;
use crate::errors::{LocItem, ValError, ValResult};
use crate::input::Input;
use crate::recursion_guard::RecursionGuard;
use crate::tools::SchemaDict;
use crate::PydanticUndefinedType;

static COPY_DEEPCOPY: GILOnceCell<PyObject> = GILOnceCell::new();

fn get_deepcopy(py: Python) -> PyResult<PyObject> {
    Ok(py.import("copy")?.getattr("deepcopy")?.into_py(py))
}

#[derive(Debug, Clone)]
pub enum DefaultType {
    None,
    Default(PyObject),
    DefaultFactory(PyObject),
}

impl DefaultType {
    pub fn new(schema: &PyDict) -> PyResult<Self> {
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

#[derive(Debug, Clone)]
enum OnError {
    Raise,
    Omit,
    Default,
}

#[derive(Debug, Clone)]
pub struct WithDefaultValidator {
    default: DefaultType,
    on_error: OnError,
    validator: Box<CombinedValidator>,
    validate_default: bool,
    copy_default: bool,
    name: String,
}

impl BuildValidator for WithDefaultValidator {
    const EXPECTED_TYPE: &'static str = "default";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let default = DefaultType::new(schema)?;
        let on_error = match schema.get_as::<&str>(intern!(py, "on_error"))? {
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

        let sub_schema: &PyAny = schema.get_as_req(intern!(schema.py(), "schema"))?;
        let validator = Box::new(build_validator(sub_schema, config, definitions)?);

        let copy_default = if let DefaultType::Default(default_obj) = &default {
            default_obj.as_ref(py).hash().is_err()
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
        }
        .into())
    }
}

impl Validator for WithDefaultValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        definitions: &'data Definitions<CombinedValidator>,
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        if input.to_object(py).is(&PydanticUndefinedType::py_undefined()) {
            Ok(self
                .default_value(py, None::<usize>, extra, definitions, recursion_guard)?
                .unwrap())
        } else {
            match self.validator.validate(py, input, extra, definitions, recursion_guard) {
                Ok(v) => Ok(v),
                Err(e) => match e {
                    ValError::UseDefault => Ok(self
                        .default_value(py, None::<usize>, extra, definitions, recursion_guard)?
                        .ok_or(e)?),
                    e => match self.on_error {
                        OnError::Raise => Err(e),
                        OnError::Default => Ok(self
                            .default_value(py, None::<usize>, extra, definitions, recursion_guard)?
                            .ok_or(e)?),
                        OnError::Omit => Err(ValError::Omit),
                    },
                },
            }
        }
    }

    fn default_value<'s, 'data>(
        &'s self,
        py: Python<'data>,
        outer_loc: Option<impl Into<LocItem>>,
        extra: &Extra,
        definitions: &'data Definitions<CombinedValidator>,
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, Option<PyObject>> {
        match self.default.default_value(py)? {
            Some(stored_dft) => {
                let dft: Py<PyAny> = if self.copy_default {
                    let deepcopy_func = COPY_DEEPCOPY.get_or_init(py, || get_deepcopy(py).unwrap());
                    deepcopy_func.call1(py, (&stored_dft,))?.into_py(py)
                } else {
                    stored_dft
                };
                if self.validate_default {
                    match self.validate(py, dft.into_ref(py), extra, definitions, recursion_guard) {
                        Ok(v) => Ok(Some(v)),
                        Err(e) => {
                            if let Some(outer_loc) = outer_loc {
                                Err(e.with_outer_location(outer_loc.into()))
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

    fn different_strict_behavior(
        &self,
        definitions: Option<&DefinitionsBuilder<CombinedValidator>>,
        ultra_strict: bool,
    ) -> bool {
        self.validator.different_strict_behavior(definitions, ultra_strict)
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, definitions: &DefinitionsBuilder<CombinedValidator>) -> PyResult<()> {
        self.validator.complete(definitions)
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
