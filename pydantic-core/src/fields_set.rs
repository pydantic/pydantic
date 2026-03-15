use fixedbitset::FixedBitSet;
use pyo3::{
    exceptions::PyValueError,
    prelude::*,
    pybacked::PyBackedStr,
    types::{PyDict, PyString, PyTuple},
};

// We have to make this a pyclass as we use it as a return value on `ModelFieldsValidator.validate()`,
// although we don't export it from the `pydantic_core` Python module:
#[pyclass(from_py_object)]
#[derive(Clone)]
pub struct ModelFieldsSetInner {
    bitset: FixedBitSet,
    extra_keys: Option<Vec<PyBackedStr>>,
}

impl ModelFieldsSetInner {
    pub fn new(bitset: FixedBitSet, extra_keys: Option<Vec<PyBackedStr>>) -> Self {
        Self { bitset, extra_keys }
    }

    pub fn len(&self) -> usize {
        match &self.extra_keys {
            Some(extra_keys) => self.bitset.count_ones(..) + extra_keys.len(),
            None => self.bitset.count_ones(..),
        }
    }
}

#[pyclass(module = "pydantic_core._pydantic_core")]
struct ModelFieldsSetIterator {
    iter: std::vec::IntoIter<Py<PyAny>>,
}

#[pymethods]
impl ModelFieldsSetIterator {
    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__(&mut self) -> Option<Py<PyAny>> {
        self.iter.next()
    }
}

#[pyclass(from_py_object, module = "pydantic_core._pydantic_core")]
#[derive(Clone)]
pub struct ModelFieldsSet {
    inner: ModelFieldsSetInner,
    model_fields: Py<PyAny>,
}

impl ModelFieldsSet {
    pub fn new(inner: ModelFieldsSetInner, model_fields: Py<PyAny>) -> Self {
        Self { inner, model_fields }
    }

    fn index_of(&self, py: Python, name: &str) -> PyResult<Option<usize>> {
        for (i, (field_name, _)) in self.model_fields.cast_bound::<PyDict>(py)?.iter().enumerate() {
            if field_name.cast::<PyString>()? == name {
                return Ok(Some(i));
            }
        }
        Ok(None)
    }
}

#[pymethods]
impl ModelFieldsSet {
    fn __contains__(&self, py: Python<'_>, key: Py<PyAny>) -> PyResult<bool> {
        let Ok(key_string) = key.cast_bound::<PyString>(py) else {
            return Ok(false);
        };
        let non_extra_exists = match self.index_of(py, key_string.to_str()?)? {
            Some(i) => self.inner.bitset.contains(i),
            None => false,
        };

        Ok(non_extra_exists
            || self
                .inner
                .extra_keys
                .as_ref()
                .is_some_and(|v| v.iter().any(|k| **k == key_string)))
    }

    fn __len__(&self) -> usize {
        self.inner.len()
    }

    fn __iter__(&self, py: Python<'_>) -> PyResult<ModelFieldsSetIterator> {
        let model_fields = self.model_fields.cast_bound::<PyDict>(py)?;
        let mut items = Vec::with_capacity(self.inner.len());

        for (i, (key, _)) in model_fields.iter().enumerate() {
            if i < self.inner.bitset.len() && self.inner.bitset.contains(i) {
                items.push(key.unbind());
            }
        }

        if let Some(extra_keys) = &self.inner.extra_keys {
            for key in extra_keys {
                items.push(PyString::new(py, key).into_any().unbind());
            }
        }

        Ok(ModelFieldsSetIterator {
            iter: items.into_iter(),
        })
    }

    fn add(&mut self, py: Python<'_>, value: Py<PyAny>) -> PyResult<()> {
        let value_string = value.cast_bound::<PyString>(py)?;
        match self.index_of(py, value_string.to_str()?)? {
            Some(i) => self.inner.bitset.insert(i),
            None => {
                let extra_keys = self.inner.extra_keys.get_or_insert_with(|| Vec::with_capacity(1));
                extra_keys.push(value_string.to_owned().try_into()?);
            }
        }

        Ok(())
    }

    #[pyo3(signature = (*py_args))]
    fn update(&mut self, py: Python<'_>, py_args: &Bound<'_, PyTuple>) -> PyResult<()> {
        for iter in py_args {
            for element in iter.try_iter()? {
                let element = element?;
                self.add(py, element.into())?;
            }
        }

        Ok(())
    }

    // Private helper, exposed because it is used by `BaseModel.model_construct()`:
    fn _add_index(&mut self, index: usize) -> PyResult<()> {
        if index >= self.inner.bitset.len() {
            return Err(PyValueError::new_err(format!(
                "Index {index} exceeds number of fields ({})",
                self.inner.bitset.len()
            )));
        }
        self.inner.bitset.insert(index);
        Ok(())
    }
}
