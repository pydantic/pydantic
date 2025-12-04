use std::convert::Infallible;
use std::ffi::CString;
use std::fmt;
use std::ops::{Deref, DerefMut};
use std::string::ToString;

use pyo3::exceptions::{PyTypeError, PyUserWarning, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyBool, PyString};
use pyo3::{PyTypeInfo, intern};

use serde::ser::Error;

use super::config::SerializationConfig;
use super::errors::{PydanticSerializationUnexpectedValue, UNEXPECTED_TYPE_SER_MARKER};
use super::ob_type::ObTypeLookup;
use crate::PydanticSerializationError;
use crate::recursion_guard::ContainsRecursionState;
use crate::recursion_guard::RecursionError;
use crate::recursion_guard::RecursionGuard;
use crate::recursion_guard::RecursionState;

/// this is ugly, would be much better if extra could be stored in `SerializationState`
/// then `SerializationState` got a `serialize_infer` method, but I couldn't get it to work
pub(crate) struct SerializationState<'py> {
    pub warnings: CollectWarnings,
    pub rec_guard: RecursionState,
    pub config: SerializationConfig,
    /// The model currently being serialized, if any
    pub model: Option<Bound<'py, PyAny>>,
    /// The name of the field currently being serialized, if any
    pub field_name: Option<FieldName<'py>>,
    /// Inside unions, checks are applied to attempt to select a preferred branch
    pub check: SerCheck,
    pub include_exclude: (Option<Bound<'py, PyAny>>, Option<Bound<'py, PyAny>>),
    /// Global settings for the serialization process
    pub extra: Extra<'py>,
}

#[derive(Clone)]
pub enum FieldName<'py> {
    Root,
    Regular(Bound<'py, PyString>),
}

impl<'py> From<Bound<'py, PyString>> for FieldName<'py> {
    fn from(s: Bound<'py, PyString>) -> Self {
        FieldName::Regular(s)
    }
}

impl fmt::Display for FieldName<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            FieldName::Root => write!(f, "root"),
            FieldName::Regular(s) => write!(f, "{s}"),
        }
    }
}

impl<'py> SerializationState<'py> {
    pub fn new(
        config: SerializationConfig,
        warnings_mode: WarningsMode,
        include: Option<Bound<'py, PyAny>>,
        exclude: Option<Bound<'py, PyAny>>,
        extra: Extra<'py>,
    ) -> PyResult<Self> {
        let warnings = CollectWarnings::new(warnings_mode);
        let rec_guard = RecursionState::default();
        Ok(Self {
            warnings,
            rec_guard,
            config,
            model: None,
            field_name: None,
            check: SerCheck::None,
            include_exclude: (include, exclude),
            extra,
        })
    }
}

impl SerializationState<'_> {
    pub fn recursion_guard(
        &mut self,
        value: &Bound<'_, PyAny>,
        def_ref_id: usize,
    ) -> PyResult<RecursionGuard<'_, Self>> {
        RecursionGuard::new(self, value.as_ptr() as usize, def_ref_id).map_err(|e| match e {
            RecursionError::Depth => PyValueError::new_err("Circular reference detected (depth exceeded)"),
            RecursionError::Cyclic => PyValueError::new_err("Circular reference detected (id repeated)"),
        })
    }

    pub fn warn_fallback_py(&mut self, field_type: &str, value: &Bound<'_, PyAny>) -> PyResult<()> {
        self.warnings
            .on_fallback_py(field_type, value, self.field_name.as_ref(), self.check)
    }

    pub fn warn_fallback_ser<S: serde::ser::Serializer>(
        &mut self,
        field_type: &str,
        value: &Bound<'_, PyAny>,
    ) -> Result<(), S::Error> {
        self.warnings
            .on_fallback_ser::<S>(field_type, value, self.field_name.as_ref(), self.check)
    }

    pub fn final_check(&self, py: Python) -> PyResult<()> {
        self.warnings.final_check(py)
    }
}

