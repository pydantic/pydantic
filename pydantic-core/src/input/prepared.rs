use ahash::AHashSet;

use crate::build_tools::ExtraBehavior;
use crate::errors::{LocItem, ValResult};
use crate::lookup_key::{FieldLookupPaths, LookupResult};

use super::{BorrowInput, ConsumeIterator, Input, KeywordArgs, ValidatedDict, ValidationMatch};

/// Represents prepared field results that can be further consumed for validation.
///
/// At present in JSON mode this is a buffer of the fields by-index, and in Python mode
/// it simply contains the input mapping with some state tracking what was looked up
/// vs remaining for extras.
pub trait PreparedFieldResults<'a, 'py> {
    type Key: BorrowInput<'py> + Clone + Into<LocItem>;
    type Item: BorrowInput<'py>;

    fn lookup(&mut self, index: usize, paths: &'a FieldLookupPaths) -> LookupResult<'a, Self::Item>;

    fn for_each_extra(self, f: impl FnMut(Self::Key, Self::Item) -> ValResult<()>) -> ValResult<()>;
}

struct ForEachExtra<F>(F);

impl<K, V, F: FnMut(K, V) -> ValResult<()>> ConsumeIterator<ValResult<(K, V)>> for ForEachExtra<F> {
    type Output = ValResult<()>;

    fn consume_iterator(mut self, mut iterator: impl Iterator<Item = ValResult<(K, V)>>) -> Self::Output {
        iterator.try_for_each(|item| {
            let (key, value) = item?;
            (self.0)(key, value)
        })
    }
}

pub(crate) struct LazyFieldResults<'a, L, E> {
    lookup: L,
    extras: Option<E>,
    used_keys: Option<AHashSet<&'a str>>,
}

impl<L, E> LazyFieldResults<'_, L, E> {
    pub fn new(lookup: L, extras: Option<E>, extra_behavior: ExtraBehavior) -> Self {
        let used_keys = (extras.is_some() && extra_behavior != ExtraBehavior::Ignore).then(AHashSet::new);
        Self {
            lookup,
            extras,
            used_keys,
        }
    }
}

impl<'a, 'py, L, E> PreparedFieldResults<'a, 'py> for LazyFieldResults<'a, L, E>
where
    E: ExtraInput<'py>,
    L: Fn(&'a FieldLookupPaths) -> LookupResult<'a, E::Item>,
{
    type Key = E::Key;
    type Item = E::Item;

    fn lookup(&mut self, _index: usize, paths: &'a FieldLookupPaths) -> LookupResult<'a, Self::Item> {
        let result = (self.lookup)(paths)?;
        if let Some((path, _)) = &result
            && let Some(used_keys) = &mut self.used_keys
        {
            used_keys.insert(path.first_key());
        }
        Ok(result)
    }

    fn for_each_extra(self, mut f: impl FnMut(Self::Key, Self::Item) -> ValResult<()>) -> ValResult<()> {
        let Some(extras) = self.extras else {
            return Ok(());
        };
        extras.for_each_extra(|raw_key, value| {
            // Invalid keys are left for the validator to report with its other errors.
            let is_used = match raw_key
                .borrow_input()
                .validate_str(true, false)
                .map(ValidationMatch::into_inner)
            {
                Ok(key) => {
                    let key = key.as_cow()?;
                    self.used_keys
                        .as_ref()
                        .is_some_and(|used_keys| used_keys.contains(key.as_ref()))
                }
                Err(_) => false,
            };
            if is_used { Ok(()) } else { f(raw_key, value) }
        })
    }
}

pub(crate) trait ExtraInput<'py> {
    type Key: BorrowInput<'py> + Clone + Into<LocItem>;
    type Item: BorrowInput<'py>;

    fn for_each_extra(self, f: impl FnMut(Self::Key, Self::Item) -> ValResult<()>) -> ValResult<()>;
}

pub(crate) struct DictExtras<'a, T: ?Sized>(pub &'a T);

impl<'a, 'py, T: ValidatedDict<'py> + ?Sized> ExtraInput<'py> for DictExtras<'a, T> {
    type Key = T::Key<'a>;
    type Item = T::Item<'a>;

    fn for_each_extra(self, f: impl FnMut(Self::Key, Self::Item) -> ValResult<()>) -> ValResult<()> {
        self.0.iterate(ForEachExtra(f))?
    }
}

pub(crate) struct KwargsExtras<'a, T: ?Sized>(pub &'a T);

impl<'a, 'py, T: KeywordArgs<'py> + ?Sized> ExtraInput<'py> for KwargsExtras<'a, T> {
    type Key = T::Key<'a>;
    type Item = T::Item<'a>;

    fn for_each_extra(self, f: impl FnMut(Self::Key, Self::Item) -> ValResult<()>) -> ValResult<()> {
        ForEachExtra(f).consume_iterator(self.0.iter())
    }
}
