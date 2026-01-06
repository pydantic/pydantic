use std::collections::hash_map::Entry;
use std::hash::Hash;

use ahash::AHashMap;
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

impl LookupTreeNode {
    /// Get all fields which wanted _exactly_ this key
    pub fn fields(&self) -> &[LookupFieldInfo] {
        &self.fields
    }

    /// Get the nested lookup map for further path items
    pub fn lookup_map(&self) -> &LookupMap {
        &self.lookup_map
    }
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
