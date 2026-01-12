use std::hash::Hash;
use std::{borrow::Cow, collections::hash_map::Entry};

use ahash::AHashMap;
use jiter::{JsonArray, JsonValue};
use smallvec::SmallVec;

use crate::errors::LocItem;
use crate::lookup_key::{LookupPath, LookupPathCollection, LookupType, PathItem, PathItemString};

/// A tree of paths for lookups when trying to find fields from input.
///
/// The structure is nested maps, typically there is only one level unless there are `AliasPath` aliases
/// which require deeper lookups.
#[derive(Debug)]
pub struct LookupTree {
    inner: AHashMap<PathItemString, LookupTreeNode>,
}

impl LookupTree {
    /// Construct a `LookupTree` from a slice of fields and a function to get the `LookupKeyCollection` for each field.
    pub fn from_fields<T>(fields: &[T], get_field_collection: impl Fn(&T) -> &LookupPathCollection) -> Self {
        let mut tree = Self {
            inner: AHashMap::with_capacity(fields.len()),
        };

        for (field_index, field) in fields.iter().enumerate() {
            let collection = get_field_collection(field);

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
        tree
    }

    /// Given a root key and JSON object representing the structure at that key, iterates through all
    /// paths in the lookup tree where there is a field which matches that path.
    pub fn iter_matches<'a, 'j>(
        &'a self,
        root_key: &'a str,
        json_value: &'a JsonValue<'j>,
    ) -> LookupMatchesIter<'a, 'j> {
        let node = self.inner.get(root_key);
        LookupMatchesIter::new(root_key, node, json_value)
    }
}

/// When resolving data for a field, aliases are preferred over names, and earlier aliases are preferred over later ones.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct LookupFieldPriority {
    /// The type of lookups that will match this lookup
    lookup_type: LookupType,
    /// The index of this alias within the `AliasChoices` for the field
    alias_index: usize,
}

