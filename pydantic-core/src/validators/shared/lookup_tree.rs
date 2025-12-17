use std::collections::hash_map::Entry;
use std::hash::Hash;

use ahash::AHashMap;

use crate::lookup_key::{LookupKey, LookupKeyCollection, LookupPath, LookupType, PathItem, PathItemString};

/// A tree of paths for lookups when trying to find fields from input names.
#[derive(Debug)]
pub struct LookupTree {
    /// FIXME: make private again
    pub inner: AHashMap<PathItemString, LookupTreeNode>,
}

impl LookupTree {
    pub fn new() -> Self {
        Self { inner: AHashMap::new() }
    }

    pub fn add_lookup_collection_for_field(&mut self, collection: &LookupKeyCollection, field_index: usize) {
        let LookupKey::Simple(path) = &collection.by_name else {
            panic!("name lookup is always simple");
        };

        self.add_field(
            path.first_item().clone(),
            LookupFieldInfo {
                field_index,
                field_lookup_type: if collection.by_alias.is_some() {
                    LookupType::Name
                } else {
                    LookupType::Both
                },
            },
        );

        if let Some(alias_key) = &collection.by_alias {
            let info = LookupFieldInfo {
                field_index,
                field_lookup_type: LookupType::Alias,
            };
            match alias_key {
                LookupKey::Simple(path) => {
                    // should be a single string key
                    debug_assert!(path.rest().is_empty());
                    self.add_field(path.first_item().to_owned(), info);
                }
                LookupKey::PathChoices(paths) => {
                    for path in paths {
                        self.add_path(path, info);
                    }
                }
            }
        }
    }

    pub fn add_field(&mut self, key: PathItemString, info: LookupFieldInfo) {
        add_field_to_map(&mut self.inner, key, info);
    }

    pub fn add_path(&mut self, path: &LookupPath, info: LookupFieldInfo) {
        add_path_to_map(&mut self.inner, path, info);
    }
}

#[derive(Debug, Clone, Copy)]
pub struct LookupFieldInfo {
    pub field_index: usize,
    pub field_lookup_type: LookupType,
}

#[derive(Debug)]
pub enum LookupTreeNode {
    /// This lookup hits an actual field
    Field(LookupFieldInfo),
    /// This lookup might applicable to multiple fields
    Complex {
        /// All fields which wanted _exactly_ this key
        fields: Vec<LookupFieldInfo>,
        /// Fields which use this key as path prefix
        lookup_map: LookupMap,
    },
}

#[derive(Debug)]
pub struct LookupMap {
    /// For lookups by name, e.g. `['foo', 'bar']`
    pub map: AHashMap<PathItemString, LookupTreeNode>,
    /// For lookups by integer index, e.g. `['foo', 0]`
    pub list: AHashMap<i64, LookupTreeNode>,
}

fn add_field_to_map<K: Hash + Eq>(map: &mut AHashMap<K, LookupTreeNode>, key: K, info: LookupFieldInfo) {
    match map.entry(key) {
        Entry::Occupied(mut entry) => match entry.get_mut() {
            &mut LookupTreeNode::Field(existing) => {
                entry.insert(LookupTreeNode::Complex {
                    fields: vec![existing, info],
                    lookup_map: LookupMap {
                        map: AHashMap::new(),
                        list: AHashMap::new(),
                    },
                });
            }
            LookupTreeNode::Complex { fields, .. } => {
                fields.push(info);
            }
        },
        Entry::Vacant(entry) => {
            entry.insert(LookupTreeNode::Field(info));
        }
    }
}

