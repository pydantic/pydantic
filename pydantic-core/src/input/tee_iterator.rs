use std::cell::RefCell;
use std::rc::Rc;

use pyo3::prelude::*;
use pyo3::types::PyIterator;
use pyo3::{PyTraverseError, PyVisit};

/// Shared state between a [`TeeIterable`] and the [`TeeIterator`] cursors created
/// from it: the underlying iterator and the items pulled from it so far.
#[derive(Debug)]
struct TeeState {
    iter: Py<PyIterator>,
    buffer: Vec<Py<PyAny>>,
    exhausted: bool,
}

/// A re-iterable wrapper around a one-shot Python iterator (e.g. a generator).
///
/// Each call to `__iter__` returns a new [`TeeIterator`] cursor which first replays
/// the items already pulled by other cursors, then keeps consuming the shared
/// iterator. Used by union validation so that each union member can be tried
/// without losing the items consumed by previous attempts.
#[pyclass(module = "pydantic_core._pydantic_core", unsendable)]
#[derive(Debug)]
pub(crate) struct TeeIterable {
    state: Rc<RefCell<TeeState>>,
}

impl TeeIterable {
    pub(crate) fn new(iter: Py<PyIterator>) -> Self {
        Self {
            state: Rc::new(RefCell::new(TeeState {
                iter,
                buffer: Vec::new(),
                exhausted: false,
            })),
        }
    }
}

#[pymethods]
impl TeeIterable {
    fn __iter__(slf: PyRef<'_, Self>, py: Python<'_>) -> PyResult<Py<TeeIterator>> {
        Py::new(
            py,
            TeeIterator {
                state: slf.state.clone(),
                index: 0,
            },
        )
    }

    // Forward the representation to the wrapped iterator, so that errors
    // display the original input (e.g. `<generator object ...>`):
    fn __repr__(slf: PyRef<'_, Self>, py: Python<'_>) -> PyResult<String> {
        Ok(slf.state.borrow().iter.bind(py).repr()?.to_string())
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        let state = self.state.borrow();
        visit.call(&state.iter)?;
        for item in &state.buffer {
            visit.call(item)?;
        }
        Ok(())
    }
}

/// A cursor over a [`TeeIterable`]'s shared buffer and underlying iterator.
#[pyclass(module = "pydantic_core._pydantic_core", unsendable)]
#[derive(Debug)]
pub(crate) struct TeeIterator {
    state: Rc<RefCell<TeeState>>,
    index: usize,
}

#[pymethods]
impl TeeIterator {
    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__(mut slf: PyRefMut<'_, Self>, py: Python<'_>) -> PyResult<Option<Py<PyAny>>> {
        // Replay the items already pulled by other cursors:
        let buffered = {
            let state = slf.state.borrow();
            state.buffer.get(slf.index).map(|item| item.clone_ref(py))
        };
        if let Some(item) = buffered {
            slf.index += 1;
            return Ok(Some(item));
        }
        let (iter, exhausted) = {
            let state = slf.state.borrow();
            (state.iter.clone_ref(py), state.exhausted)
        };
        if exhausted {
            return Ok(None);
        }
        // Note: the underlying iterator can run arbitrary Python code, so the shared
        // state is only borrowed to read from it, never while `next()` is called:
        match iter.bind(py).to_owned().next() {
            Some(Ok(item)) => {
                let item = item.unbind();
                slf.state.borrow_mut().buffer.push(item.clone_ref(py));
                slf.index += 1;
                Ok(Some(item))
            }
            Some(Err(err)) => Err(err),
            None => {
                slf.state.borrow_mut().exhausted = true;
                Ok(None)
            }
        }
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        let state = self.state.borrow();
        visit.call(&state.iter)?;
        for item in &state.buffer {
            visit.call(item)?;
        }
        Ok(())
    }
}
