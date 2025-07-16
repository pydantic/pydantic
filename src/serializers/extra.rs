use std::convert::Infallible;
use std::ffi::CString;
use std::fmt;
use std::sync::Mutex;

use pyo3::exceptions::{PyTypeError, PyUserWarning, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyBool, PyString};
use pyo3::{intern, PyTypeInfo};

use serde::ser::Error;

use super::config::SerializationConfig;
use super::errors::{PydanticSerializationUnexpectedValue, UNEXPECTED_TYPE_SER_MARKER};
use super::ob_type::ObTypeLookup;
use crate::recursion_guard::ContainsRecursionState;
use crate::recursion_guard::RecursionError;
use crate::recursion_guard::RecursionGuard;
use crate::recursion_guard::RecursionState;
use crate::PydanticSerializationError;

/// this is ugly, would be much better if extra could be stored in `SerializationState`
/// then `SerializationState` got a `serialize_infer` method, but I couldn't get it to work
pub(crate) struct SerializationState {
    warnings: CollectWarnings,
    rec_guard: SerRecursionState,
    config: SerializationConfig,
}

impl SerializationState {
    pub fn new(timedelta_mode: &str, temporal_mode: &str, bytes_mode: &str, inf_nan_mode: &str) -> PyResult<Self> {
        let warnings = CollectWarnings::new(WarningsMode::None);
        let rec_guard = SerRecursionState::default();
        let config = SerializationConfig::from_args(timedelta_mode, temporal_mode, bytes_mode, inf_nan_mode)?;
        Ok(Self {
            warnings,
            rec_guard,
            config,
        })
    }

    #[allow(clippy::too_many_arguments)]
    pub fn extra<'py>(
        &'py self,
        py: Python<'py>,
        mode: &'py SerMode,
        by_alias: Option<bool>,
        exclude_none: bool,
        round_trip: bool,
        serialize_unknown: bool,
        fallback: Option<&'py Bound<'_, PyAny>>,
        serialize_as_any: bool,
        context: Option<&'py Bound<'_, PyAny>>,
    ) -> Extra<'py> {
        Extra::new(
            py,
            mode,
            by_alias,
            &self.warnings,
            false,
            false,
            exclude_none,
            round_trip,
            &self.config,
            &self.rec_guard,
            serialize_unknown,
            fallback,
            serialize_as_any,
            context,
        )
    }

    pub fn final_check(&self, py: Python) -> PyResult<()> {
        self.warnings.final_check(py)
    }
}

/// Useful things which are passed around by type_serializers
#[derive(Clone)]
#[cfg_attr(debug_assertions, derive(Debug))]
pub(crate) struct Extra<'a> {
    pub mode: &'a SerMode,
    pub ob_type_lookup: &'a ObTypeLookup,
    pub warnings: &'a CollectWarnings,
    pub by_alias: Option<bool>,
    pub exclude_unset: bool,
    pub exclude_defaults: bool,
    pub exclude_none: bool,
    pub round_trip: bool,
    pub config: &'a SerializationConfig,
    pub rec_guard: &'a SerRecursionState,
    // the next two are used for union logic
    pub check: SerCheck,
    // data representing the current model field
    // that is being serialized, if this is a model serializer
    // it will be None otherwise
    pub model: Option<&'a Bound<'a, PyAny>>,
    pub field_name: Option<&'a str>,
    pub serialize_unknown: bool,
    pub fallback: Option<&'a Bound<'a, PyAny>>,
    pub serialize_as_any: bool,
    pub context: Option<&'a Bound<'a, PyAny>>,
}

impl<'a> Extra<'a> {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        py: Python<'a>,
        mode: &'a SerMode,
        by_alias: Option<bool>,
        warnings: &'a CollectWarnings,
        exclude_unset: bool,
        exclude_defaults: bool,
        exclude_none: bool,
        round_trip: bool,
        config: &'a SerializationConfig,
        rec_guard: &'a SerRecursionState,
        serialize_unknown: bool,
        fallback: Option<&'a Bound<'a, PyAny>>,
        serialize_as_any: bool,
        context: Option<&'a Bound<'a, PyAny>>,
    ) -> Self {
        Self {
            mode,
            ob_type_lookup: ObTypeLookup::cached(py),
            warnings,
            by_alias,
            exclude_unset,
            exclude_defaults,
            exclude_none,
            round_trip,
            config,
            rec_guard,
            check: SerCheck::None,
            model: None,
            field_name: None,
            serialize_unknown,
            fallback,
            serialize_as_any,
            context,
        }
    }

    pub fn recursion_guard<'x, 'y>(
        // TODO: this double reference is a bit if a hack, but it's necessary because the recursion
        // guard is not passed around with &mut reference
        //
        // See how validation has &mut ValidationState passed around; we should aim to refactor
        // to match that.
        self: &'x mut &'y Self,
        value: &Bound<'_, PyAny>,
        def_ref_id: usize,
    ) -> PyResult<RecursionGuard<'x, &'y Self>> {
        RecursionGuard::new(self, value.as_ptr() as usize, def_ref_id).map_err(|e| match e {
            RecursionError::Depth => PyValueError::new_err("Circular reference detected (depth exceeded)"),
            RecursionError::Cyclic => PyValueError::new_err("Circular reference detected (id repeated)"),
        })
    }

    pub fn serialize_infer<'py>(&'py self, value: &'py Bound<'py, PyAny>) -> super::infer::SerializeInfer<'py> {
        super::infer::SerializeInfer::new(value, None, None, self)
    }

    pub(crate) fn model_type_name(&self) -> Option<Bound<'a, PyString>> {
        self.model.and_then(|model| model.get_type().name().ok())
    }

    pub fn serialize_by_alias_or(&self, serialize_by_alias: Option<bool>) -> bool {
        self.by_alias.or(serialize_by_alias).unwrap_or(false)
    }
}

