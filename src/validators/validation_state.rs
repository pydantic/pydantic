use crate::recursion_guard::{ContainsRecursionState, RecursionState};

use super::Extra;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Ord, PartialOrd, Hash)]
pub enum Exactness {
    Lax,
    Strict,
    Exact,
}

pub struct ValidationState<'a, 'py> {
    pub recursion_guard: &'a mut RecursionState,
    pub exactness: Option<Exactness>,
    // deliberately make Extra readonly
    extra: Extra<'a, 'py>,
}

impl<'a, 'py> ValidationState<'a, 'py> {
    pub fn new(extra: Extra<'a, 'py>, recursion_guard: &'a mut RecursionState) -> Self {
        Self {
            recursion_guard, // Don't care about exactness unless doing union validation
            exactness: None,
            extra,
        }
    }

    /// Temporarily rebinds the extra field by calling `f` to modify extra.
    ///
    /// When `ValidationStateWithReboundExtra` drops, the extra field is restored to its original value.
    pub fn rebind_extra<'state>(
        &'state mut self,
        f: impl FnOnce(&mut Extra<'a, 'py>),
    ) -> ValidationStateWithReboundExtra<'state, 'a, 'py> {
        let old_extra = self.extra.clone();
        f(&mut self.extra);
        ValidationStateWithReboundExtra { state: self, old_extra }
    }

    pub fn extra(&self) -> &'_ Extra<'a, 'py> {
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

impl ContainsRecursionState for ValidationState<'_, '_> {
    fn access_recursion_state<R>(&mut self, f: impl FnOnce(&mut RecursionState) -> R) -> R {
        f(self.recursion_guard)
    }
}

pub struct ValidationStateWithReboundExtra<'state, 'a, 'py> {
    state: &'state mut ValidationState<'a, 'py>,
    old_extra: Extra<'a, 'py>,
}

impl<'a, 'py> std::ops::Deref for ValidationStateWithReboundExtra<'_, 'a, 'py> {
    type Target = ValidationState<'a, 'py>;

    fn deref(&self) -> &Self::Target {
        self.state
    }
}

impl std::ops::DerefMut for ValidationStateWithReboundExtra<'_, '_, '_> {
    fn deref_mut(&mut self) -> &mut Self::Target {
        self.state
    }
}

impl Drop for ValidationStateWithReboundExtra<'_, '_, '_> {
    fn drop(&mut self) {
        std::mem::swap(&mut self.state.extra, &mut self.old_extra);
    }
}
