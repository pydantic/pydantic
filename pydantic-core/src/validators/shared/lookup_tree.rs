use std::borrow::Cow;
use std::ops::Range;

use ahash::AHashMap;
use jiter::{JsonArray, JsonObject, JsonValue};
use smallvec::SmallVec;

use crate::lookup_key::{LookupPath, LookupPathCollection, LookupType, PathItem, PathItemString};

/// Maps JSON object keys to the lookup paths of the fields (names and aliases), so that JSON objects
/// can be validated in a single pass over their keys.
///
/// Built once from the fields, using the simplest representation they allow.
#[derive(Debug)]
pub enum LookupTree {
    /// No field has an alias: each key maps to the index of the field with that name.
    NoAliases(AHashMap<PathItemString, usize>),
    /// Some fields have aliases, but none is an `AliasPath`: each key maps to the matching lookup paths.
    ///
    /// The best match for a field can be selected as keys are seen, discarding lower-priority ones.
    Flat(FlatLookup),
    /// Some aliases are `AliasPath`s: keys map to a tree of nested object keys and array indices.
    ///
    /// All matches must be retained until the end, as a later duplicate key can replace the
    /// parent of the preferred match (e.g. `{"a": {"b": 1}, "a": 2}` with `AliasPath('a', 'b')`).
    Nested(Box<NestedLookup>),
}

impl LookupTree {
    pub fn from_fields<T>(fields: &[T], get_field_collection: impl Fn(&T) -> &LookupPathCollection) -> Self {
        if fields
            .iter()
            .all(|field| get_field_collection(field).by_alias.is_empty())
        {
            return Self::NoAliases(
                fields
                    .iter()
                    .enumerate()
                    .map(|(index, field)| (get_field_collection(field).by_name.first_item().clone(), index))
                    .collect(),
            );
        }
        let has_nested_paths = fields.iter().any(|field| {
            get_field_collection(field)
                .by_alias
                .iter()
                .any(|path| !path.rest().is_empty())
        });

        if has_nested_paths {
            let mut roots: AHashMap<PathItemString, LookupNodeBuilder> = AHashMap::with_capacity(fields.len());
            for_each_path(fields, get_field_collection, |path, info| {
                let mut node = roots.entry(path.first_item().clone()).or_default();
                for item in path.rest() {
                    node = match item {
                        PathItem::S(s) => node.map.entry(s.clone()).or_default(),
                        PathItem::Pos(i) => node.list.entry(*i as i64).or_default(),
                        PathItem::Neg(i) => node.list.entry(-(*i as i64)).or_default(),
                    };
                }
                node.fields.push(info);
            });
            let mut paths = Vec::new();
            let mut branch_count = 0;
            let inner = roots
                .into_iter()
                .map(|(key, node)| (key, node.build(&mut paths, &mut branch_count)))
                .collect();
            Self::Nested(Box::new(NestedLookup {
                inner,
                paths,
                branch_count,
            }))
        } else {
            let mut inner: AHashMap<PathItemString, SmallVec<[LookupFieldInfo; 1]>> =
                AHashMap::with_capacity(fields.len());
            for_each_path(fields, get_field_collection, |path, info| {
                inner.entry(path.first_item().clone()).or_default().push(info);
            });
            Self::Flat(FlatLookup { inner })
        }
    }
}