#[derive(Clone, Copy, PartialEq, Eq)]
#[cfg_attr(debug_assertions, derive(Debug))]
pub(crate) enum SerCheck {
    // no checks, used everywhere except in union choices
    None,
    // strict means subclasses are not allowed
    Strict,
    // check but allow subclasses
    Lax,
}

impl SerCheck {
    pub fn enabled(self) -> bool {
        self != SerCheck::None
    }
}

#[derive(Clone)]
#[cfg_attr(debug_assertions, derive(Debug))]
pub(crate) struct ExtraOwned {
    mode: SerMode,
    warnings: CollectWarnings,
    by_alias: Option<bool>,
    exclude_unset: bool,
    exclude_defaults: bool,
    exclude_none: bool,
    round_trip: bool,
    config: SerializationConfig,
    rec_guard: SerRecursionState,
    check: SerCheck,
    pub model: Option<PyObject>,
    field_name: Option<String>,
    serialize_unknown: bool,
    pub fallback: Option<PyObject>,
    serialize_as_any: bool,
    pub context: Option<PyObject>,
}

impl ExtraOwned {
    pub fn new(extra: &Extra) -> Self {
        Self {
            mode: extra.mode.clone(),
            warnings: extra.warnings.clone(),
            by_alias: extra.by_alias,
            exclude_unset: extra.exclude_unset,
            exclude_defaults: extra.exclude_defaults,
            exclude_none: extra.exclude_none,
            round_trip: extra.round_trip,
            config: extra.config.clone(),
            rec_guard: extra.rec_guard.clone(),
            check: extra.check,
            model: extra.model.map(|model| model.clone().into()),
            field_name: extra.field_name.map(ToString::to_string),
            serialize_unknown: extra.serialize_unknown,
            fallback: extra.fallback.map(|model| model.clone().into()),
            serialize_as_any: extra.serialize_as_any,
            context: extra.context.map(|model| model.clone().into()),
        }
    }

    pub fn to_extra<'py>(&'py self, py: Python<'py>) -> Extra<'py> {
        Extra {
            mode: &self.mode,
            ob_type_lookup: ObTypeLookup::cached(py),
            warnings: &self.warnings,
            by_alias: self.by_alias,
            exclude_unset: self.exclude_unset,
            exclude_defaults: self.exclude_defaults,
            exclude_none: self.exclude_none,
            round_trip: self.round_trip,
            config: &self.config,
            rec_guard: &self.rec_guard,
            check: self.check,
            model: self.model.as_ref().map(|m| m.bind(py)),
            field_name: self.field_name.as_deref(),
            serialize_unknown: self.serialize_unknown,
            fallback: self.fallback.as_ref().map(|m| m.bind(py)),
            serialize_as_any: self.serialize_as_any,
            context: self.context.as_ref().map(|m| m.bind(py)),
        }
    }
}

#[derive(Clone)]
#[cfg_attr(debug_assertions, derive(Debug))]
pub(crate) enum SerMode {
    Python,
    Json,
    Other(String),
}

impl fmt::Display for SerMode {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            SerMode::Python => write!(f, "python"),
            SerMode::Json => write!(f, "json"),
            SerMode::Other(s) => write!(f, "{s}"),
        }
    }
}

impl SerMode {
    pub fn is_json(&self) -> bool {
        matches!(self, SerMode::Json)
    }
}

impl From<Option<&str>> for SerMode {
    fn from(s: Option<&str>) -> Self {
        match s {
            Some("json") => SerMode::Json,
            Some("python") => SerMode::Python,
            Some(other) => SerMode::Other(other.to_string()),
            None => SerMode::Python,
        }
    }
}

impl<'py> IntoPyObject<'py> for &'_ SerMode {
    type Target = PyString;
    type Output = Bound<'py, PyString>;
    type Error = Infallible;

    fn into_pyobject(self, py: Python<'py>) -> Result<Self::Output, Self::Error> {
        match self {
            SerMode::Python => Ok(intern!(py, "python").clone()),
            SerMode::Json => Ok(intern!(py, "json").clone()),
            SerMode::Other(s) => Ok(PyString::new(py, s)),
        }
    }
}

#[derive(Debug, Clone, Copy, Eq, PartialEq)]
pub enum WarningsMode {
    None,
    Warn,
    Error,
}

