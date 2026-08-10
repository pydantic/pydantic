//! Cheaper key lookups on core-schema and core-config dicts while building validators and serializers.
//!
//! Building reads every schema node through a series of `dict` lookups, most of which are for optional keys that
//! are absent: a plain `{'type': 'str'}` node is probed for 9 optional schema keys and 8 config keys, and each
//! probe (`PyDict_GetItemRef`) costs 100+ instructions even when it misses. Two exact bookkeeping devices avoid
//! most of these misses without changing what is looked up where (and hence which error wins for an invalid
//! schema):
//!
//! * [`SchemaKeys`]: the lookups a builder does on *its* schema dict, counted. A dict with `len` entries in which
//!   `len` distinct keys have already been found present cannot contain any other key, so from that point on
//!   lookups of further (optional) keys are answered "absent" without touching the dict.
//! * [`BuildConfig`]: the config dict together with the set of known config keys it contains ([`ConfigKeys`],
//!   established once per config dict and build by looking at its handful of keys); a config lookup is only
//!   performed for a key that is present.
use std::cell::Cell;

use pyo3::exceptions::PyKeyError;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};

use crate::definitions::DefinitionsBuilder;
use crate::tools::{SchemaDict, py_err};

/// Lookups on one schema dict, see the module docs.
///
/// Only meant for the fixed, distinct keys a builder reads: looking the same key up twice through one `SchemaKeys`
/// would count it twice (debug builds assert against that).
pub struct SchemaKeys<'a, 'py> {
    dict: &'a Bound<'py, PyDict>,
    /// entries of `dict` not (yet) matched by a lookup
    unaccounted: Cell<usize>,
    #[cfg(debug_assertions)]
    looked_up: std::cell::RefCell<Vec<String>>,
}

impl<'a, 'py> SchemaKeys<'a, 'py> {
    pub fn new(dict: &'a Bound<'py, PyDict>) -> Self {
        Self {
            dict,
            unaccounted: Cell::new(dict.len()),
            #[cfg(debug_assertions)]
            looked_up: std::cell::RefCell::default(),
        }
    }

    /// For the schema dict of a validator / serializer builder, normally reached by dispatch on its `'type'`: carry
    /// on from the lookups the dispatcher did on this same dict (see [`DefinitionsBuilder::dispatch`]), or else
    /// just account for the `'type'` key by looking it up.
    pub fn new_typed<T>(dict: &'a Bound<'py, PyDict>, definitions: &mut DefinitionsBuilder<T>) -> PyResult<Self> {
        match definitions.take_dispatched(dict) {
            Some(detached) => Ok(Self {
                dict,
                unaccounted: Cell::new(detached.unaccounted),
                #[cfg(debug_assertions)]
                looked_up: std::cell::RefCell::new(detached.looked_up),
            }),
            None => {
                let keys = Self::new(dict);
                keys.get_item(intern!(dict.py(), "type"))?;
                Ok(keys)
            }
        }
    }

    /// The bookkeeping alone, to be resumed by [`Self::new_typed`] on the same dict.
    pub fn detach(self) -> DetachedSchemaKeys {
        DetachedSchemaKeys {
            dict: self.dict.as_ptr(),
            unaccounted: self.unaccounted.get(),
            #[cfg(debug_assertions)]
            looked_up: self.looked_up.into_inner(),
        }
    }

    #[inline]
    pub fn py(&self) -> Python<'py> {
        self.dict.py()
    }

    /// `dict.get(key)`
    pub fn get_item(&self, key: &Bound<'py, PyString>) -> PyResult<Option<Bound<'py, PyAny>>> {
        #[cfg(debug_assertions)]
        {
            let key_str = key.to_string();
            let mut looked_up = self.looked_up.borrow_mut();
            debug_assert!(
                !looked_up.contains(&key_str),
                "key {key_str:?} looked up twice through the same SchemaKeys"
            );
            looked_up.push(key_str);
        }
        if self.unaccounted.get() == 0 {
            // every entry of the dict has been matched by an earlier lookup of a different key
            return Ok(None);
        }
        let value = self.dict.get_item(key)?;
        if value.is_some() {
            self.unaccounted.set(self.unaccounted.get() - 1);
        }
        Ok(value)
    }

    /// `key in dict`
    pub fn contains(&self, key: &Bound<'py, PyString>) -> PyResult<bool> {
        Ok(self.get_item(key)?.is_some())
    }

    /// `dict[key]` given the earlier result of `get_item(key)`: the same `KeyError` as `get_as_req` for a missing
    /// item, raised where the item is needed rather than where it was looked up.
    pub fn required(item: Option<Bound<'py, PyAny>>, key: &Bound<'py, PyString>) -> PyResult<Bound<'py, PyAny>> {
        match item {
            Some(v) => Ok(v),
            None => py_err!(PyKeyError; "{key}"),
        }
    }

    /// The value for `key` in the schema, else for `config_key` in the config.
    pub fn get_as_or_config<T>(
        &self,
        key: &Bound<'py, PyString>,
        config: BuildConfig<'_, 'py>,
        config_key: ConfigKey,
    ) -> PyResult<Option<T>>
    where
        T: FromPyObjectOwned<'py>,
    {
        match self.get_as(key)? {
            Some(v) => Ok(Some(v)),
            None => config.get_as(config_key),
        }
    }

    /// The `strict` setting from the schema or else the config (default false).
    pub fn is_strict(&self, config: BuildConfig<'_, 'py>) -> PyResult<bool> {
        Ok(self
            .get_as_or_config(intern!(self.py(), "strict"), config, ConfigKey::Strict)?
            .unwrap_or(false))
    }
}