impl<'py> SerializationState<'py> {
    /// Temporarily rebinds a field of the state by calling `projector` to get a mutable reference to the field,
    /// and setting that field to `value`.
    ///
    /// When `ScopedSetState` drops, the field is restored to its original value.
    pub fn scoped_set<'state, P, T>(&'state mut self, projector: P, new_value: T) -> ScopedSetState<'state, 'py, P, T>
    where
        P: for<'p> Fn(&'p mut Self) -> &'p mut T,
    {
        let value = std::mem::replace((projector)(self), new_value);
        ScopedSetState {
            state: self,
            projector,
            value,
        }
    }

    pub fn scoped_include_exclude<'scope>(
        &'scope mut self,
        next_include: Option<Bound<'py, PyAny>>,
        next_exclude: Option<Bound<'py, PyAny>>,
    ) -> ScopedIncludeExcludeState<'scope, 'py> {
        self.scoped_set(SerializationState::include_exclude_mut, (next_include, next_exclude))
    }

    pub fn include(&self) -> Option<&Bound<'py, PyAny>> {
        self.include_exclude.0.as_ref()
    }

    pub fn exclude(&self) -> Option<&Bound<'py, PyAny>> {
        self.include_exclude.1.as_ref()
    }

    pub fn serialize_infer<'slf>(
        &'slf mut self,
        value: &'slf Bound<'py, PyAny>,
    ) -> super::infer::SerializeInfer<'slf, 'py> {
        super::infer::SerializeInfer::new(value, self)
    }

    fn include_exclude_mut(&mut self) -> &mut (Option<Bound<'py, PyAny>>, Option<Bound<'py, PyAny>>) {
        &mut self.include_exclude
    }
}

/// Constants for a serialization process
#[derive(Clone)]
#[cfg_attr(debug_assertions, derive(Debug))]
pub(crate) struct Extra<'py> {
    pub mode: SerMode,
    pub ob_type_lookup: &'static ObTypeLookup,
    pub by_alias: Option<bool>,
    pub exclude_unset: bool,
    pub exclude_defaults: bool,
    pub exclude_none: bool,
    pub exclude_computed_fields: bool,
    pub round_trip: bool,
    pub serialize_unknown: bool,
    pub fallback: Option<Bound<'py, PyAny>>,
    pub serialize_as_any: bool,
    /// Whether `polymorphic_serialization` is globally enabled / disabled for this serialization process
    pub polymorphic_serialization: Option<bool>,
    pub context: Option<Bound<'py, PyAny>>,
}

impl<'py> Extra<'py> {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        py: Python<'py>,
        mode: SerMode,
        by_alias: Option<bool>,
        exclude_unset: bool,
        exclude_defaults: bool,
        exclude_none: bool,
        exclude_computed_fields: bool,
        round_trip: bool,
        serialize_unknown: bool,
        fallback: Option<Bound<'py, PyAny>>,
        serialize_as_any: bool,
        polymorphic_serialization: Option<bool>,
        context: Option<Bound<'py, PyAny>>,
    ) -> Self {
        Self {
            mode,
            ob_type_lookup: ObTypeLookup::cached(py),
            by_alias,
            exclude_unset,
            exclude_defaults,
            exclude_none,
            exclude_computed_fields,
            round_trip,
            serialize_unknown,
            fallback,
            serialize_as_any,
            polymorphic_serialization,
            context,
        }
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
    exclude_computed_fields: bool,
    round_trip: bool,
    config: SerializationConfig,
    rec_guard: RecursionState,
    check: SerCheck,
    pub model: Option<Py<PyAny>>,
    field_name: Option<FieldNameOwned>,
    serialize_unknown: bool,
    pub fallback: Option<Py<PyAny>>,
    serialize_as_any: bool,
    polymorphic_serialization: Option<bool>,
    pub context: Option<Py<PyAny>>,
    include: Option<Py<PyAny>>,
    exclude: Option<Py<PyAny>>,
}

impl_py_gc_traverse!(ExtraOwned {
    model,
    fallback,
    context,
    include,
    exclude,
});

#[derive(Clone)]
enum FieldNameOwned {
    Root,
    Regular(Py<PyString>),
}

impl fmt::Debug for FieldNameOwned {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            FieldNameOwned::Root => write!(f, "root"),
            FieldNameOwned::Regular(s) => write!(f, "\"{s}\""),
        }
    }
}

