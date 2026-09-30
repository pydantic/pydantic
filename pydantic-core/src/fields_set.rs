//! Implementation of `ModelFieldsSet`, the set used to track the fields explicitly set on a model instance.

use std::ops::Deref;
use std::sync::Arc;

use pyo3::exceptions::{PyKeyError, PyTypeError};
use pyo3::pyclass::CompareOp;
use pyo3::sync::PyOnceLock;
use pyo3::types::{PyFrozenSet, PyIterator, PyList, PySet, PyString, PyTuple, PyType};
use pyo3::{PyTypeInfo, ffi, intern, prelude::*, pybacked::PyBackedStr};
use smallvec::SmallVec;

/// A minimal fixed-size bitset, for up to 64 bits.
#[derive(Debug, Clone, PartialEq, Eq)]
struct BitSet(SmallVec<[u64; 1]>);

impl BitSet {
    fn with_len(len: usize) -> Self {
        Self(smallvec::smallvec![0; len.div_ceil(u64::BITS as usize)])
    }

    fn contains(&self, index: usize) -> bool {
        self.0
            .get(index / u64::BITS as usize)
            .is_some_and(|block| block & (1u64 << (index % u64::BITS as usize)) != 0)
    }

    fn insert(&mut self, index: usize) {
        self.0[index / u64::BITS as usize] |= 1u64 << (index % u64::BITS as usize);
    }

    /// Unsets the bit at `index`, returning whether it was previously set.
    fn remove(&mut self, index: usize) -> bool {
        let block = &mut self.0[index / u64::BITS as usize];
        let mask = 1u64 << (index % u64::BITS as usize);
        let was_set = *block & mask != 0;
        *block &= !mask;
        was_set
    }

    fn count_ones(&self) -> usize {
        self.0.iter().map(|block| block.count_ones() as usize).sum()
    }

    fn clear(&mut self) {
        self.0.iter_mut().for_each(|block| *block = 0);
    }
}

/// The names of the fields of a model, in definition order.
#[derive(Debug)]
// The slice is boxed so that `Arc<FieldNames>` is a thin pointer, keeping the size of
// `ModelFieldsValidator` (and thus of `CombinedValidator`) small:
pub struct FieldNames(Box<[PyBackedStr]>);

impl Deref for FieldNames {
    type Target = [PyBackedStr];

    fn deref(&self) -> &Self::Target {
        &self.0
    }
}

impl FromIterator<PyBackedStr> for FieldNames {
    fn from_iter<I: IntoIterator<Item = PyBackedStr>>(iter: I) -> Self {
        Self(iter.into_iter().collect())
    }
}

static ABC_SET: PyOnceLock<Py<PyType>> = PyOnceLock::new();

/// Whether `obj` is a set-like object, i.e. an instance of `set`, `frozenset`, `ModelFieldsSet`,
/// or a (virtual) subclass of `collections.abc.Set`.
///
/// This mirrors what the builtin `set` type accepts for its binary operators and comparisons.
fn is_set_like(obj: &Bound<'_, PyAny>) -> PyResult<bool> {
    // SAFETY: `obj` is a valid pointer to a Python object.
    if unsafe { ffi::PyAnySet_Check(obj.as_ptr()) } != 0 || obj.is_instance_of::<ModelFieldsSet>() {
        return Ok(true);
    }
    let py = obj.py();
    let abc_set = ABC_SET.get_or_try_init(py, || -> PyResult<Py<PyType>> {
        Ok(py
            .import(intern!(py, "collections.abc"))?
            .getattr(intern!(py, "Set"))?
            .cast_into::<PyType>()?
            .unbind())
    })?;
    obj.is_instance(abc_set.bind(py))
}

/// A set-like object, as accepted by the binary operators and comparison methods of `set`.
///
/// When used as a method argument, a failed extraction results in `NotImplemented` being returned.
struct SetLike<'py>(Bound<'py, PyAny>);

