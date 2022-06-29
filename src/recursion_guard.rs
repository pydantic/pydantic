use std::collections::HashSet;
use std::hash::BuildHasherDefault;

use nohash_hasher::NoHashHasher;

/// This is used to avoid cyclic references in input data causing recursive validation and a nasty segmentation fault.
/// It's used in `validators/recursive.rs` to detect when a reference is reused within itself.
#[derive(Debug, Clone, Default)]
pub struct RecursionGuard(Option<HashSet<usize, BuildHasherDefault<NoHashHasher<usize>>>>);

impl RecursionGuard {
    // insert a new id into the set, return whether the set already had the id in it
    pub fn contains_or_insert(&mut self, id: usize) -> bool {
        match self.0 {
            // https://doc.rust-lang.org/std/collections/struct.HashSet.html#method.insert
            // "If the set did not have this value present, `true` is returned."
            Some(ref mut set) => !set.insert(id),
            None => {
                let mut set: HashSet<usize, BuildHasherDefault<NoHashHasher<usize>>> =
                    HashSet::with_capacity_and_hasher(10, BuildHasherDefault::default());
                set.insert(id);
                self.0 = Some(set);
                false
            }
        }
    }

    pub fn remove(&mut self, id: &usize) {
        match self.0 {
            Some(ref mut set) => {
                set.remove(id);
            }
            None => unreachable!(),
        };
    }
}
