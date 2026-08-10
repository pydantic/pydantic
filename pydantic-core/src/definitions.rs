/// Definition / reference management
/// Our definitions system is very similar to json schema's: there's ref strings and a definitions section
/// Unlike json schema we let you put definitions inline, not just in a single '#/$defs/' block or similar.
/// We use DefinitionsBuilder to collect the references / definitions into a single vector
/// and then get a definition from a reference using an integer id (just for performance of not using a HashMap)
use std::{
    borrow::Borrow,
    collections::hash_map::Entry,
    fmt::Debug,
    sync::{
        Arc, OnceLock, Weak,
        atomic::{AtomicBool, Ordering},
    },
};

use pyo3::{PyTraverseError, PyVisit, prelude::*, types::PyDict};

use crate::schema_keys::{ConfigKeys, DetachedSchemaKeys, SchemaKeys};
use crate::{build_tools::py_schema_err, py_gc::PyGcTraverse, tools::BuildHashMap};

/// Definitions are validators and serializers that are
/// shared by reference.
/// They come into play whenever there is recursion, e.g.
/// if you have validators A -> B -> A then A will be shared
/// by reference so that the SchemaValidator itself can own it.
/// These primarily get used by DefinitionRefValidator and DefinitionRefSerializer,
/// other validators / serializers primarily pass them around without interacting with them.
/// They get indexed by a ReferenceId, which are integer identifiers
/// that are handed out and managed by DefinitionsBuilder when the Schema{Validator,Serializer}
/// gets build.
pub struct Definitions<T>(BuildHashMap<Arc<String>, Definition<T>>);

struct Definition<T> {
    value: Arc<OnceLock<T>>,
    name: Arc<LazyName>,
}

/// Reference to a definition.
pub struct DefinitionRef<T> {
    reference: Arc<String>,
    // We use a weak reference to the definition to avoid a reference cycle
    // when recursive definitions are used.
    value: Weak<OnceLock<T>>,
    name: Arc<LazyName>,
}

// DefinitionRef can always be cloned (#[derive(Clone)] would require T: Clone)
impl<T> Clone for DefinitionRef<T> {
    fn clone(&self) -> Self {
        Self {
            reference: self.reference.clone(),
            value: self.value.clone(),
            name: self.name.clone(),
        }
    }
}

impl<T> DefinitionRef<T> {
    pub fn id(&self) -> usize {
        Weak::as_ptr(&self.value) as usize
    }

    pub fn get_or_init_name(&self, init: impl FnOnce(&T) -> String) -> &str {
        let Some(definition) = self.value.upgrade() else {
            return "...";
        };
        match definition.get() {
            Some(value) => self.name.get_or_init(|| init(value)),
            None => "...",
        }
    }

    pub fn read<R>(&self, f: impl FnOnce(Option<&T>) -> R) -> R {
        f(self.value.upgrade().as_ref().and_then(|value| value.get()))
    }
}

impl<T: Debug> Debug for DefinitionRef<T> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        // To avoid possible infinite recursion from recursive definitions,
        // a DefinitionRef just displays debug as its name
        self.name.fmt(f)
    }
}

impl<T: Debug> Debug for Definitions<T> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        // Formatted as a list for backwards compatibility; in principle
        // this could be formatted as a map. Maybe change in a future
        // minor release of pydantic.
        write![f, "["]?;
        let mut first = true;
        for def in self.0.values() {
            write![f, "{sep}{def:?}", sep = if first { "" } else { ", " }]?;
            first = false;
        }
        write![f, "]"]?;
        Ok(())
    }
}

impl<T: Debug> Debug for Definition<T> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self.value.get() {
            Some(value) => value.fmt(f),
            None => "...".fmt(f),
        }
    }
}

impl<T: PyGcTraverse> PyGcTraverse for DefinitionRef<T> {
    fn py_gc_traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        if let Some(value) = self.value.upgrade().as_ref().and_then(|v| v.get()) {
            value.py_gc_traverse(visit)?;
        }
        Ok(())
    }
}

impl<T: PyGcTraverse> PyGcTraverse for Definitions<T> {
    fn py_gc_traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        for value in self.0.values() {
            if let Some(value) = value.value.get() {
                value.py_gc_traverse(visit)?;
            }
        }
        Ok(())
    }
}

#[derive(Debug)]
pub struct DefinitionsBuilder<T> {
    definitions: Definitions<T>,
    use_prebuilt: bool,
    /// the known keys of each config dict met during this build (each dict is queried many times over)
    config_keys: Vec<(Py<PyDict>, ConfigKeys)>,
    /// see `dispatch`
    dispatched: Option<DetachedSchemaKeys>,
}

impl<T> DefinitionsBuilder<T> {
    /// Run `build` — the type-specific builder for the schema dict of `keys`, found by dispatch on its `'type'` —
    /// letting the `SchemaKeys::new_typed` of that builder carry on from `keys` (the dispatcher's lookups on the same
    /// dict) rather than start counting afresh.
    pub fn dispatch<R>(&mut self, keys: SchemaKeys<'_, '_>, build: impl FnOnce(&mut Self) -> R) -> R {
        self.dispatched = Some(keys.detach());
        let result = build(self);
        // (normally taken by the builder straight away; never left behind past the build of that dict, during which
        // the dict is certainly alive, so the address comparison in `take_dispatched` can't be fooled)
        self.dispatched = None;
        result
    }

