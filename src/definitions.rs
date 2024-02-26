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
        atomic::{AtomicBool, Ordering},
        Arc, OnceLock, Weak,
    },
};

use pyo3::{prelude::*, PyTraverseError, PyVisit};

use ahash::AHashMap;

use crate::{build_tools::py_schema_err, py_gc::PyGcTraverse};

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
pub struct Definitions<T>(AHashMap<Arc<String>, Definition<T>>);

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
}

impl<T: std::fmt::Debug> DefinitionsBuilder<T> {
    pub fn new() -> Self {
        Self {
            definitions: Definitions(AHashMap::new()),
        }
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
                    Err(_) => return py_schema_err!("Duplicate ref: `{}`", reference),
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
                return py_schema_err!("Definitions error: definition `{}` was never filled", reference);
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