fn for_each_path<T>(
    fields: &[T],
    get_field_collection: impl Fn(&T) -> &LookupPathCollection,
    mut f: impl FnMut(&LookupPath, LookupFieldInfo),
) {
    for (field_index, field) in fields.iter().enumerate() {
        let collection = get_field_collection(field);
        f(
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
        for (alias_index, path) in collection.by_alias.iter().enumerate() {
            f(
                path,
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
}

#[derive(Debug)]
pub struct FlatLookup {
    inner: AHashMap<PathItemString, SmallVec<[LookupFieldInfo; 1]>>,
}

impl FlatLookup {
    pub fn get(&self, key: &str) -> &[LookupFieldInfo] {
        self.inner.get(key).map_or(&[], |fields| fields.as_slice())
    }
}

/// The priority of a lookup path of a field, i.e. whether it is the field name or one of its aliases (and which one).
///
/// When multiple lookup paths of the same field match the input, this is used to decide which input to use:
/// aliases are preferred over names, and earlier aliases are preferred over later ones.
///
/// For example, with the following field:
///
/// ```python
/// a: int = Field(validation_alias=AliasChoices('b', 'c'))
/// ```
///
/// `2` is used, as `b` comes before `c` in the alias choices (regardless of the input order):
///
/// ```json
/// {"c": 1, "b": 2}
/// ```
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct LookupFieldPriority {
    /// The kind of lookup this path is used for.
    lookup_type: LookupType,
    /// The index of this path within the field's aliases (e.g. `1` for `c` in `AliasChoices('b', 'c')`).
    ///
    /// Lower is higher priority. Only meaningful when `lookup_type` is `Alias`, `0` otherwise.
    alias_index: usize,
}

impl LookupFieldPriority {
    pub fn is_higher_priority_than(&self, other: &Self) -> bool {
        if self.lookup_type == LookupType::Name {
            false
        } else if other.lookup_type == LookupType::Name {
            true
        } else {
            self.alias_index < other.alias_index
        }
    }

    pub fn is_maximum_priority_for_lookup_type(&self, lookup_type: LookupType) -> bool {
        #[expect(clippy::match_same_arms, reason = "clearer to separate invalid from name/both case")]
        match (self.lookup_type, lookup_type) {
            (LookupType::Both, _) | (LookupType::Name, LookupType::Name) => true,
            (LookupType::Alias, LookupType::Alias | LookupType::Both) => self.alias_index == 0,
            (LookupType::Name, LookupType::Alias) | (LookupType::Alias, LookupType::Name) => false,
            (LookupType::Name, LookupType::Both) => false,
        }
    }
}

/// A lookup path of a field, as stored in the lookup tree.
#[derive(Debug, Clone, Copy)]
pub struct LookupFieldInfo {
    /// The index (in the `fields` of the schema) of the field this lookup path belongs to.
    ///
    /// For example, both the `b` and `c` paths have index `1` in the following model:
    ///
    /// ```python
    /// class Model(BaseModel):
    ///     a: int
    ///     b: int = Field(alias='c')
    /// ```
    pub field_index: usize,
    /// The priority of this path among the field's other lookup paths.
    pub lookup_priority: LookupFieldPriority,
}

impl LookupFieldInfo {
    pub fn by_name(field_index: usize) -> Self {
        Self {
            field_index,
            lookup_priority: LookupFieldPriority {
                lookup_type: LookupType::Both,
                alias_index: 0,
            },
        }
    }

    pub fn matches_lookup(&self, lookup_type: LookupType) -> bool {
        self.lookup_priority.lookup_type.matches(lookup_type)
    }

    pub fn alias_index(&self) -> Option<usize> {
        if self.lookup_priority.lookup_type == LookupType::Alias {
            Some(self.lookup_priority.alias_index)
        } else {
            None
        }
    }
}

/// Offer `value` as the input for the field of `info`, keeping it only if it matches `lookup_type`
/// and the field doesn't already have a higher priority input. Returns whether it was kept.
pub fn offer_field_input<'a, 'j>(
    field_inputs: &mut [Option<(LookupFieldInfo, &'a JsonValue<'j>)>],
    info: &LookupFieldInfo,
    value: &'a JsonValue<'j>,
    lookup_type: LookupType,
) -> bool {
    if !info.matches_lookup(lookup_type) {
        return false;
    }
    let field_input = &mut field_inputs[info.field_index];
    if let Some((existing, _)) = field_input
        && existing.lookup_priority.is_higher_priority_than(&info.lookup_priority)
    {
        return false;
    }
    *field_input = Some((*info, value));
    true
}

#[derive(Default)]
struct LookupNodeBuilder {
    fields: SmallVec<[LookupFieldInfo; 1]>,
    map: AHashMap<PathItemString, LookupNodeBuilder>,
    list: AHashMap<i64, LookupNodeBuilder>,
}

impl LookupNodeBuilder {
    fn build(self, paths: &mut Vec<LookupFieldInfo>, branch_count: &mut usize) -> NestedLookupNode {
        let branch_start = *branch_count;
        if !self.map.is_empty() || !self.list.is_empty() {
            *branch_count += 1;
        }
        let start = paths.len();
        paths.extend(self.fields);
        let fields = start..paths.len();
        let map = self
            .map
            .into_iter()
            .map(|(key, node)| (key, node.build(paths, branch_count)))
            .collect();
        let list = self
            .list
            .into_iter()
            .map(|(key, node)| (key, node.build(paths, branch_count)))
            .collect();
        NestedLookupNode {
            fields,
            subtree_end: paths.len(),
            branches: branch_start..*branch_count,
            map,
            list,
        }
    }
}

#[derive(Debug)]
pub struct NestedLookup {
    inner: AHashMap<PathItemString, NestedLookupNode>,
    paths: Vec<LookupFieldInfo>,
    branch_count: usize,
}

impl NestedLookup {
    pub fn collect_json<'a, 'j>(
        &self,
        object: &'a JsonObject<'j>,
        lookup_type: LookupType,
        field_inputs: &mut [Option<(LookupFieldInfo, &'a JsonValue<'j>)>],
        mut record_extra: impl FnMut(&'a str, &'a JsonValue<'j>),
    ) {
        let mut candidates = vec![None; self.paths.len()];
        let mut visited = SmallVec::<[u64; 1]>::new();
        visited.resize(self.branch_count.div_ceil(64), 0);
        let mut stack = SmallVec::<[NestedFrame<'_, '_, '_>; 1]>::new();

        for (key, value) in &**object {
            record_extra(key.as_ref(), value);
            let Some(node) = self.inner.get(key.as_ref()) else {
                continue;
            };
            stack.push(node.enter(value, &mut candidates, &mut visited));
            while let Some(frame) = stack.last_mut() {
                let next = match &mut frame.state {
                    FrameState::Object(iter) => {
                        iter.find_map(|(key, value)| frame.node.map.get(key.as_ref()).map(|node| (node, value)))
                    }
                    FrameState::Array { iter, array } => iter.find_map(|(index, node)| {
                        let index = if *index < 0 { index + array.len() as i64 } else { *index };
                        array.get(index as usize).map(|value| (node, value))
                    }),
                    FrameState::Done => None,
                };
                if let Some((node, value)) = next {
                    stack.push(node.enter(value, &mut candidates, &mut visited));
                } else {
                    stack.pop();
                }
            }
        }

        for (info, value) in self.paths.iter().zip(candidates) {
            if let Some(value) = value {
                offer_field_input(field_inputs, info, value, lookup_type);
            }
        }
    }
}

#[derive(Debug)]
struct NestedLookupNode {
    // Paths and internal nodes are numbered depth-first, so invalidation needs no descendant lists.
    fields: Range<usize>,
    subtree_end: usize,
    // Empty for leaves; otherwise the first bit represents this node, followed by its descendants.
    branches: Range<usize>,
    map: AHashMap<PathItemString, NestedLookupNode>,
    list: AHashMap<i64, NestedLookupNode>,
}

impl NestedLookupNode {
    fn enter<'s, 'a, 'j>(
        &'s self,
        value: &'a JsonValue<'j>,
        candidates: &mut [Option<&'a JsonValue<'j>>],
        visited: &mut [u64],
    ) -> NestedFrame<'s, 'a, 'j> {
        if !self.branches.is_empty() {
            let index = self.branches.start;
            let mask = 1 << (index % 64);
            if visited[index / 64] & mask != 0 {
                // Replacement invalidates descendants even if the new value has no matching paths.
                candidates[self.fields.start..self.subtree_end].fill(None);
                for index in self.branches.clone() {
                    visited[index / 64] &= !(1 << (index % 64));
                }
            }
            visited[index / 64] |= mask;
        }
        candidates[self.fields.clone()].fill(Some(value));
        let state = match value {
            JsonValue::Object(object) if !self.map.is_empty() => FrameState::Object(object.iter()),
            JsonValue::Array(array) if !self.list.is_empty() => FrameState::Array {
                iter: self.list.iter(),
                array,
            },
            _ => FrameState::Done,
        };
        NestedFrame { node: self, state }
    }
}

struct NestedFrame<'s, 'a, 'j> {
    node: &'s NestedLookupNode,
    state: FrameState<'s, 'a, 'j>,
}

enum FrameState<'s, 'a, 'j> {
    Object(std::slice::Iter<'a, (Cow<'j, str>, JsonValue<'j>)>),
    Array {
        iter: std::collections::hash_map::Iter<'s, i64, NestedLookupNode>,
        array: &'a JsonArray<'j>,
    },
    Done,
}