impl<'py> FromPyObject<'py> for WarningsMode {
    fn extract_bound(ob: &Bound<'py, PyAny>) -> PyResult<WarningsMode> {
        if let Ok(bool_mode) = ob.downcast::<PyBool>() {
            Ok(bool_mode.is_true().into())
        } else if let Ok(str_mode) = ob.extract::<&str>() {
            match str_mode {
                "none" => Ok(Self::None),
                "warn" => Ok(Self::Warn),
                "error" => Ok(Self::Error),
                _ => Err(PyValueError::new_err(
                    "Invalid warnings parameter, should be `'none'`, `'warn'`, `'error'` or a `bool`",
                )),
            }
        } else {
            Err(PyTypeError::new_err(
                "Invalid warnings parameter, should be `'none'`, `'warn'`, `'error'` or a `bool`",
            ))
        }
    }
}

impl From<bool> for WarningsMode {
    fn from(mode: bool) -> Self {
        if mode {
            Self::Warn
        } else {
            Self::None
        }
    }
}

#[cfg_attr(debug_assertions, derive(Debug))]
pub(crate) struct CollectWarnings {
    mode: WarningsMode,
    // FIXME: mutex is to satisfy PyO3 0.23, we should be able to refactor this away
    warnings: Mutex<Vec<PydanticSerializationUnexpectedValue>>,
}

impl Clone for CollectWarnings {
    fn clone(&self) -> Self {
        Self {
            mode: self.mode,
            warnings: Mutex::new(self.warnings.lock().expect("lock poisoned").clone()),
        }
    }
}

impl CollectWarnings {
    pub(crate) fn new(mode: WarningsMode) -> Self {
        Self {
            mode,
            warnings: Mutex::new(Vec::new()),
        }
    }

    pub fn register_warning(&self, warning: PydanticSerializationUnexpectedValue) {
        if self.mode != WarningsMode::None {
            self.warnings.lock().expect("lock poisoned").push(warning);
        }
    }

    pub fn on_fallback_py(&self, field_type: &str, value: &Bound<'_, PyAny>, extra: &Extra) -> PyResult<()> {
        // special case for None as it's very common e.g. as a default value
        if value.is_none() {
            Ok(())
        } else if extra.check.enabled() {
            Err(PydanticSerializationUnexpectedValue::new_from_parts(
                Some(field_type.to_string()),
                Some(value.clone().unbind()),
            )
            .to_py_err())
        } else {
            self.fallback_warning(field_type, value);
            Ok(())
        }
    }

    pub fn on_fallback_ser<S: serde::ser::Serializer>(
        &self,
        field_type: &str,
        value: &Bound<'_, PyAny>,
        extra: &Extra,
    ) -> Result<(), S::Error> {
        // special case for None as it's very common e.g. as a default value
        if value.is_none() {
            Ok(())
        } else if extra.check.enabled() {
            // note: I think this should never actually happen since we use `to_python(..., mode='json')` during
            // JSON serialisation to "try" union branches, but it's here for completeness/correctness
            // in particular, in future we could allow errors instead of warnings on fallback
            Err(S::Error::custom(UNEXPECTED_TYPE_SER_MARKER))
        } else {
            self.fallback_warning(field_type, value);
            Ok(())
        }
    }

    fn fallback_warning(&self, field_type: &str, value: &Bound<'_, PyAny>) {
        if self.mode != WarningsMode::None {
            self.register_warning(PydanticSerializationUnexpectedValue::new_from_parts(
                Some(field_type.to_string()),
                Some(value.clone().unbind()),
            ));
        }
    }

    pub fn final_check(&self, py: Python) -> PyResult<()> {
        if self.mode == WarningsMode::None {
            return Ok(());
        }
        let warnings = self.warnings.lock().expect("lock poisoned");

        if warnings.is_empty() {
            return Ok(());
        }

        let formatted_warnings: Vec<String> = warnings.iter().map(|w| w.__repr__(py).to_string()).collect();

        let message = format!("Pydantic serializer warnings:\n  {}", formatted_warnings.join("\n  "));
        if self.mode == WarningsMode::Warn {
            let user_warning_type = PyUserWarning::type_object(py);
            PyErr::warn(py, &user_warning_type, &CString::new(message)?, 0)
        } else {
            Err(PydanticSerializationError::new_err(message))
        }
    }
}

#[derive(Default)]
#[cfg_attr(debug_assertions, derive(Debug))]
pub struct SerRecursionState {
    // FIXME: mutex is to satisfy PyO3 0.23, we should be able to refactor this away
    guard: Mutex<RecursionState>,
}

impl Clone for SerRecursionState {
    fn clone(&self) -> Self {
        Self {
            guard: Mutex::new(self.guard.lock().expect("lock poisoned").clone()),
        }
    }
}

impl ContainsRecursionState for &'_ Extra<'_> {
    fn access_recursion_state<R>(&mut self, f: impl FnOnce(&mut RecursionState) -> R) -> R {
        f(&mut self.rec_guard.guard.lock().expect("lock poisoned"))
    }
}
