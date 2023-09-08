use std::borrow::Borrow;
use std::cmp::{Eq, PartialEq};
use std::fmt::Debug;
use std::hash::Hash;
use std::slice::Iter as SliceIter;
use std::sync::OnceLock;

use ahash::AHashMap;
use smallvec::SmallVec;

#[derive(Debug, Clone, Default)]
pub struct LazyIndexMap<K, V> {
    vec: SmallVec<[(K, V); 8]>,
    map: OnceLock<AHashMap<K, usize>>,
}

/// Like [IndexMap](https://docs.rs/indexmap/latest/indexmap/) but only builds the lookup map when it's needed.
impl<K, V> LazyIndexMap<K, V>
where
    K: Clone + Debug + Eq + Hash,
    V: Debug,
{
    pub fn new() -> Self {
        Self {
            vec: SmallVec::new(),
            map: OnceLock::new(),
        }
    }

    pub fn insert(&mut self, key: K, value: V) {
        if let Some(map) = self.map.get_mut() {
            map.insert(key.clone(), self.vec.len());
        }
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
        let map = self.map.get_or_init(|| {
            self.vec
                .iter()
                .enumerate()
                .map(|(index, (key, _))| (key.clone(), index))
                .collect()
        });
        map.get(key).map(|&i| &self.vec[i].1)
    }

    pub fn keys(&self) -> impl Iterator<Item = &K> {
        self.vec.iter().map(|(k, _)| k)
    }

    pub fn iter(&self) -> SliceIter<'_, (K, V)> {
        self.vec.iter()
    }
}
