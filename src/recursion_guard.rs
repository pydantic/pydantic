use ahash::AHashSet;

/// This is used to avoid cyclic references in input data causing recursive validation and a nasty segmentation fault.
/// It's used in `validators/definition` to detect when a reference is reused within itself.
#[derive(Debug, Clone, Default)]
pub struct RecursionGuard {
    ids: Option<AHashSet<usize>>,
    // see validators/definition::BACKUP_GUARD_LIMIT for details
    // depth could be a hashmap {validator_id => depth} but for simplicity and performance it's easier to just
    // use one number for all validators
    depth: u16,
}

impl RecursionGuard {
    // insert a new id into the set, return whether the set already had the id in it
    pub fn contains_or_insert(&mut self, id: usize) -> bool {
        match self.ids {
            // https://doc.rust-lang.org/std/collections/struct.HashSet.html#method.insert
            // "If the set did not have this value present, `true` is returned."
            Some(ref mut set) => !set.insert(id),
            None => {
                let mut set: AHashSet<usize> = AHashSet::with_capacity(10);
                set.insert(id);
                self.ids = Some(set);
                false
            }
        }
    }

    // see #143 this is used as a backup in case the identity check recursion guard fails
    pub fn incr_depth(&mut self) -> u16 {
        self.depth += 1;
        self.depth
    }

    pub fn decr_depth(&mut self) {
        self.depth -= 1;
    }

    pub fn remove(&mut self, id: &usize) {
        match self.ids {
            Some(ref mut set) => {
                set.remove(id);
            }
            None => unreachable!(),
        };
    }
}