    /// The bookkeeping left by `dispatch` for `dict`, if that is the dict being dispatched on.
    pub fn take_dispatched(&mut self, dict: &Bound<'_, PyDict>) -> Option<DetachedSchemaKeys> {
        match &self.dispatched {
            Some(detached) if detached.is_for(dict) => self.dispatched.take(),
            _ => None,
        }
    }

    /// Which known config keys `config` contains; established once per dict and build.
    pub fn config_keys(&mut self, config: &Bound<'_, PyDict>) -> ConfigKeys {
        // (identity is a sound cache key here: the vec holds a reference to each dict, so none can go away and have
        // its address reused while cached)
        if let Some((_, keys)) = self.config_keys.iter().find(|(d, _)| d.as_ptr() == config.as_ptr()) {
            return *keys;
        }
        let keys = ConfigKeys::of_dict(config);
        if self.config_keys.len() >= 64 {
            self.config_keys.clear();
        }
        self.config_keys.push((config.clone().unbind(), keys));
        keys
    }
}

impl<T: std::fmt::Debug> DefinitionsBuilder<T> {
    pub fn new(use_prebuilt: bool) -> Self {
        Self {
            definitions: Definitions(BuildHashMap::default()),
            use_prebuilt,
            config_keys: Vec::new(),
            dispatched: None,
        }
    }

    /// Whether prebuilt validators/serializers should be used
    pub fn use_prebuilt(&self) -> bool {
        self.use_prebuilt
    }

    /// Get a ReferenceId for the given reference string.
    pub fn get_definition(&mut self, reference: &str) -> DefinitionRef<T> {
        // We either need a String copy or two hashmap lookups
        // Neither is better than the other
        // We opted for the easier outward facing API
        let reference = Arc::new(reference.to_string());
        let value = match self.definitions.0.entry(reference.clone()) {
            Entry::Occupied(entry) => entry.into_mut(),
            Entry::Vacant(entry) => entry.insert(Definition {
                value: Arc::new(OnceLock::new()),
                name: Arc::new(LazyName::new()),
            }),
        };
        DefinitionRef {
            reference,
            value: Arc::downgrade(&value.value),
            name: value.name.clone(),
        }
    }

    /// Add a definition, returning the ReferenceId that maps to it
    pub fn add_definition(&mut self, reference: String, value: T) -> PyResult<DefinitionRef<T>> {
        let reference = Arc::new(reference);
        let value = match self.definitions.0.entry(reference.clone()) {
            Entry::Occupied(entry) => {
                let definition = entry.into_mut();
                match definition.value.set(value) {
                    Ok(()) => definition,
                    Err(_) => return py_schema_err!("Duplicate ref: `{reference}`"),
                }
            }
            Entry::Vacant(entry) => entry.insert(Definition {
                value: Arc::new(OnceLock::from(value)),
                name: Arc::new(LazyName::new()),
            }),
        };
        Ok(DefinitionRef {
            reference,
            value: Arc::downgrade(&value.value),
            name: value.name.clone(),
        })
    }

    /// Consume this Definitions into a vector of items, indexed by each items ReferenceId
    pub fn finish(self) -> PyResult<Definitions<T>> {
        for (reference, def) in &self.definitions.0 {
            if def.value.get().is_none() {
                return py_schema_err!("Definitions error: definition `{reference}` was never filled");
            }
        }
        Ok(self.definitions)
    }
}

/// Because definitions can create recursive structures, we often need to be able to populate
/// values lazily from these structures in a way that avoids infinite recursion. This structure
/// avoids infinite recursion by returning a default value when a recursion loop is detected.
pub(crate) struct RecursionSafeCache<T> {
    cache: OnceLock<T>,
    in_recursion: AtomicBool,
}

impl<T: Clone> Clone for RecursionSafeCache<T> {
    fn clone(&self) -> Self {
        Self {
            cache: self.cache.clone(),
            in_recursion: AtomicBool::new(false),
        }
    }
}

impl<T> RecursionSafeCache<T> {
    /// Creates a new RecursionSafeCache
    pub(crate) fn new() -> Self {
        Self {
            cache: OnceLock::new(),
            in_recursion: AtomicBool::new(false),
        }
    }

    /// Gets or initialized the cached value, returning the default in the case of recursion loops
    pub(crate) fn get_or_init<D: ?Sized>(&self, init: impl FnOnce() -> T, recursive_default: &'static D) -> &D
    where
        T: Borrow<D>,
    {
        if let Some(cached) = self.cache.get() {
            return cached.borrow();
        }

        if self
            .in_recursion
            .compare_exchange(false, true, Ordering::SeqCst, Ordering::SeqCst)
            .is_err()
        {
            return recursive_default;
        }
        let result = self.cache.get_or_init(init).borrow();
        self.in_recursion.store(false, Ordering::SeqCst);
        result
    }

    /// Gets the value, if it is set
    fn get(&self) -> Option<&T> {
        self.cache.get()
    }
}

#[derive(Clone)]
struct LazyName(RecursionSafeCache<String>);

impl LazyName {
    fn new() -> Self {
        Self(RecursionSafeCache::new())
    }

    /// Gets the validator name, returning the default in the case of recursion loops
    fn get_or_init(&self, init: impl FnOnce() -> String) -> &str {
        self.0.get_or_init(init, "...")
    }
}

impl Debug for LazyName {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        self.0.get().map_or("...", String::as_str).fmt(f)
    }
}
