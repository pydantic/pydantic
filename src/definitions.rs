/// Definition / reference management
/// Our definitions system is very similar to json schema's: there's ref strings and a definitions section
/// Unlike json schema we let you put definitions inline, not just in a single '#/$defs/' block or similar.
/// We use DefinitionsBuilder to collect the references / definitions into a single vector
/// and then get a definition from a reference using an integer id (just for performance of not using a HashMap)
use std::collections::hash_map::Entry;

use pyo3::prelude::*;

use ahash::AHashMap;

use crate::build_tools::py_schema_err;

// An integer id for the reference
pub type ReferenceId = usize;

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
pub type Definitions<T> = [T];

#[derive(Clone, Debug)]
struct Definition<T> {
    pub id: ReferenceId,
    pub value: Option<T>,
}

#[derive(Clone, Debug)]
pub struct DefinitionsBuilder<T> {
    definitions: AHashMap<String, Definition<T>>,
}

impl<T: Clone + std::fmt::Debug> DefinitionsBuilder<T> {
    pub fn new() -> Self {
        Self {
            definitions: AHashMap::new(),
        }
    }

    /// Get a ReferenceId for the given reference string.
    // This ReferenceId can later be used to retrieve a definition
    pub fn get_reference_id(&mut self, reference: &str) -> ReferenceId {
        let next_id = self.definitions.len();
        // We either need a String copy or two hashmap lookups
        // Neither is better than the other
        // We opted for the easier outward facing API
        match self.definitions.entry(reference.to_string()) {
            Entry::Occupied(entry) => entry.get().id,
            Entry::Vacant(entry) => {
                entry.insert(Definition {
                    id: next_id,
                    value: None,
                });
                next_id
            }
        }
    }

    /// Add a definition, returning the ReferenceId that maps to it
    pub fn add_definition(&mut self, reference: String, value: T) -> PyResult<ReferenceId> {
        let next_id = self.definitions.len();
        match self.definitions.entry(reference.clone()) {
            Entry::Occupied(mut entry) => match entry.get_mut().value.replace(value) {
                Some(_) => py_schema_err!("Duplicate ref: `{}`", reference),
                None => Ok(entry.get().id),
            },
            Entry::Vacant(entry) => {
                entry.insert(Definition {
                    id: next_id,
                    value: Some(value),
                });
                Ok(next_id)
            }
        }
    }

    /// Retrieve an item definition using a ReferenceId
    /// Will raise an error if the definition for that reference does not yet exist
    pub fn get_definition(&self, reference_id: ReferenceId) -> PyResult<&T> {
        let (reference, def) = match self.definitions.iter().find(|(_, def)| def.id == reference_id) {
            Some(v) => v,
            None => return py_schema_err!("Definitions error: no definition for ReferenceId `{}`", reference_id),
        };
        match def.value.as_ref() {
            Some(v) => Ok(v),
            None => py_schema_err!(
                "Definitions error: attempted to use `{}` before it was filled",
                reference
            ),
        }
    }

    /// Consume this Definitions into a vector of items, indexed by each items ReferenceId
    pub fn finish(self) -> PyResult<Vec<T>> {
        // We need to create a vec of defs according to the order in their ids
        let mut defs: Vec<(usize, T)> = Vec::new();
        for (reference, def) in self.definitions {
            match def.value {
                None => return py_schema_err!("Definitions error: definition {} was never filled", reference),
                Some(v) => defs.push((def.id, v)),
            }
        }
        defs.sort_by_key(|(id, _)| *id);
        Ok(defs.into_iter().map(|(_, v)| v).collect())
    }
}