fn add_path_to_map(map: &mut AHashMap<PathItemString, LookupTreeNode>, path: &LookupPath, info: LookupFieldInfo) {
    if path.rest().is_empty() {
        // terminal value
        add_field_to_map(map, path.first_item().to_owned(), info);
        return;
    }

    let mut nested_map = match map.entry(path.first_item().to_owned()) {
        Entry::Occupied(entry) => {
            let entry = entry.into_mut();
            match entry {
                &mut LookupTreeNode::Field(i) => {
                    *entry = LookupTreeNode::Complex {
                        fields: vec![i],
                        lookup_map: LookupMap {
                            map: AHashMap::new(),
                            list: AHashMap::new(),
                        },
                    };
                    match entry {
                        LookupTreeNode::Complex {
                            lookup_map: nested_map, ..
                        } => nested_map,
                        LookupTreeNode::Field(_) => unreachable!("just created complex"),
                    }
                }
                LookupTreeNode::Complex {
                    lookup_map: nested_map, ..
                } => nested_map,
            }
        }
        Entry::Vacant(entry) => {
            let LookupTreeNode::Complex {
                lookup_map: nested_map, ..
            } = entry.insert(LookupTreeNode::Complex {
                fields: Vec::new(),
                lookup_map: LookupMap {
                    map: AHashMap::new(),
                    list: AHashMap::new(),
                },
            })
            else {
                unreachable!()
            };
            nested_map
        }
    };

    let mut path_iter = path.rest().iter();

    let mut current = path_iter.next().expect("rest is non-empty");

    for next in path_iter {
        nested_map = match current {
            PathItem::S(s) => {
                let str_key = s.clone();
                match nested_map.map.entry(str_key) {
                    Entry::Occupied(entry) => {
                        let entry = entry.into_mut();
                        match entry {
                            &mut LookupTreeNode::Field(i) => {
                                *entry = LookupTreeNode::Complex {
                                    fields: vec![i],
                                    lookup_map: LookupMap {
                                        map: AHashMap::new(),
                                        list: AHashMap::new(),
                                    },
                                };
                                let LookupTreeNode::Complex {
                                    lookup_map: nested_map, ..
                                } = entry
                                else {
                                    unreachable!()
                                };
                                nested_map
                            }
                            LookupTreeNode::Complex {
                                lookup_map: nested_map, ..
                            } => nested_map,
                        }
                    }
                    Entry::Vacant(entry) => {
                        let LookupTreeNode::Complex {
                            lookup_map: nested_map, ..
                        } = entry.insert(LookupTreeNode::Complex {
                            fields: vec![],
                            lookup_map: LookupMap {
                                map: AHashMap::new(),
                                list: AHashMap::new(),
                            },
                        })
                        else {
                            unreachable!()
                        };
                        nested_map
                    }
                }
            }
            PathItem::Pos(i) => match nested_map.list.entry(*i as i64) {
                Entry::Occupied(entry) => {
                    let entry = entry.into_mut();
                    match entry {
                        &mut LookupTreeNode::Field(i) => {
                            *entry = LookupTreeNode::Complex {
                                fields: vec![i],
                                lookup_map: LookupMap {
                                    map: AHashMap::new(),
                                    list: AHashMap::new(),
                                },
                            };
                            let LookupTreeNode::Complex {
                                lookup_map: nested_map, ..
                            } = entry
                            else {
                                unreachable!()
                            };
                            nested_map
                        }
                        LookupTreeNode::Complex {
                            lookup_map: nested_map, ..
                        } => nested_map,
                    }
                }
                Entry::Vacant(entry) => {
                    let LookupTreeNode::Complex {
                        lookup_map: nested_map, ..
                    } = entry.insert(LookupTreeNode::Complex {
                        fields: vec![],
                        lookup_map: LookupMap {
                            map: AHashMap::new(),
                            list: AHashMap::new(),
                        },
                    })
                    else {
                        unreachable!()
                    };
                    nested_map
                }
            },
            PathItem::Neg(i) => match nested_map.list.entry(-(*i as i64)) {
                Entry::Occupied(entry) => {
                    let entry = entry.into_mut();
                    match entry {
                        &mut LookupTreeNode::Field(i) => {
                            *entry = LookupTreeNode::Complex {
                                fields: vec![i],
                                lookup_map: LookupMap {
                                    map: AHashMap::new(),
                                    list: AHashMap::new(),
                                },
                            };
                            let LookupTreeNode::Complex {
                                lookup_map: nested_map, ..
                            } = entry
                            else {
                                unreachable!()
                            };
                            nested_map
                        }
                        LookupTreeNode::Complex {
                            lookup_map: nested_map, ..
                        } => nested_map,
                    }
                }
                Entry::Vacant(entry) => {
                    let LookupTreeNode::Complex {
                        lookup_map: nested_map, ..
                    } = entry.insert(LookupTreeNode::Complex {
                        fields: vec![],
                        lookup_map: LookupMap {
                            map: AHashMap::new(),
                            list: AHashMap::new(),
                        },
                    })
                    else {
                        unreachable!()
                    };
                    nested_map
                }
            },
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