impl<'py> FromPyObject<'_, 'py> for SetLike<'py> {
    type Error = PyErr;

    fn extract(obj: Borrowed<'_, 'py, PyAny>) -> PyResult<Self> {
        if is_set_like(&obj)? {
            Ok(Self(obj.to_owned()))
        } else {
            Err(PyTypeError::new_err(format!(
                "expected a set-like object, got {}",
                obj.get_type().qualname()?
            )))
        }
    }
}

/// Returns `other` if it is a set-like object, or a new `set` built from the iterable otherwise.
///
/// Mirrors the way the named methods of `set` (e.g. `issubset()`) accept any iterable.
fn as_set_like<'py>(other: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
    if is_set_like(other)? {
        Ok(other.clone())
    } else {
        PySet::type_object(other.py()).call1((other,))
    }
}

/// Returns `other`, unless it is `slf`, in which case a snapshot of it as a plain `set` is returned.
///
/// This is used by mutating methods to avoid a borrow conflict when a set is updated from itself.
/// See also: <https://docs.rs/pyo3/latest/pyo3/pycell/index.html#dealing-with-possibly-overlapping-mutable-references>.
fn snapshot_if_self<'py>(slf: &Bound<'py, ModelFieldsSet>, other: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
    if other.is(slf) {
        PySet::type_object(other.py()).call1((other,))
    } else {
        Ok(other.clone())
    }
}

/// The set of field names explicitly set on a model instance, available as `__pydantic_fields_set__`.
///
/// Instead of storing every field name, the set holds a reference to the list of the model's field names
/// (shared between all instances validated by the same `model-fields` validator) along with a bitset
/// of the fields that are set. Extra keys (when `extra='allow'` is used) are stored in a plain Python
/// `set`, only allocated when needed.
///
/// The type is *not* a subclass of `set` but it implements the full `set` API and is registered as
/// a virtual subclass of `collections.abc.MutableSet`.
///
/// Invariant: a known field name is never stored in `extra`.
#[pyclass(module = "pydantic_core._pydantic_core")]
#[derive(Debug)]
pub struct ModelFieldsSet {
    field_names: Arc<FieldNames>,
    bits: BitSet,
    extra: Option<Py<PySet>>,
}

impl ModelFieldsSet {
    /// Creates an empty set, for a model with the provided field names.
    pub fn empty(field_names: Arc<FieldNames>) -> Self {
        Self {
            bits: BitSet::with_len(field_names.len()),
            field_names,
            extra: None,
        }
    }

    /// Marks the field at `index` (in the field names list) as set.
    pub fn insert_field(&mut self, index: usize) {
        self.bits.insert(index);
    }

    /// Adds an extra key to the set, without checking whether it is a known field name.
    ///
    /// Callers must ensure `key` is not a known field name, otherwise use [`insert_value()`][Self::insert_value].
    pub fn insert_extra(&mut self, py: Python<'_>, key: &Bound<'_, PyString>) -> PyResult<()> {
        debug_assert!(
            self.index_of(key).is_none(),
            "extra key {key} is a known field name, `insert_value()` should be used instead"
        );
        match &self.extra {
            Some(extra) => extra.bind(py).add(key),
            None => {
                self.extra = Some(PySet::new(py, [key])?.unbind());
                Ok(())
            }
        }
    }

    /// Adds `value` to the set, returning an error if it is not a string.
    pub fn insert_value(&mut self, py: Python<'_>, value: &Bound<'_, PyAny>) -> PyResult<()> {
        let Ok(value) = value.cast::<PyString>() else {
            return Err(PyTypeError::new_err(format!(
                "ModelFieldsSet elements must be strings, got {}",
                value.get_type().qualname()?
            )));
        };
        match self.index_of(value) {
            Some(index) => {
                self.bits.insert(index);
                Ok(())
            }
            None => self.insert_extra(py, value),
        }
    }

