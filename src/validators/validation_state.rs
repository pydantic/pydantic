use crate::{definitions::Definitions, recursion_guard::RecursionGuard};

use super::{CombinedValidator, Extra};

pub struct ValidationState<'a> {
    pub recursion_guard: &'a mut RecursionGuard,
    pub definitions: &'a Definitions<CombinedValidator>,
    // deliberately make Extra readonly
    extra: Extra<'a>,
}

impl<'a> ValidationState<'a> {
    pub fn new(
        extra: Extra<'a>,
        definitions: &'a Definitions<CombinedValidator>,
        recursion_guard: &'a mut RecursionGuard,
    ) -> Self {
        Self {
            recursion_guard,
            definitions,
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
            definitions: self.definitions,
            extra,
        };
        f(&mut new_state)
    }

    pub fn extra(&self) -> &'_ Extra<'a> {
        &self.extra
    }

    pub fn strict_or(&self, default: bool) -> bool {
        self.extra.strict.unwrap_or(default)
    }
}
