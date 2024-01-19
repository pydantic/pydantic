use ahash::AHashSet;
use std::mem::MaybeUninit;

type RecursionKey = (
    // Identifier for the input object, e.g. the id() of a Python dict
    usize,
    // Identifier for the node we are traversing, e.g. the validator's id
    // Generally only things that can be traversed multiple times, like a definition reference
    // need to use the recursion guard, and those things should already have a natural node id
    usize,
);

/// This is used to avoid cyclic references in input data causing recursive validation and a nasty segmentation fault.
/// It's used in `validators/definition` to detect when a reference is reused within itself.
pub(crate) struct RecursionGuard<'a, S: ContainsRecursionState> {
    state: &'a mut S,
    obj_id: usize,
    node_id: usize,
}

pub(crate) enum RecursionError {
    /// Cyclic reference detected
    Cyclic,
    /// Recursion limit exceeded
    Depth,
}

impl<S: ContainsRecursionState> RecursionGuard<'_, S> {
    /// Creates a recursion guard for the given object and node id.
    ///
    /// When dropped, this will release the recursion for the given object and node id.
    pub fn new(state: &'_ mut S, obj_id: usize, node_id: usize) -> Result<RecursionGuard<'_, S>, RecursionError> {
        state.access_recursion_state(|state| {
            if !state.insert(obj_id, node_id) {
                return Err(RecursionError::Cyclic);
            }
            if state.incr_depth() {
                return Err(RecursionError::Depth);
            }
            Ok(())
        })?;
        Ok(RecursionGuard { state, obj_id, node_id })
    }

    /// Retrieves the underlying state for further use.
    pub fn state(&mut self) -> &mut S {
        self.state
    }
}

impl<S: ContainsRecursionState> Drop for RecursionGuard<'_, S> {
    fn drop(&mut self) {
        self.state.access_recursion_state(|state| {
            state.decr_depth();
            state.remove(self.obj_id, self.node_id);
        });
    }
}

/// This trait is used to retrieve the recursion state from some other type
pub(crate) trait ContainsRecursionState {
    fn access_recursion_state<R>(&mut self, f: impl FnOnce(&mut RecursionState) -> R) -> R;
}

/// State for the RecursionGuard. Can also be used directly to increase / decrease depth.
#[derive(Debug, Clone, Default)]
pub struct RecursionState {
    ids: RecursionStack,
    // depth could be a hashmap {validator_id => depth} but for simplicity and performance it's easier to just
    // use one number for all validators
    depth: u8,
}

// A hard limit to avoid stack overflows when rampant recursion occurs
pub const RECURSION_GUARD_LIMIT: u8 = if cfg!(any(target_family = "wasm", all(windows, PyPy))) {
    // wasm and windows PyPy have very limited stack sizes
    49
} else if cfg!(any(PyPy, windows)) {
    // PyPy and Windows in general have more restricted stack space
    99
} else {
    255
};

impl RecursionState {
    // insert a new value
    // * return `false` if the stack already had it in it
    // * return `true` if the stack didn't have it in it and it was inserted
    fn insert(&mut self, obj_id: usize, node_id: usize) -> bool {
        self.ids.insert((obj_id, node_id))
    }

    // see #143 this is used as a backup in case the identity check recursion guard fails
    #[must_use]
    #[cfg(any(target_family = "wasm", windows, PyPy))]
    pub fn incr_depth(&mut self) -> bool {
        // use saturating_add as it's faster (since there's no error path)
        // and the RECURSION_GUARD_LIMIT check will be hit before it overflows
        debug_assert!(RECURSION_GUARD_LIMIT < 255);
        self.depth = self.depth.saturating_add(1);
        self.depth > RECURSION_GUARD_LIMIT
    }

    #[must_use]
    #[cfg(not(any(target_family = "wasm", windows, PyPy)))]
    pub fn incr_depth(&mut self) -> bool {
        debug_assert_eq!(RECURSION_GUARD_LIMIT, 255);
        // use checked_add to check if we've hit the limit
        if let Some(depth) = self.depth.checked_add(1) {
            self.depth = depth;
            false
        } else {
            true
        }
    }

    pub fn decr_depth(&mut self) {
        // for the same reason as incr_depth, use saturating_sub
        self.depth = self.depth.saturating_sub(1);
    }

    fn remove(&mut self, obj_id: usize, node_id: usize) {
        self.ids.remove(&(obj_id, node_id));
    }
}

// trial and error suggests this is a good value, going higher causes array lookups to get significantly slower
const ARRAY_SIZE: usize = 16;

#[derive(Debug, Clone)]
enum RecursionStack {
    Array {
        data: [MaybeUninit<RecursionKey>; ARRAY_SIZE],
        len: usize,
    },
    Set(AHashSet<RecursionKey>),
}

impl Default for RecursionStack {
    fn default() -> Self {
        Self::Array {
            data: std::array::from_fn(|_| MaybeUninit::uninit()),
            len: 0,
        }
    }
}

impl RecursionStack {
    // insert a new value
    // * return `false` if the stack already had it in it
    // * return `true` if the stack didn't have it in it and it was inserted
    fn insert(&mut self, v: RecursionKey) -> bool {
        match self {
            Self::Array { data, len } => {
                if *len < ARRAY_SIZE {
                    for value in data.iter().take(*len) {
                        // Safety: reading values within bounds
                        if unsafe { value.assume_init() } == v {
                            return false;
                        }
                    }

                    data[*len].write(v);
                    *len += 1;
                    true
                } else {
                    let mut set = AHashSet::with_capacity(ARRAY_SIZE + 1);
                    for existing in data.iter() {
                        // Safety: the array is fully initialized
                        set.insert(unsafe { existing.assume_init() });
                    }
                    let inserted = set.insert(v);
                    *self = Self::Set(set);
                    inserted
                }
            }
            // https://doc.rust-lang.org/std/collections/struct.HashSet.html#method.insert
            // "If the set did not have this value present, `true` is returned."
            Self::Set(set) => set.insert(v),
        }
    }

    fn remove(&mut self, v: &RecursionKey) {
        match self {
            Self::Array { data, len } => {
                *len = len.checked_sub(1).expect("remove from empty recursion guard");
                // Safety: this is reading what was the back of the initialized array
                let removed = unsafe { data.get_unchecked_mut(*len) };
                assert!(unsafe { removed.assume_init_ref() } == v, "remove did not match insert");
                // this should compile away to a noop
                unsafe { std::ptr::drop_in_place(removed.as_mut_ptr()) }
            }
            Self::Set(set) => {
                set.remove(v);
            }
        }
    }
}

impl Drop for RecursionStack {
    fn drop(&mut self) {
        // This should compile away to a noop as Recursion>Key doesn't implement Drop, but it seemed
        // desirable to leave this in for safety in case that should change in the future
        if let Self::Array { data, len } = self {
            for value in data.iter_mut().take(*len) {
                // Safety: reading values within bounds
                unsafe { std::ptr::drop_in_place(value.as_mut_ptr()) };
            }
        }
    }
}