    /// Removes `value` from the set, returning whether it was present.
    fn discard_value(&mut self, py: Python<'_>, value: &Bound<'_, PyAny>) -> PyResult<bool> {
        let Ok(value) = value.cast::<PyString>() else {
            return Ok(false);
        };
        if let Some(index) = self.index_of(value) {
            return Ok(self.bits.remove(index));
        }
        match &self.extra {
            Some(extra) => extra.bind(py).discard(value),
            None => Ok(false),
        }
    }

    /// Whether `value` is in the set.
    pub fn contains_value(&self, py: Python<'_>, value: &Bound<'_, PyAny>) -> PyResult<bool> {
        let Ok(value) = value.cast::<PyString>() else {
            return Ok(false);
        };
        if let Some(index) = self.index_of(value) {
            return Ok(self.bits.contains(index));
        }
        match &self.extra {
            Some(extra) => extra.bind(py).contains(value),
            None => Ok(false),
        }
    }

    /// The index of the field named `name`, if any.
    fn index_of(&self, name: &Bound<'_, PyString>) -> Option<usize> {
        // Fast path: field names are (almost always) interned, so pointer equality is likely to succeed:
        let ptr = name.as_ptr();
        if let Some(index) = self.field_names.iter().position(|n| n.as_py_str().as_ptr() == ptr) {
            return Some(index);
        }
        // A string that can't be represented as UTF-8 (e.g. with lone surrogates) can't be a field name:
        let name = name.to_str().ok()?;
        self.field_names.iter().position(|n| &**n == name)
    }

    fn num_elements(&self, py: Python<'_>) -> usize {
        self.bits.count_ones() + self.extra.as_ref().map_or(0, |extra| extra.bind(py).len())
    }

    /// Iterates over the elements of the set: known fields in definition order, then extra keys.
    fn elements<'py>(&self, py: Python<'py>) -> impl Iterator<Item = Bound<'py, PyAny>> {
        let fields = (0..self.field_names.len())
            .filter(|index| self.bits.contains(*index))
            .map(move |index| self.field_names[index].as_py_str().bind(py).clone().into_any());
        let extra = self.extra.as_ref().map(|extra| extra.bind(py).iter());
        fields.chain(extra.into_iter().flatten())
    }

    fn duplicate(&self, py: Python<'_>) -> PyResult<Self> {
        Ok(Self {
            field_names: Arc::clone(&self.field_names),
            bits: self.bits.clone(),
            extra: match &self.extra {
                Some(extra) => Some(PySet::new(py, extra.bind(py))?.unbind()),
                None => None,
            },
        })
    }

    /// Whether every element of the set is in `other` (which must be a set-like object).
    fn is_subset_of(&self, py: Python<'_>, other: &Bound<'_, PyAny>) -> PyResult<bool> {
        for element in self.elements(py) {
            if !other.contains(element)? {
                return Ok(false);
            }
        }
        Ok(true)
    }

    /// Whether every element of `other` (which can be any iterable) is in the set.
    fn is_superset_of(&self, py: Python<'_>, other: &Bound<'_, PyAny>) -> PyResult<bool> {
        for element in other.try_iter()? {
            if !self.contains_value(py, &element?)? {
                return Ok(false);
            }
        }
        Ok(true)
    }

    fn update_with(&mut self, py: Python<'_>, other: &Bound<'_, PyAny>) -> PyResult<()> {
        for element in other.try_iter()? {
            self.insert_value(py, &element?)?;
        }
        Ok(())
    }

    fn intersection_update_with(&mut self, py: Python<'_>, other: &Bound<'_, PyAny>) -> PyResult<()> {
        let other = as_set_like(other)?;
        for index in 0..self.field_names.len() {
            if self.bits.contains(index) && !other.contains(self.field_names[index].as_py_str())? {
                self.bits.remove(index);
            }
        }
        if let Some(extra) = &self.extra {
            extra
                .bind(py)
                .call_method1(intern!(py, "intersection_update"), (other,))?;
        }
        Ok(())
    }

    fn difference_update_with(&mut self, py: Python<'_>, other: &Bound<'_, PyAny>) -> PyResult<()> {
        for element in other.try_iter()? {
            self.discard_value(py, &element?)?;
        }
        Ok(())
    }

    fn symmetric_difference_update_with(&mut self, py: Python<'_>, other: &Bound<'_, PyAny>) -> PyResult<()> {
        // Converting to a set first ensures each element is toggled at most once:
        for element in as_set_like(other)?.try_iter()? {
            let element = element?;
            if !self.discard_value(py, &element)? {
                self.insert_value(py, &element)?;
            }
        }
        Ok(())
    }

    /// Builds the result of a reflected binary operator (e.g. `{'a'} | fields_set`), which is a plain `set`,
    /// or a `frozenset` if `other` is one.
    fn reflected_result<'py>(
        py: Python<'py>,
        other: &Bound<'py, PyAny>,
        elements: impl IntoIterator<Item = Bound<'py, PyAny>>,
    ) -> PyResult<Bound<'py, PyAny>> {
        let result = PySet::new(py, elements)?;
        if other.is_instance_of::<PyFrozenSet>() {
            Ok(PyFrozenSet::new(py, &result)?.into_any())
        } else {
            Ok(result.into_any())
        }
    }
}

