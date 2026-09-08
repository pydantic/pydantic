use std::collections::hash_map::Entry;
use std::hash::Hash;

use ahash::AHashMap;
use jiter::{JsonObject, JsonValue};
use smallvec::SmallVec;

use crate::build_tools::ExtraBehavior;
use crate::lookup_key::{FieldLookupPaths, LookupPath, LookupResult, LookupType, PathItem, PathItemString};

/// A tree of paths for lookups when trying to find fields from input.
///
/// The structure is nested maps, typically there is only one level unless there are `AliasPath` aliases
/// which require deeper lookups.
#[derive(Debug)]
pub struct LookupTree {
    inner: AHashMap<PathItemString, LookupTreeNode>,
    field_count: usize,
    node_count: usize,
}

impl LookupTree {
    /// Construct a `LookupTree` from a slice of fields and a function to get the `LookupKeyCollection` for each field.
    pub fn from_fields<T>(fields: &[T], get_field_collection: impl Fn(&T) -> &FieldLookupPaths) -> Self {
        Self::from_optional_fields(fields, |field| Some(get_field_collection(field)))
    }

    /// Variant of the above for cases where not all fields permit path-based lookup (and only accept indexing).
    pub fn from_optional_fields<T>(
        fields: &[T],
        get_field_collection: impl Fn(&T) -> Option<&FieldLookupPaths>,
    ) -> Self {
        let mut tree = Self {
            inner: AHashMap::with_capacity(fields.len()),
            field_count: fields.len(),
            node_count: 0,
        };

        for (field_index, field) in fields.iter().enumerate() {
            let Some(collection) = get_field_collection(field) else {
                continue;
            };

            add_path_to_map(
                &mut tree.inner,
                &collection.by_name,
                LookupFieldInfo {
                    field_index,
                    lookup_priority: LookupFieldPriority {
                        lookup_type: if collection.by_alias.is_empty() {
                            LookupType::Both
                        } else {
                            LookupType::Name
                        },
                        alias_index: 0,
                    },
                },
            );

            for (alias_index, alias) in collection.by_alias.iter().enumerate() {
                add_path_to_map(
                    &mut tree.inner,
                    alias,
                    LookupFieldInfo {
                        field_index,
                        lookup_priority: LookupFieldPriority {
                            lookup_type: LookupType::Alias,
                            alias_index,
                        },
                    },
                );
            }
        }
        for node in tree.inner.values_mut() {
            node.assign_indices(&mut tree.node_count);
        }
        tree
    }

    /// Resolve fields using alias priority and last-duplicate-key semantics.
    pub fn prepare_json<'a, 'data>(
        &self,
        object: &'a JsonObject<'data>,
        lookup_type: LookupType,
        extra_behavior: ExtraBehavior,
    ) -> JsonFieldResults<'a, 'data> {
        let mut results = vec![None; self.field_count];
        let mut seen = vec![false; self.node_count];
        for (key, value) in object.iter().rev() {
            if let Some(node) = self.inner.get(key.as_ref()) {
                node.collect_json(value, lookup_type, node.index, &mut seen, &mut results);
            }
        }
        let extras = if extra_behavior == ExtraBehavior::Ignore {
            Vec::new()
        } else {
            seen.fill(false);
            for (_, _, root_index) in results.iter().flatten() {
                seen[*root_index] = true;
            }
            object
                .iter()
                .filter(|(key, _)| self.inner.get(key.as_ref()).is_none_or(|node| !seen[node.index]))
                .map(|(key, value)| (key.as_ref(), value))
                .collect()
        };
        JsonFieldResults { results, extras }
    }
}

type JsonFieldResult<'a, 'data> = (LookupFieldInfo, &'a JsonValue<'data>, usize);

pub struct JsonFieldResults<'a, 'data> {
    results: Vec<Option<JsonFieldResult<'a, 'data>>>,
    pub extras: Vec<(&'a str, &'a JsonValue<'data>)>,
}

impl<'a, 'data> JsonFieldResults<'a, 'data> {
    pub fn lookup(&self, index: usize, paths: &'a FieldLookupPaths) -> LookupResult<'a, &'a JsonValue<'data>> {
        Ok(self.results[index].map(|(info, value, _)| {
            let path = match info.alias_index() {
                Some(index) => &paths.by_alias[index],
                None => &paths.by_name,
            };
            (path, value)
        }))
    }
}

/// When resolving data for a field, aliases are preferred over names, and earlier aliases are preferred over later ones.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct LookupFieldPriority {
    /// The type of lookups that will match this lookup
    lookup_type: LookupType,
    /// The index of this alias within the `AliasChoices` for the field
    alias_index: usize,
}

impl LookupFieldPriority {
    /// Returns `true` if `self` has higher priority than `other`, i.e. data from this lookup should be used over data from `other`.
    fn is_higher_priority_than(&self, other: &Self) -> bool {
        if self.lookup_type == LookupType::Name {
            // name lookups are never higher priority than other lookups
            return false;
        } else if other.lookup_type == LookupType::Name {
            // other is a name lookup, so self is higher priority
            return true;
        }

        // lower alias indices are higher priority
        self.alias_index < other.alias_index
    }
}

/// Represents a location in the lookup tree which corresponds to data for a specific field.
#[derive(Debug, Clone, Copy)]
struct LookupFieldInfo {
    /// The field which this lookup will populate.
    field_index: usize,
    /// Information about whether this data should be preferred over other possible matches for the same field.
    lookup_priority: LookupFieldPriority,
}

impl LookupFieldInfo {
    /// Whether this lookup should be used for the given lookup type (i.e. when validating by_name / by_alias)
    fn matches_lookup(&self, lookup_type: LookupType) -> bool {
        self.lookup_priority.lookup_type.matches(lookup_type)
    }