impl LookupFieldPriority {
    /// Returns `true` if `self` has higher priority than `other`, i.e. data from this lookup should be used over data from `other`.
    pub fn is_higher_priority_than(&self, other: &Self) -> bool {
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
pub struct LookupFieldInfo {
    /// The field which this lookup will populate.
    pub field_index: usize,
    /// Information about whether this data should be preferred over other possible matches for the same field.
    pub lookup_priority: LookupFieldPriority,
}

impl LookupFieldInfo {
    /// Whether this lookup should be used for the given lookup type (i.e. when validating by_name / by_alias)
    pub fn matches_lookup(&self, lookup_type: LookupType) -> bool {
        self.lookup_priority.lookup_type.matches(lookup_type)
    }
}

/// Represents a point in the lookup tree, containing exact matches plus possible nested lookups.
#[derive(Debug, Default)]
pub struct LookupTreeNode {
    /// All fields which wanted _exactly_ this key, typically this is just a single entry
    fields: SmallVec<[LookupFieldInfo; 1]>,
    /// For nested lookups by name, e.g. `['foo', 'bar']`, typically empty
    pub map: AHashMap<PathItemString, LookupTreeNode>,
    /// For nested lookups by integer index, e.g. `['foo', 0]`, typically empty
    pub list: AHashMap<i64, LookupTreeNode>,
}

fn add_field_to_map<K: Hash + Eq>(map: &mut AHashMap<K, LookupTreeNode>, key: K, info: LookupFieldInfo) {
    match map.entry(key) {
        Entry::Occupied(entry) => {
            entry.into_mut().fields.push(info);
        }
        Entry::Vacant(entry) => {
            entry.insert(LookupTreeNode {
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
            PathItem::Pos(i) => tree_node.list.entry(*i as i64).or_default(),
            PathItem::Neg(i) => tree_node.list.entry(-(*i as i64)).or_default(),
        };

        current = next;
    }

    // now have a terminal value
    match current {
        PathItem::S(s) => {
            add_field_to_map(&mut tree_node.map, s.clone(), info);
        }
        PathItem::Pos(i) => {
            add_field_to_map(&mut tree_node.list, *i as i64, info);
        }
        PathItem::Neg(i) => {
            add_field_to_map(&mut tree_node.list, -(*i as i64), info);
        }
    }
}

/// Iterator for matching fields in a lookup tree against JSON values, retrurn value of `iter_matches`.
///
/// Call `next_match` to get the next matching field along with the JSON value and the path taken to reach it.
///
/// This isn't a typical `Iterator` because `next_match` returns data which borrows from the iterator itself,
/// not yet supported by Rust's `Iterator` trait.
pub struct LookupMatchesIter<'a, 'j> {
    stack: LookupMatchesStack<'a, 'j>,
}

/// Current stack of the `LookupMatches` iterator
pub struct LookupMatchesStack<'a, 'j>(
    // uses SmallVec to avoid allocating if there are no `AliasPath` lookups
    SmallVec<[NestedFrame<'a, 'j>; 1]>,
);

/// State of the iterator at a given depth in the lookup tree
struct NestedFrame<'a, 'j> {
    json_value: &'a JsonValue<'j>,
    lookup_path: LookupPathItem<'a>,
    node: &'a LookupTreeNode,
    state: FrameState<'a, 'j>,
}

#[derive(Clone, Copy)]
enum LookupPathItem<'a> {
    Key(&'a str),
    Index(i64),
}

enum FrameState<'a, 'j> {
    /// Iterating through all fields that match exactly this path
    Fields {
        fields: std::slice::Iter<'a, LookupFieldInfo>,
    },
    /// Iterating through a JSON object at this path which might have matches on its keys
    NestedObject {
        iter: std::slice::Iter<'a, (Cow<'j, str>, JsonValue<'j>)>,
    },
    /// Iterating through a JSON array at this path which might have matches on its indices
    NestedArray {
        // NB we iterate the interesting entries in the lookup map, not the JSON array itself
        iter: std::collections::hash_map::Iter<'a, i64, LookupTreeNode>,
        json_array: &'a JsonArray<'j>,
    },
}

impl<'a, 'j> LookupMatchesIter<'a, 'j> {
    fn new(root_key: &'a str, node: Option<&'a LookupTreeNode>, json_value: &'a JsonValue<'j>) -> Self {
        let stack = if let Some(node) = node {
            SmallVec::from_buf([NestedFrame {
                json_value,
                lookup_path: LookupPathItem::Key(root_key),
                node,
                state: FrameState::Fields {
                    fields: node.fields.iter(),
                },
            }])
        } else {
            SmallVec::new()
        };

        Self {
            stack: LookupMatchesStack(stack),
        }
    }

    pub fn next_match(&mut self) -> Option<(&'_ LookupFieldInfo, &'_ JsonValue<'j>, &'_ LookupMatchesStack<'a, 'j>)> {
        'top_level: while let Some(frame) = self.stack.0.last_mut() {
            // Initialize exploration state if needed
            match &mut frame.state {
                FrameState::Fields { fields } => {
                    if let Some(field_info) = fields.next() {
                        return Some((field_info, frame.json_value, &self.stack));
                    }

                    // no more fields, possibly explore nested structures if there are complex aliases
                    match frame.json_value {
                        JsonValue::Object(obj) if !frame.node.map.is_empty() => {
                            frame.state = FrameState::NestedObject { iter: obj.iter() };
                        }
                        JsonValue::Array(arr) if !frame.node.list.is_empty() => {
                            frame.state = FrameState::NestedArray {
                                json_array: arr,
                                iter: frame.node.list.iter(),
                            };
                        }
                        _ => {
                            self.stack.0.pop();
                        }
                    }
                }
                FrameState::NestedObject { iter } => {
                    if let Some(next_frame) = iter.by_ref().find_map(|(key, value)| {
                        let nested_node = frame.node.map.get(key.as_ref())?;
                        Some(NestedFrame {
                            json_value: value,
                            lookup_path: LookupPathItem::Key(key.as_ref()),
                            node: nested_node,
                            state: FrameState::Fields {
                                fields: nested_node.fields.iter(),
                            },
                        })
                    }) {
                        self.stack.0.push(next_frame);
                        continue 'top_level;
                    }

                    self.stack.0.pop();
                }
                FrameState::NestedArray { json_array, iter } => {
                    if let Some(next_frame) = iter.by_ref().find_map(|(list_item, nested_node)| {
                        let index = if *list_item < 0 {
                            list_item + json_array.len() as i64
                        } else {
                            *list_item
                        };

                        let value = json_array.get(index as usize)?;
                        Some(NestedFrame {
                            json_value: value,
                            lookup_path: LookupPathItem::Index(*list_item),
                            node: nested_node,
                            state: FrameState::Fields {
                                fields: nested_node.fields.iter(),
                            },
                        })
                    }) {
                        self.stack.0.push(next_frame);
                        continue 'top_level;
                    }

                    self.stack.0.pop();
                }
            }
        }
        None
    }
}

impl LookupMatchesStack<'_, '_> {
    /// Iterate the location items representing the path taken to reach the current match
    pub fn iter_loc_items(&self) -> impl DoubleEndedIterator<Item = LocItem> + use<'_> {
        self.0.iter().map(|frame| match frame.lookup_path {
            LookupPathItem::Key(s) => s.into(),
            LookupPathItem::Index(i) => i.into(),
        })
    }
}