#[pymethods]
impl ModelFieldsSet {
    /// Creates a new set from the elements of `iterable`, for a model with the provided `field_names`.
    #[new]
    #[pyo3(signature = (iterable = None, field_names = None))]
    fn py_new(
        py: Python<'_>,
        iterable: Option<&Bound<'_, PyAny>>,
        field_names: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<Self> {
        let field_names: FieldNames = match field_names {
            Some(field_names) => field_names
                .try_iter()?
                .map(|name| name?.extract::<PyBackedStr>())
                .collect::<PyResult<_>>()?,
            None => FieldNames::from_iter([]),
        };
        let mut set = Self::empty(Arc::new(field_names));
        if let Some(iterable) = iterable {
            set.update_with(py, iterable)?;
        }
        Ok(set)
    }

    fn __reduce__<'py>(slf: &Bound<'py, Self>) -> PyResult<Bound<'py, PyTuple>> {
        let py = slf.py();
        let this = slf.borrow();
        let elements = PyList::new(py, this.elements(py).collect::<Vec<_>>())?;
        let field_names = PyList::new(py, this.field_names.iter().map(PyBackedStr::as_py_str))?;
        (slf.get_type(), (elements, field_names)).into_pyobject(py)
    }

    fn __copy__(&self, py: Python<'_>) -> PyResult<Self> {
        self.duplicate(py)
    }

    fn __deepcopy__(&self, py: Python<'_>, _memo: &Bound<'_, PyAny>) -> PyResult<Self> {
        // The elements are strings, so a shallow copy is enough:
        self.duplicate(py)
    }

    // The representation mirrors the one of `set`.
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        if self.num_elements(py) == 0 {
            return Ok("set()".to_string());
        }
        let elements = self
            .elements(py)
            .map(|element| element.repr().map(|repr| repr.to_string()))
            .collect::<PyResult<Vec<_>>>()?;
        Ok(format!("{{{}}}", elements.join(", ")))
    }

    fn __len__(&self, py: Python<'_>) -> usize {
        self.num_elements(py)
    }

    fn __contains__(&self, py: Python<'_>, value: &Bound<'_, PyAny>) -> PyResult<bool> {
        self.contains_value(py, value)
    }

    fn __iter__(&self, py: Python<'_>) -> PyResult<ModelFieldsSetIterator> {
        Ok(ModelFieldsSetIterator {
            field_names: Arc::clone(&self.field_names),
            bits: self.bits.clone(),
            next_index: 0,
            extra: match &self.extra {
                Some(extra) => Some(extra.bind(py).try_iter()?.unbind()),
                None => None,
            },
        })
    }

    fn __richcmp__(&self, py: Python<'_>, other: SetLike<'_>, op: CompareOp) -> PyResult<bool> {
        let other = &other.0;
        match op {
            CompareOp::Eq => Ok(self.num_elements(py) == other.len()? && self.is_subset_of(py, other)?),
            CompareOp::Ne => Ok(self.num_elements(py) != other.len()? || !self.is_subset_of(py, other)?),
            CompareOp::Le => self.is_subset_of(py, other),
            CompareOp::Lt => Ok(self.num_elements(py) < other.len()? && self.is_subset_of(py, other)?),
            CompareOp::Ge => self.is_superset_of(py, other),
            CompareOp::Gt => Ok(self.num_elements(py) > other.len()? && self.is_superset_of(py, other)?),
        }
    }

    fn add(&mut self, py: Python<'_>, value: &Bound<'_, PyAny>) -> PyResult<()> {
        self.insert_value(py, value)
    }

    fn discard(&mut self, py: Python<'_>, value: &Bound<'_, PyAny>) -> PyResult<()> {
        self.discard_value(py, value)?;
        Ok(())
    }

    fn remove(&mut self, py: Python<'_>, value: &Bound<'_, PyAny>) -> PyResult<()> {
        if self.discard_value(py, value)? {
            Ok(())
        } else {
            Err(PyKeyError::new_err(value.clone().unbind()))
        }
    }

    fn pop<'py>(&mut self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        if let Some(index) = (0..self.field_names.len()).find(|index| self.bits.contains(*index)) {
            self.bits.remove(index);
            return Ok(self.field_names[index].as_py_str().bind(py).clone().into_any());
        }
        if let Some(element) = self.extra.as_ref().and_then(|extra| extra.bind(py).pop()) {
            return Ok(element);
        }
        Err(PyKeyError::new_err("pop from an empty set"))
    }

    fn clear(&mut self) {
        self.bits.clear();
        self.extra = None;
    }

    fn copy(&self, py: Python<'_>) -> PyResult<Self> {
        self.duplicate(py)
    }

    #[pyo3(signature = (*others))]
    fn update(slf: &Bound<'_, Self>, others: &Bound<'_, PyTuple>) -> PyResult<()> {
        let py = slf.py();
        for other in others {
            let other = snapshot_if_self(slf, &other)?;
            slf.borrow_mut().update_with(py, &other)?;
        }
        Ok(())
    }

    #[pyo3(signature = (*others))]
    fn intersection_update(slf: &Bound<'_, Self>, others: &Bound<'_, PyTuple>) -> PyResult<()> {
        let py = slf.py();
        for other in others {
            let other = snapshot_if_self(slf, &other)?;
            slf.borrow_mut().intersection_update_with(py, &other)?;
        }
        Ok(())
    }

    #[pyo3(signature = (*others))]
    fn difference_update(slf: &Bound<'_, Self>, others: &Bound<'_, PyTuple>) -> PyResult<()> {
        let py = slf.py();
        for other in others {
            let other = snapshot_if_self(slf, &other)?;
            slf.borrow_mut().difference_update_with(py, &other)?;
        }
        Ok(())
    }

    fn symmetric_difference_update(slf: &Bound<'_, Self>, other: &Bound<'_, PyAny>) -> PyResult<()> {
        let other = snapshot_if_self(slf, other)?;
        slf.borrow_mut().symmetric_difference_update_with(slf.py(), &other)
    }

    #[pyo3(signature = (*others))]
    fn union(&self, py: Python<'_>, others: &Bound<'_, PyTuple>) -> PyResult<Self> {
        let mut result = self.duplicate(py)?;
        for other in others {
            result.update_with(py, &other)?;
        }
        Ok(result)
    }

    #[pyo3(signature = (*others))]
    fn intersection(&self, py: Python<'_>, others: &Bound<'_, PyTuple>) -> PyResult<Self> {
        let mut result = self.duplicate(py)?;
        for other in others {
            result.intersection_update_with(py, &other)?;
        }
        Ok(result)
    }

    #[pyo3(signature = (*others))]
    fn difference(&self, py: Python<'_>, others: &Bound<'_, PyTuple>) -> PyResult<Self> {
        let mut result = self.duplicate(py)?;
        for other in others {
            result.difference_update_with(py, &other)?;
        }
        Ok(result)
    }

    fn symmetric_difference(&self, py: Python<'_>, other: &Bound<'_, PyAny>) -> PyResult<Self> {
        let mut result = self.duplicate(py)?;
        result.symmetric_difference_update_with(py, other)?;
        Ok(result)
    }

    fn issubset(&self, py: Python<'_>, other: &Bound<'_, PyAny>) -> PyResult<bool> {
        self.is_subset_of(py, &as_set_like(other)?)
    }

    fn issuperset(&self, py: Python<'_>, other: &Bound<'_, PyAny>) -> PyResult<bool> {
        self.is_superset_of(py, other)
    }

    fn isdisjoint(&self, py: Python<'_>, other: &Bound<'_, PyAny>) -> PyResult<bool> {
        for element in other.try_iter()? {
            if self.contains_value(py, &element?)? {
                return Ok(false);
            }
        }
        Ok(true)
    }

    fn __or__(&self, py: Python<'_>, other: SetLike<'_>) -> PyResult<Self> {
        let mut result = self.duplicate(py)?;
        result.update_with(py, &other.0)?;
        Ok(result)
    }

    fn __ror__<'py>(&self, py: Python<'py>, other: SetLike<'py>) -> PyResult<Bound<'py, PyAny>> {
        let other_elements = other.0.try_iter()?.collect::<PyResult<Vec<_>>>()?;
        Self::reflected_result(py, &other.0, other_elements.into_iter().chain(self.elements(py)))
    }

    fn __ior__(slf: &Bound<'_, Self>, other: SetLike<'_>) -> PyResult<()> {
        let other = snapshot_if_self(slf, &other.0)?;
        slf.borrow_mut().update_with(slf.py(), &other)
    }

    fn __and__(&self, py: Python<'_>, other: SetLike<'_>) -> PyResult<Self> {
        let mut result = self.duplicate(py)?;
        result.intersection_update_with(py, &other.0)?;
        Ok(result)
    }

    fn __rand__<'py>(&self, py: Python<'py>, other: SetLike<'py>) -> PyResult<Bound<'py, PyAny>> {
        let mut elements = Vec::new();
        for element in other.0.try_iter()? {
            let element = element?;
            if self.contains_value(py, &element)? {
                elements.push(element);
            }
        }
        Self::reflected_result(py, &other.0, elements)
    }

    fn __iand__(slf: &Bound<'_, Self>, other: SetLike<'_>) -> PyResult<()> {
        let other = snapshot_if_self(slf, &other.0)?;
        slf.borrow_mut().intersection_update_with(slf.py(), &other)
    }

    fn __sub__(&self, py: Python<'_>, other: SetLike<'_>) -> PyResult<Self> {
        let mut result = self.duplicate(py)?;
        result.difference_update_with(py, &other.0)?;
        Ok(result)
    }

    fn __rsub__<'py>(&self, py: Python<'py>, other: SetLike<'py>) -> PyResult<Bound<'py, PyAny>> {
        let mut elements = Vec::new();
        for element in other.0.try_iter()? {
            let element = element?;
            if !self.contains_value(py, &element)? {
                elements.push(element);
            }
        }
        Self::reflected_result(py, &other.0, elements)
    }

    fn __isub__(slf: &Bound<'_, Self>, other: SetLike<'_>) -> PyResult<()> {
        let other = snapshot_if_self(slf, &other.0)?;
        slf.borrow_mut().difference_update_with(slf.py(), &other)
    }

    fn __xor__(&self, py: Python<'_>, other: SetLike<'_>) -> PyResult<Self> {
        let mut result = self.duplicate(py)?;
        result.symmetric_difference_update_with(py, &other.0)?;
        Ok(result)
    }

    fn __rxor__<'py>(&self, py: Python<'py>, other: SetLike<'py>) -> PyResult<Bound<'py, PyAny>> {
        let mut elements = Vec::new();
        for element in other.0.try_iter()? {
            let element = element?;
            if !self.contains_value(py, &element)? {
                elements.push(element);
            }
        }
        for element in self.elements(py) {
            if !other.0.contains(&element)? {
                elements.push(element);
            }
        }
        Self::reflected_result(py, &other.0, elements)
    }

    fn __ixor__(slf: &Bound<'_, Self>, other: SetLike<'_>) -> PyResult<()> {
        let other = snapshot_if_self(slf, &other.0)?;
        slf.borrow_mut().symmetric_difference_update_with(slf.py(), &other)
    }
}

