use ahash::AHashSet;
use pyo3::PyResult;

use crate::build_tools::ExtraBehavior;
use crate::errors::{ErrorTypeDefaults, LocItem, ValError, ValResult};
use crate::input::EitherString;
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

    /// Lookup a field by its `index` and `paths`. The implementation can select which indexing
    /// is more efficient for the underlying data structure.
    ///
    /// Consuming a field via `lookup` should mark it as used so that it is not included in the extras.
    fn lookup(&mut self, index: usize, paths: &'a FieldLookupPaths) -> LookupResult<'a, Self::Item>;

    /// Call this to consume the remaining prepared results and apply `f` to any extras not mapped to
    /// fields or already consumed by `lookup`.
    ///
    /// `f` will be called with the extra field value or a `ValResult` if extraction of the extra failed
    /// (e.g. key not a string).
    ///
    /// `PyResult<()>` is returned to allow for early exit on ~fatal error; callers should ideally be
    /// collecting errors as a side-effect of `f`.
    fn for_each_extra(
        self,
        f: impl FnMut(ValResult<ExtraField<'a, 'py, Self::Key, Self::Item>>) -> PyResult<()>,
    ) -> PyResult<()>;
}

/// Extra field not mapped to a field in the model
pub struct ExtraField<'a, 'py, K, V> {
    /// The raw key (as in the native input type)
    pub raw_key: K,
    /// The raw key extracted as a string
    pub key_str: EitherString<'a, 'py>,
    /// The value of the extra field
    pub value: V,
}

struct ForEachExtra<F>(F);

impl<K, V, F: FnMut(ValResult<(K, V)>) -> PyResult<()>> ConsumeIterator<ValResult<(K, V)>> for ForEachExtra<F> {
    type Output = PyResult<()>;

    fn consume_iterator(mut self, mut iterator: impl Iterator<Item = ValResult<(K, V)>>) -> Self::Output {
        iterator.try_for_each(&mut self.0)
    }
}

/// Lazy implementation of `PreparedFieldResults` that uses a lookup function `L` to retrieve fields on demand,
/// and tracks used keys to avoid including them in extras.
pub(crate) struct LazyFieldResults<'a, L, E> {
    lookup: L,
    extras: Option<E>,
    // If tracking extras, we lazily mark consumed keys to avoid including
    // them in extras
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

    fn for_each_extra(
        self,
        mut f: impl FnMut(ValResult<ExtraField<'a, 'py, Self::Key, Self::Item>>) -> PyResult<()>,
    ) -> PyResult<()> {
        let Some(extras) = self.extras else {
            return Ok(());
        };
        extras.for_each_extra(|item| {
            let (raw_key, value) = match item {
                Ok(item) => item,
                Err(err) => return f(Err(err)),
            };
            let key_str = match raw_key
                .borrow_input()
                .validate_str(true, false)
                .map(ValidationMatch::into_inner)
            {
                Ok(key) => key,
                Err(ValError::LineErrors(line_errors)) => {
                    return f(Err(ValError::LineErrors(
                        line_errors
                            .into_iter()
                            .map(|err| {
                                err.with_outer_location(raw_key.clone())
                                    .with_type(ErrorTypeDefaults::InvalidKey)
                            })
                            .collect(),
                    )));
                }
                Err(err) => return f(Err(err)),
            };
            let is_used = match key_str.as_cow() {
                Ok(key) => self
                    .used_keys
                    .as_ref()
                    .is_some_and(|used_keys| used_keys.contains(key.as_ref())),
                Err(err) => return f(Err(err)),
            };
            if is_used {
                return Ok(());
            }
            let key_str = match key_str {
                EitherString::Cow(key) => EitherString::from(key.into_owned()),
                EitherString::Py(key) => EitherString::Py(key),
            };
            f(Ok(ExtraField {
                raw_key,
                key_str,
                value,
            }))
        })
    }
}

pub(crate) trait ExtraInput<'py> {
    type Key: BorrowInput<'py> + Clone + Into<LocItem>;
    type Item: BorrowInput<'py>;

    fn for_each_extra(self, f: impl FnMut(ValResult<(Self::Key, Self::Item)>) -> PyResult<()>) -> PyResult<()>;
}

pub(crate) struct DictExtras<'a, T: ?Sized>(pub &'a T);

impl<'a, 'py, T: ValidatedDict<'py> + ?Sized> ExtraInput<'py> for DictExtras<'a, T> {
    type Key = T::Key<'a>;
    type Item = T::Item<'a>;

    fn for_each_extra(self, mut f: impl FnMut(ValResult<(Self::Key, Self::Item)>) -> PyResult<()>) -> PyResult<()> {
        match self.0.iterate(ForEachExtra(&mut f)) {
            Ok(result) => result,
            Err(ValError::InternalErr(err)) => Err(err),
            Err(err) => f(Err(err)),
        }
    }
}

pub(crate) struct KwargsExtras<'a, T: ?Sized>(pub &'a T);

impl<'a, 'py, T: KeywordArgs<'py> + ?Sized> ExtraInput<'py> for KwargsExtras<'a, T> {
    type Key = T::Key<'a>;
    type Item = T::Item<'a>;

    fn for_each_extra(self, f: impl FnMut(ValResult<(Self::Key, Self::Item)>) -> PyResult<()>) -> PyResult<()> {
        ForEachExtra(f).consume_iterator(self.0.iter())
    }
}
