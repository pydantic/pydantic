use std::hash::Hash;
use std::{borrow::Cow, collections::hash_map::Entry};

use ahash::AHashMap;
use jiter::{JsonArray, JsonValue};
use smallvec::SmallVec;

use crate::lookup_key::{LookupPath, LookupPathCollection, LookupType, PathItem, PathItemString};

/// A tree of paths for lookups when trying to find fields from input names.
#[derive(Debug)]
pub struct LookupTree {
    /// FIXME: make private again
    pub inner: AHashMap<PathItemString, LookupTreeNode>,
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
                    field_lookup_type: if collection.by_alias.is_empty() {
                        LookupType::Both
                    } else {
                        LookupType::Name
                    },
                },
            );

            for alias in &collection.by_alias {
                add_path_to_map(
                    &mut tree.inner,
                    alias,
                    LookupFieldInfo {
                        field_index,
                        field_lookup_type: LookupType::Alias,
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

#[derive(Debug, Clone, Copy)]
pub struct LookupFieldInfo {
    pub field_index: usize,
    pub field_lookup_type: LookupType,
}

#[derive(Debug, Default)]
pub struct LookupTreeNode {
    /// All fields which wanted _exactly_ this key, typically this is just a single entry
    fields: SmallVec<[LookupFieldInfo; 1]>,
    /// Fields which use this key as path prefix (often empty)
    lookup_map: LookupMap,
}

#[derive(Clone, Copy)]
pub enum LookupPathItem<'a> {
    Key(&'a str),
    Index(i64),
}

#[derive(Debug, Default)]
pub struct LookupMap {
    /// For lookups by name, e.g. `['foo', 'bar']`
    pub map: AHashMap<PathItemString, LookupTreeNode>,
    /// For lookups by integer index, e.g. `['foo', 0]`
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
                lookup_map: LookupMap::default(),
            });
        }
    }
}

fn add_path_to_map(map: &mut AHashMap<PathItemString, LookupTreeNode>, path: &LookupPath, info: LookupFieldInfo) {
    if path.rest().is_empty() {
        // terminal value
        add_field_to_map(map, path.first_item().to_owned(), info);
        return;
    }

    let mut nested_map = &mut map.entry(path.first_item().to_owned()).or_default().lookup_map;

    let mut path_iter = path.rest().iter();

    let mut current = path_iter.next().expect("rest is non-empty");

    for next in path_iter {
        nested_map = match current {
            PathItem::S(s) => {
                let str_key = s.clone();
                &mut nested_map.map.entry(str_key).or_default().lookup_map
            }
            PathItem::Pos(i) => &mut nested_map.list.entry(*i as i64).or_default().lookup_map,
            PathItem::Neg(i) => &mut nested_map.list.entry(-(*i as i64)).or_default().lookup_map,
        };

        current = next;
    }

    // now have a terminal value
    match current {
        PathItem::S(s) => {
            add_field_to_map(&mut nested_map.map, s.clone(), info);
        }
        PathItem::Pos(i) => {
            add_field_to_map(&mut nested_map.list, *i as i64, info);
        }
        PathItem::Neg(i) => {
            add_field_to_map(&mut nested_map.list, -(*i as i64), info);
        }
    }
}

/// Iterator for matching fields in a lookup tree against JSON values
pub struct LookupMatchesIter<'a, 'j> {
    /// Current stack of the iterator; avoids allocating if the fields do not have nested-level aliases
    stack: SmallVec<[NestedFrame<'a, 'j>; 1]>,
}

struct NestedFrame<'a, 'j> {
    json_value: &'a JsonValue<'j>,
    lookup_path: LookupPathItem<'a>,
    node: &'a LookupTreeNode,
    state: FrameState<'a, 'j>,
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

        Self { stack }
    }

    pub fn next_match(&mut self) -> Option<(&'_ LookupFieldInfo, &'_ JsonValue<'j>, LookupMatchesStack<'_, 'a, 'j>)> {
        'top_level: while let Some(frame) = self.stack.last_mut() {
            // Initialize exploration state if needed
            match &mut frame.state {
                FrameState::Fields { fields } => {
                    if let Some(field_info) = fields.next() {
                        return Some((field_info, frame.json_value, LookupMatchesStack { inner: &self.stack }));
                    }

                    // no more fields, possibly explore nested structures if there are complex aliases
                    match frame.json_value {
                        JsonValue::Object(obj) if !frame.node.lookup_map.map.is_empty() => {
                            frame.state = FrameState::NestedObject { iter: obj.iter() };
                        }
                        JsonValue::Array(arr) if !frame.node.lookup_map.list.is_empty() => {
                            frame.state = FrameState::NestedArray {
                                json_array: arr,
                                iter: frame.node.lookup_map.list.iter(),
                            };
                        }
                        _ => {
                            self.stack.pop();
                        }
                    }
                }
                FrameState::NestedObject { iter } => {
                    if let Some(next_frame) = iter.by_ref().find_map(|(key, value)| {
                        let nested_node = frame.node.lookup_map.map.get(key.as_ref())?;
                        Some(NestedFrame {
                            json_value: value,
                            lookup_path: LookupPathItem::Key(key.as_ref()),
                            node: nested_node,
                            state: FrameState::Fields {
                                fields: nested_node.fields.iter(),
                            },
                        })
                    }) {
                        self.stack.push(next_frame);
                        continue 'top_level;
                    }

                    self.stack.pop();
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
                        self.stack.push(next_frame);
                        continue 'top_level;
                    }

                    self.stack.pop();
                }
            }
        }
        None
    }
}

pub struct LookupMatchesStack<'stack, 'a, 'j> {
    inner: &'stack SmallVec<[NestedFrame<'a, 'j>; 1]>,
}

impl<'a> LookupMatchesStack<'_, 'a, '_> {
    /// Iterate paths from the deepest level up to the root
    pub fn iter_paths_bottom_up(&self) -> impl Iterator<Item = LookupPathItem<'a>> + use<'_, 'a> {
        self.inner.iter().rev().map(|frame| frame.lookup_path)
    }
}