    /// The alias index for this lookup, if it is an alias lookup, or `None` if it is a name lookup.
    fn alias_index(&self) -> Option<usize> {
        if self.lookup_priority.lookup_type == LookupType::Alias {
            Some(self.lookup_priority.alias_index)
        } else {
            None
        }
    }
}

/// Represents a point in the lookup tree, containing exact matches plus possible nested lookups.
#[derive(Debug, Default)]
struct LookupTreeNode {
    index: usize,
    /// All fields which wanted _exactly_ this key, typically this is just a single entry
    fields: SmallVec<[LookupFieldInfo; 1]>,
    /// For nested lookups by name, e.g. `['foo', 'bar']`, typically empty
    map: AHashMap<PathItemString, LookupTreeNode>,
    /// For nested lookups by integer index, e.g. `['foo', 0]`, typically empty.
    /// Uses i128 to accommodate both usize and negative isize path items.
    list: AHashMap<i128, LookupTreeNode>,
}

impl LookupTreeNode {
    fn assign_indices(&mut self, next_index: &mut usize) {
        self.index = *next_index;
        *next_index += 1;
        for node in self.map.values_mut().chain(self.list.values_mut()) {
            node.assign_indices(next_index);
        }
    }

    fn collect_json<'a, 'data>(
        &self,
        value: &'a JsonValue<'data>,
        lookup_type: LookupType,
        root_index: usize,
        seen: &mut [bool],
        results: &mut [Option<JsonFieldResult<'a, 'data>>],
    ) {
        // Objects are visited backwards so a duplicate replaces the whole subtree,
        // even if the last occurrence no longer contains a matching alias path.
        if std::mem::replace(&mut seen[self.index], true) {
            return;
        }
        for info in &self.fields {
            if !info.matches_lookup(lookup_type) {
                continue;
            }
            let result = &mut results[info.field_index];
            if let Some((existing, _, _)) = result
                && existing.lookup_priority.is_higher_priority_than(&info.lookup_priority)
            {
                continue;
            }
            *result = Some((*info, value, root_index));
        }
        match value {
            JsonValue::Object(object) if !self.map.is_empty() => {
                for (key, value) in object.iter().rev() {
                    if let Some(node) = self.map.get(key.as_ref()) {
                        node.collect_json(value, lookup_type, root_index, seen, results);
                    }
                }
            }
            JsonValue::Array(array) => {
                for (index, node) in &self.list {
                    let index = if *index < 0 {
                        *index + array.len() as i128
                    } else {
                        *index
                    };
                    if let Some(value) = array.get(index as usize) {
                        node.collect_json(value, lookup_type, root_index, seen, results);
                    }
                }
            }
            _ => {}
        }
    }
}

fn add_field_to_map<K: Hash + Eq>(map: &mut AHashMap<K, LookupTreeNode>, key: K, info: LookupFieldInfo) {
    match map.entry(key) {
        Entry::Occupied(entry) => {
            entry.into_mut().fields.push(info);
        }
        Entry::Vacant(entry) => {
            entry.insert(LookupTreeNode {
                index: 0,
                fields: SmallVec::from_buf([info]),
                map: AHashMap::new(),
                list: AHashMap::new(),
            });
        }
    }
}

fn add_path_to_map(map: &mut AHashMap<PathItemString, LookupTreeNode>, path: &LookupPath, info: LookupFieldInfo) {
    let base_key = path.first_item().to_owned();
    let mut path_iter = path.rest().iter();

    let Some(mut current) = path_iter.next() else {
        // there was no items in "rest", so just a string key to add to the current map
        add_field_to_map(map, base_key, info);
        return;
    };

    // traverse the tree structure to find the final node to insert the field info into
    let mut tree_node = map.entry(base_key).or_default();
    for next in path_iter {
        tree_node = match current {
            PathItem::S(s) => tree_node.map.entry(s.clone()).or_default(),
            PathItem::Pos(i) => tree_node.list.entry(*i as i128).or_default(),
            PathItem::Neg(i) => tree_node.list.entry(-(*i as i128)).or_default(),
        };

        current = next;
    }

    // now have a terminal value
    match current {
        PathItem::S(s) => {
            add_field_to_map(&mut tree_node.map, s.clone(), info);
        }
        PathItem::Pos(i) => {
            add_field_to_map(&mut tree_node.list, *i as i128, info);
        }
        PathItem::Neg(i) => {
            add_field_to_map(&mut tree_node.list, -(*i as i128), info);
        }
    }
}