/// See [`SchemaKeys::detach`].
#[derive(Debug)]
pub struct DetachedSchemaKeys {
    /// (only compared by address)
    dict: *mut pyo3::ffi::PyObject,
    unaccounted: usize,
    #[cfg(debug_assertions)]
    looked_up: Vec<String>,
}

impl DetachedSchemaKeys {
    pub fn is_for(&self, dict: &Bound<'_, PyDict>) -> bool {
        self.dict == dict.as_ptr()
    }
}

impl<'py> SchemaDict<'py> for SchemaKeys<'_, 'py> {
    fn get_as<T>(&self, key: &Bound<'py, PyString>) -> PyResult<Option<T>>
    where
        T: FromPyObjectOwned<'py>,
    {
        match self.get_item(key)? {
            Some(t) => t.extract().map(Some).map_err(Into::into),
            None => Ok(None),
        }
    }

    fn get_as_req<T>(&self, key: &Bound<'py, PyString>) -> PyResult<T>
    where
        T: FromPyObjectOwned<'py>,
    {
        match self.get_item(key)? {
            Some(t) => t.extract().map_err(Into::into),
            None => py_err!(PyKeyError; "{key}"),
        }
    }
}

macro_rules! config_keys {
    ($($variant:ident => $name:literal,)+) => {
        /// The config keys read while building validators and serializers.
        #[derive(Debug, Clone, Copy, PartialEq, Eq)]
        #[repr(u8)]
        pub enum ConfigKey {
            $($variant,)+
        }

        impl ConfigKey {
            fn from_name(name: &str) -> Option<Self> {
                match name {
                    $($name => Some(Self::$variant),)+
                    _ => None,
                }
            }

            /// The (interned) key string.
            pub fn py_name(self, py: Python<'_>) -> &Bound<'_, PyString> {
                match self {
                    $(Self::$variant => intern!(py, $name),)+
                }
            }
        }
    };
}

config_keys! {
    Title => "title",
    Strict => "strict",
    ExtraFieldsBehavior => "extra_fields_behavior",
    TypedDictTotal => "typed_dict_total",
    FromAttributes => "from_attributes",
    LocByAlias => "loc_by_alias",
    RevalidateInstances => "revalidate_instances",
    ValidateDefault => "validate_default",
    StrMaxLength => "str_max_length",
    StrMinLength => "str_min_length",
    StrStripWhitespace => "str_strip_whitespace",
    StrToLower => "str_to_lower",
    StrToUpper => "str_to_upper",
    AllowInfNan => "allow_inf_nan",
    SerJsonTimedelta => "ser_json_timedelta",
    SerJsonTemporal => "ser_json_temporal",
    SerJsonBytes => "ser_json_bytes",
    SerJsonInfNan => "ser_json_inf_nan",
    ValJsonBytes => "val_json_bytes",
    HideInputInErrors => "hide_input_in_errors",
    ValidationErrorCause => "validation_error_cause",
    CoerceNumbersToStr => "coerce_numbers_to_str",
    RegexEngine => "regex_engine",
    CacheStrings => "cache_strings",
    ValidateByAlias => "validate_by_alias",
    ValidateByName => "validate_by_name",
    SerializeByAlias => "serialize_by_alias",
    PolymorphicSerialization => "polymorphic_serialization",
    UrlPreserveEmptyPath => "url_preserve_empty_path",
    // (not `CoreConfig` keys, but looked up in the config all the same)
    AsciiOnly => "ascii_only",
}

const _: () = assert!((ConfigKey::AsciiOnly as u32) < 64);

/// Which [`ConfigKey`]s a config dict contains.
#[derive(Debug, Clone, Copy)]
pub struct ConfigKeys(u64);

impl ConfigKeys {
    const NONE: Self = Self(0);
    /// "can't tell": every key has to be looked up
    const ALL: Self = Self(u64::MAX);

    /// Establish which known keys `config` contains, by name — which for `str` keys is exactly what decides a
    /// dict lookup. If any key is something else (its `__eq__` / `__hash__` could claim anything), all keys are
    /// reported as possibly present so that every lookup is really performed.
    pub fn of_dict(config: &Bound<'_, PyDict>) -> Self {
        let mut bits = 0u64;
        for (key, _) in config.iter() {
            let Ok(key) = key.cast_exact::<PyString>() else {
                return Self::ALL;
            };
            match key.to_str() {
                Ok(name) => {
                    if let Some(key) = ConfigKey::from_name(name) {
                        bits |= 1 << (key as u32);
                    }
                }
                Err(_) => return Self::ALL,
            }
        }
        Self(bits)
    }

    #[inline]
    pub fn contains(self, key: ConfigKey) -> bool {
        self.0 & (1 << (key as u32)) != 0
    }
}

/// The config dict for a build step, with cheap negative lookups (see the module docs).
#[derive(Clone, Copy)]
pub struct BuildConfig<'a, 'py> {
    dict: Option<&'a Bound<'py, PyDict>>,
    keys: ConfigKeys,
}

impl<'a, 'py> BuildConfig<'a, 'py> {
    pub fn new<T>(config: Option<&'a Bound<'py, PyDict>>, definitions: &mut DefinitionsBuilder<T>) -> Self {
        let keys = match config {
            Some(dict) => definitions.config_keys(dict),
            None => ConfigKeys::NONE,
        };
        Self { dict: config, keys }
    }

    #[inline]
    pub fn dict(&self) -> Option<&'a Bound<'py, PyDict>> {
        self.dict
    }

    /// `config.get(key)` converted to `T`
    pub fn get_as<T>(&self, key: ConfigKey) -> PyResult<Option<T>>
    where
        T: FromPyObjectOwned<'py>,
    {
        match self.dict {
            Some(dict) if self.keys.contains(key) => dict.get_as(key.py_name(dict.py())),
            _ => Ok(None),
        }
    }
}
