use std::borrow::Borrow;
use std::cell::RefCell;
use std::cmp::{Eq, PartialEq};
use std::fmt::Debug;
use std::hash::Hash;
use std::slice::Iter as SliceIter;

use ahash::AHashMap;

#[derive(Debug, Clone, Default)]
pub struct LazyIndexMap<K, V> {
    vec: Vec<(K, V)>,
    map: RefCell<Option<AHashMap<K, usize>>>,
}

/// Like [IndexMap](https://docs.rs/indexmap/latest/indexmap/) but only builds the lookup map when it's needed.
impl<K, V> LazyIndexMap<K, V>
where
    K: Clone + Debug + Eq + Hash,
    V: Clone + Debug,
{
    pub fn new() -> Self {
        Self {
            vec: Vec::new(),
            map: RefCell::new(None),
        }
    }

    pub fn insert(&mut self, key: K, value: V) {
        self.vec.push((key, value));
    }

    pub fn len(&self) -> usize {
        self.vec.len()
    }

    pub fn get<Q: ?Sized>(&self, key: &Q) -> Option<&V>
    where
        K: Borrow<Q> + PartialEq<Q>,
        Q: Hash + Eq,
    {
        let mut map = self.map.borrow_mut();
        if let Some(map) = map.as_ref() {
            map.get(key).map(|&i| &self.vec[i].1)
        } else {
            let mut new_map = AHashMap::with_capacity(self.vec.len());
            let mut value = None;
            // reverse here so the last value is the one that's returned
            for (index, (k, v)) in self.vec.iter().enumerate().rev() {
                if value.is_none() && k == key {
                    value = Some(v);
                }
                new_map.insert(k.clone(), index);
            }
            *map = Some(new_map);
            value
        }
    }

    pub fn keys(&self) -> impl Iterator<Item = &K> {
        self.vec.iter().map(|(k, _)| k)
    }

    pub fn iter(&self) -> SliceIter<'_, (K, V)> {
        self.vec.iter()
    }
}