/// The `__pydantic_fields_set__` attribute of a model instance, which is usually a [`ModelFieldsSet`]
/// but can also be a plain `set` (e.g. when the instance was created using `model_construct()`).
pub enum FieldsSet<'py> {
    ModelFieldsSet(Bound<'py, ModelFieldsSet>),
    Set(Bound<'py, PySet>),
}

// Implemented manually rather than derived to avoid the performance cost when a variant fails to extract
// (see https://github.com/PyO3/pyo3/discussions/2968).
impl<'py> FromPyObject<'_, 'py> for FieldsSet<'py> {
    type Error = PyErr;

    fn extract(obj: Borrowed<'_, 'py, PyAny>) -> PyResult<Self> {
        if let Ok(fields_set) = obj.cast::<ModelFieldsSet>() {
            Ok(Self::ModelFieldsSet(fields_set.to_owned()))
        } else if let Ok(set) = obj.cast::<PySet>() {
            Ok(Self::Set(set.to_owned()))
        } else {
            Err(PyTypeError::new_err(format!(
                "`__pydantic_fields_set__` must be a `ModelFieldsSet` or `set` instance, got {}",
                obj.get_type().qualname()?
            )))
        }
    }
}

impl FieldsSet<'_> {
    pub fn contains(&self, value: &Bound<'_, PyAny>) -> PyResult<bool> {
        match self {
            Self::ModelFieldsSet(fields_set) => fields_set.try_borrow()?.contains_value(value.py(), value),
            Self::Set(set) => set.contains(value),
        }
    }

    pub fn add(&self, value: &Bound<'_, PyAny>) -> PyResult<()> {
        match self {
            Self::ModelFieldsSet(fields_set) => fields_set.try_borrow_mut()?.insert_value(value.py(), value),
            Self::Set(set) => set.add(value),
        }
    }
}

#[pyclass(module = "pydantic_core._pydantic_core")]
struct ModelFieldsSetIterator {
    field_names: Arc<FieldNames>,
    bits: BitSet,
    next_index: usize,
    extra: Option<Py<PyIterator>>,
}

#[pymethods]
impl ModelFieldsSetIterator {
    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__<'py>(&mut self, py: Python<'py>) -> PyResult<Option<Bound<'py, PyAny>>> {
        while self.next_index < self.field_names.len() {
            let index = self.next_index;
            self.next_index += 1;
            if self.bits.contains(index) {
                return Ok(Some(self.field_names[index].as_py_str().bind(py).clone().into_any()));
            }
        }
        match &self.extra {
            Some(extra) => extra.bind(py).clone().next().transpose(),
            None => Ok(None),
        }
    }
}