impl ExtraOwned {
    pub fn new(state: &SerializationState<'_>) -> Self {
        let extra = &state.extra;
        Self {
            mode: extra.mode.clone(),
            warnings: state.warnings.clone(),
            by_alias: extra.by_alias,
            exclude_unset: extra.exclude_unset,
            exclude_defaults: extra.exclude_defaults,
            exclude_none: extra.exclude_none,
            exclude_computed_fields: extra.exclude_computed_fields,
            round_trip: extra.round_trip,
            config: state.config,
            rec_guard: state.rec_guard.clone(),
            check: state.check,
            model: state.model.as_ref().map(|model| model.clone().into()),
            field_name: state.field_name.as_ref().map(|name| match name {
                FieldName::Root => FieldNameOwned::Root,
                FieldName::Regular(b) => FieldNameOwned::Regular(b.clone().into()),
            }),
            serialize_unknown: extra.serialize_unknown,
            fallback: extra.fallback.clone().map(Bound::unbind),
            serialize_as_any: extra.serialize_as_any,
            context: extra.context.clone().map(Bound::unbind),
            polymorphic_serialization: extra.polymorphic_serialization,
            include: state.include().map(|m| m.clone().into()),
            exclude: state.exclude().map(|m| m.clone().into()),
        }
    }

