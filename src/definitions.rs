/// Definition / reference management
/// Our definitions system is very similar to json schema's: there's ref strings and a definitions section
/// Unlike json schema we let you put definitions inline, not just in a single '#/$defs/' block or similar.
/// We use DefinitionsBuilder to collect the references / definitions into a single vector
/// and then get a definition from a reference using an integer id (just for performance of not using a HashMap)
use std::{
    collections::hash_map::Entry,
    fmt::Debug,
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc, OnceLock,
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
#[derive(Clone)]
pub struct Definitions<T>(AHashMap<Arc<String>, Definition<T>>);

/// Internal type which contains a definition to be filled
pub struct Definition<T>(Arc<DefinitionInner<T>>);

struct DefinitionInner<T> {
    value: OnceLock<T>,
    name: LazyName,
}

/// Reference to a definition.
pub struct DefinitionRef<T> {
    name: Arc<String>,
    value: Definition<T>,
}

// DefinitionRef can always be cloned (#[derive(Clone)] would require T: Clone)
impl<T> Clone for DefinitionRef<T> {
    fn clone(&self) -> Self {
        Self {
            name: self.name.clone(),
            value: self.value.clone(),
        }
    }
}

impl<T> DefinitionRef<T> {
    pub fn id(&self) -> usize {
        Arc::as_ptr(&self.value.0) as usize
    }

    pub fn get_or_init_name(&self, init: impl FnOnce(&T) -> String) -> &str {
        match self.value.0.value.get() {
            Some(value) => self.value.0.name.get_or_init(|| init(value)),
            None => "...",
        }
    }

    pub fn get(&self) -> Option<&T> {
        self.value.0.value.get()
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

impl<T> Clone for Definition<T> {
    fn clone(&self) -> Self {
        Self(self.0.clone())
    }
}

impl<T: Debug> Debug for Definition<T> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self.0.value.get() {
            Some(value) => value.fmt(f),
            None => "...".fmt(f),
        }
    }
}

impl<T: PyGcTraverse> PyGcTraverse for DefinitionRef<T> {
    fn py_gc_traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        if let Some(value) = self.value.0.value.get() {
            value.py_gc_traverse(visit)?;
        }
        Ok(())
    }
}

impl<T: PyGcTraverse> PyGcTraverse for Definitions<T> {
    fn py_gc_traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        for value in self.0.values() {
            if let Some(value) = value.0.value.get() {
                value.py_gc_traverse(visit)?;
            }
        }
        Ok(())
    }
}

#[derive(Clone, Debug)]
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
        let name = Arc::new(reference.to_string());
        let value = match self.definitions.0.entry(name.clone()) {
            Entry::Occupied(entry) => entry.into_mut(),
            Entry::Vacant(entry) => entry.insert(Definition(Arc::new(DefinitionInner {
                value: OnceLock::new(),
                name: LazyName::new(),
            }))),
        };
        DefinitionRef {
            name,
            value: value.clone(),
        }
    }

    /// Add a definition, returning the ReferenceId that maps to it
    pub fn add_definition(&mut self, reference: String, value: T) -> PyResult<DefinitionRef<T>> {
        let name = Arc::new(reference);
        let value = match self.definitions.0.entry(name.clone()) {
            Entry::Occupied(entry) => {
                let definition = entry.into_mut();
                match definition.0.value.set(value) {
                    Ok(()) => definition.clone(),
                    Err(_) => return py_schema_err!("Duplicate ref: `{}`", name),
                }
            }
            Entry::Vacant(entry) => entry
                .insert(Definition(Arc::new(DefinitionInner {
                    value: OnceLock::from(value),
                    name: LazyName::new(),
                })))
                .clone(),
        };
        Ok(DefinitionRef { name, value })
    }

    /// Consume this Definitions into a vector of items, indexed by each items ReferenceId
    pub fn finish(self) -> PyResult<Definitions<T>> {
        for (reference, def) in &self.definitions.0 {
            if def.0.value.get().is_none() {
                return py_schema_err!("Definitions error: definition `{}` was never filled", reference);
            }
        }
        Ok(self.definitions)
    }
}

struct LazyName {
    initialized: OnceLock<String>,
    in_recursion: AtomicBool,
}

impl LazyName {
    fn new() -> Self {
        Self {
            initialized: OnceLock::new(),
            in_recursion: AtomicBool::new(false),
        }
    }

    /// Gets the validator name, returning the default in the case of recursion loops
    fn get_or_init(&self, init: impl FnOnce() -> String) -> &str {
        if let Some(s) = self.initialized.get() {
            return s.as_str();
        }

        if self
            .in_recursion
            .compare_exchange(false, true, Ordering::SeqCst, Ordering::SeqCst)
            .is_err()
        {
            return "...";
        }
        let result = self.initialized.get_or_init(init).as_str();
        self.in_recursion.store(false, Ordering::SeqCst);
        result
    }
}

impl Debug for LazyName {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        self.initialized.get().map_or("...", String::as_str).fmt(f)
    }
}

impl Clone for LazyName {
    fn clone(&self) -> Self {
        Self {
            initialized: OnceLock::new(),
            in_recursion: AtomicBool::new(false),
        }
    }
}
