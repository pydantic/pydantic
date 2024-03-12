use crate::recursion_guard::{ContainsRecursionState, RecursionState};

use super::Extra;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Ord, PartialOrd, Hash)]
pub enum Exactness {
    Lax,
    Strict,
    Exact,
}

pub struct ValidationState<'a> {
    pub recursion_guard: &'a mut RecursionState,
    pub exactness: Option<Exactness>,
    // deliberately make Extra readonly
    extra: Extra<'a>,
}

impl<'a> ValidationState<'a> {
    pub fn new(extra: Extra<'a>, recursion_guard: &'a mut RecursionState) -> Self {
        Self {
            recursion_guard, // Don't care about exactness unless doing union validation
            exactness: None,
            extra,
        }
    }

    pub fn with_new_extra<'r, R: 'r>(
        &mut self,
        extra: Extra<'_>,
        f: impl for<'s> FnOnce(&'s mut ValidationState<'_>) -> R,
    ) -> R {
        // TODO: It would be nice to implement this function with a drop guard instead of a closure,
        // but lifetimes get in a tangle. Maybe someone brave wants to have a go at unpicking lifetimes.
        let mut new_state = ValidationState {
            recursion_guard: self.recursion_guard,
            exactness: self.exactness,
            extra,
        };
        let result = f(&mut new_state);
        let exactness = new_state.exactness;
        drop(new_state);
        match exactness {
            Some(exactness) => self.floor_exactness(exactness),
            None => self.exactness = None,
        }
        result
    }

    /// Temporarily rebinds the extra field by calling `f` to modify extra.
    ///
    /// When `ValidationStateWithReboundExtra` drops, the extra field is restored to its original value.
    pub fn rebind_extra<'state>(
        &'state mut self,
        f: impl FnOnce(&mut Extra<'a>),
    ) -> ValidationStateWithReboundExtra<'state, 'a> {
        #[allow(clippy::unnecessary_struct_initialization)]
        let old_extra = Extra {
            data: self.extra.data.clone(),
            ..self.extra
        };
        f(&mut self.extra);
        ValidationStateWithReboundExtra { state: self, old_extra }
    }

    pub fn extra(&self) -> &'_ Extra<'a> {
        &self.extra
    }

    pub fn strict_or(&self, default: bool) -> bool {
        self.extra.strict.unwrap_or(default)
    }

    /// Sets the exactness to the lower of the current exactness
    /// and the given exactness.
    ///
    /// This is designed to be used in union validation, where the
    /// idea is that the "most exact" validation wins.
    pub fn floor_exactness(&mut self, exactness: Exactness) {
        match self.exactness {
            None | Some(Exactness::Lax) => {}
            Some(Exactness::Strict) => {
                if exactness == Exactness::Lax {
                    self.exactness = Some(Exactness::Lax);
                }
            }
            Some(Exactness::Exact) => self.exactness = Some(exactness),
        }
    }
}

impl ContainsRecursionState for ValidationState<'_> {
    fn access_recursion_state<R>(&mut self, f: impl FnOnce(&mut RecursionState) -> R) -> R {
        f(self.recursion_guard)
    }
}

pub struct ValidationStateWithReboundExtra<'state, 'a> {
    state: &'state mut ValidationState<'a>,
    old_extra: Extra<'a>,
}

impl<'a> std::ops::Deref for ValidationStateWithReboundExtra<'_, 'a> {
    type Target = ValidationState<'a>;

    fn deref(&self) -> &Self::Target {
        self.state
    }
}

impl<'a> std::ops::DerefMut for ValidationStateWithReboundExtra<'_, 'a> {
    fn deref_mut(&mut self) -> &mut Self::Target {
        self.state
    }
}

impl Drop for ValidationStateWithReboundExtra<'_, '_> {
    fn drop(&mut self) {
        std::mem::swap(&mut self.state.extra, &mut self.old_extra);
    }
}