    pub fn to_extra<'py>(&self, py: Python<'py>) -> Extra<'py> {
        Extra {
            mode: self.mode.clone(),
            ob_type_lookup: ObTypeLookup::cached(py),
            by_alias: self.by_alias,
            exclude_unset: self.exclude_unset,
            exclude_defaults: self.exclude_defaults,
            exclude_none: self.exclude_none,
            exclude_computed_fields: self.exclude_computed_fields,
            round_trip: self.round_trip,
            serialize_unknown: self.serialize_unknown,
            fallback: self.fallback.as_ref().map(|m| m.bind(py).clone()),
            serialize_as_any: self.serialize_as_any,
            context: self.context.as_ref().map(|m| m.bind(py).clone()),
            polymorphic_serialization: self.polymorphic_serialization,
        }
    }

    pub fn to_state<'py>(&self, py: Python<'py>) -> SerializationState<'py> {
        let extra = self.to_extra(py);
        SerializationState {
            warnings: self.warnings.clone(),
            rec_guard: self.rec_guard.clone(),
            config: self.config,
            model: self.model.as_ref().map(|m| m.bind(py).clone()),
            field_name: match &self.field_name {
                Some(FieldNameOwned::Root) => Some(FieldName::Root),
                Some(FieldNameOwned::Regular(b)) => Some(FieldName::Regular(b.bind(py).clone())),
                None => None,
            },
            check: self.check,
            include_exclude: (
                self.include.as_ref().map(|m| m.bind(py).clone()),
                self.exclude.as_ref().map(|m| m.bind(py).clone()),
            ),
            extra,
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
            Some("python") | None => SerMode::Python,
            Some(other) => SerMode::Other(other.to_string()),
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

impl FromPyObject<'_, '_> for WarningsMode {
    type Error = PyErr;
    fn extract(ob: Borrowed<'_, '_, PyAny>) -> PyResult<WarningsMode> {
        if let Ok(bool_mode) = ob.cast::<PyBool>() {
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
        if mode { Self::Warn } else { Self::None }
    }
}

#[cfg_attr(debug_assertions, derive(Debug))]
#[derive(Clone)]
pub(crate) struct CollectWarnings {
    mode: WarningsMode,
    warnings: Vec<PydanticSerializationUnexpectedValue>,
}

impl CollectWarnings {
    pub(crate) fn new(mode: WarningsMode) -> Self {
        Self {
            mode,
            warnings: Vec::new(),
        }
    }

    pub fn register_warning(&mut self, warning: PydanticSerializationUnexpectedValue) {
        if self.mode != WarningsMode::None {
            self.warnings.push(warning);
        }
    }

    fn on_fallback_py(
        &mut self,
        field_type: &str,
        value: &Bound<'_, PyAny>,
        field_name: Option<&FieldName<'_>>,
        check: SerCheck,
    ) -> PyResult<()> {
        // special case for None as it's very common e.g. as a default value
        if value.is_none() {
            Ok(())
        } else if check.enabled() {
            Err(PydanticSerializationUnexpectedValue::new_from_parts(
                field_name.map(ToString::to_string),
                Some(field_type.to_string()),
                Some(value.clone().unbind()),
            )
            .to_py_err())
        } else {
            self.fallback_warning(field_name, field_type, value);
            Ok(())
        }
    }

    pub fn on_fallback_ser<S: serde::ser::Serializer>(
        &mut self,
        field_type: &str,
        value: &Bound<'_, PyAny>,
        field_name: Option<&FieldName<'_>>,
        check: SerCheck,
    ) -> Result<(), S::Error> {
        // special case for None as it's very common e.g. as a default value
        if value.is_none() {
            Ok(())
        } else if check.enabled() {
            // note: I think this should never actually happen since we use `to_python(..., mode='json')` during
            // JSON serialization to "try" union branches, but it's here for completeness/correctness
            // in particular, in future we could allow errors instead of warnings on fallback
            Err(S::Error::custom(UNEXPECTED_TYPE_SER_MARKER))
        } else {
            self.fallback_warning(field_name, field_type, value);
            Ok(())
        }
    }

    fn fallback_warning(&mut self, field_name: Option<&FieldName<'_>>, field_type: &str, value: &Bound<'_, PyAny>) {
        if self.mode != WarningsMode::None {
            self.register_warning(PydanticSerializationUnexpectedValue::new_from_parts(
                field_name.map(ToString::to_string),
                Some(field_type.to_string()),
                Some(value.clone().unbind()),
            ));
        }
    }

    pub fn final_check(&self, py: Python) -> PyResult<()> {
        if self.mode == WarningsMode::None {
            return Ok(());
        }

        if self.warnings.is_empty() {
            return Ok(());
        }

        let formatted_warnings: Vec<String> = self.warnings.iter().map(|w| w.__repr__(py)).collect();

        let message = format!("Pydantic serializer warnings:\n  {}", formatted_warnings.join("\n  "));
        if self.mode == WarningsMode::Warn {
            let user_warning_type = PyUserWarning::type_object(py);
            PyErr::warn(py, &user_warning_type, &CString::new(message)?, 0)
        } else {
            Err(PydanticSerializationError::new_err(message))
        }
    }
}

impl ContainsRecursionState for SerializationState<'_> {
    fn access_recursion_state<R>(&mut self, f: impl FnOnce(&mut RecursionState) -> R) -> R {
        f(&mut self.rec_guard)
    }
}

pub(crate) struct ScopedSetState<'scope, 'py, P, T>
where
    P: for<'p> Fn(&'p mut SerializationState<'py>) -> &'p mut T,
{
    /// The state which has been set for the scope.
    state: &'scope mut SerializationState<'py>,
    /// A function that projects from the state to the field that has been set.
    projector: P,
    /// The previous value of the field that has been set.
    value: T,
}

impl<'py, P, T> Drop for ScopedSetState<'_, 'py, P, T>
where
    P: for<'drop> Fn(&'drop mut SerializationState<'py>) -> &'drop mut T,
{
    fn drop(&mut self) {
        std::mem::swap((self.projector)(self.state), &mut self.value);
    }
}

impl<'py, P, T> Deref for ScopedSetState<'_, 'py, P, T>
where
    P: for<'p> Fn(&'p mut SerializationState<'py>) -> &'p mut T,
{
    type Target = SerializationState<'py>;

    fn deref(&self) -> &Self::Target {
        self.state
    }
}

impl<'py, P, T> DerefMut for ScopedSetState<'_, 'py, P, T>
where
    P: for<'p> Fn(&'p mut SerializationState<'py>) -> &'p mut T,
{
    fn deref_mut(&mut self) -> &mut SerializationState<'py> {
        self.state
    }
}

type ScopedIncludeExcludeState<'scope, 'py> = ScopedSetState<
    'scope,
    'py,
    for<'s> fn(&'s mut SerializationState<'py>) -> &'s mut (Option<Bound<'py, PyAny>>, Option<Bound<'py, PyAny>>),
    (Option<Bound<'py, PyAny>>, Option<Bound<'py, PyAny>>),
>;
