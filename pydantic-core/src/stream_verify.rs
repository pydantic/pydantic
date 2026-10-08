//! A build that checks the streaming path against the ordinary one on every single call.
//!
//! Compiled only under the `stream-verify` feature, never into a released wheel. When it is on,
//! any document the fast path completes is *also* validated the ordinary way and the two results
//! are compared; a difference raises rather than being returned. The point is not to add tests
//! but to turn every test that already exists — pydantic's own suite included — into a
//! differential test of this change, covering schemas nobody would think to write down.
//!
//! Only successes are compared, and that is the whole risk surface by construction: the fast
//! path contains no error-construction code at all, so it cannot invent, reword or relocate a
//! validation error. It can only produce a value or decline, and declining is what sends the
//! document down the ordinary path. So the two failure modes worth catching are "returned a
//! different value" and "accepted something the ordinary path rejects", and both are exactly
//! what comparing a streamed success against the ordinary result catches.
//!
//! One consequence to know about: validating twice runs any side effect twice. Two tests in
//! pydantic's suite count validator invocations (`test_validate_json_context`, in test_main.py
//! and in test_type_adapter.py) and so fail under this feature while passing in every ordinary
//! build. They are the only two of 12,683.

use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyFloat, PyList, PySet, PyTuple};

use crate::errors::ValResult;

/// Compare a streamed result against the ordinary one, raising if they differ.
pub fn compare(py: Python<'_>, streamed: &Py<PyAny>, tree: ValResult<Py<PyAny>>) -> PyResult<()> {
    let Ok(tree) = tree else {
        return Err(PyRuntimeError::new_err(
            "stream-verify: the streaming path accepted a document the ordinary path rejects",
        ));
    };
    let (streamed, tree) = (streamed.bind(py), tree.bind(py));
    if deep_eq(streamed, tree)? {
        Ok(())
    } else {
        Err(PyRuntimeError::new_err(format!(
            "stream-verify: the two paths disagree\n  streaming: {}\n  ordinary : {}",
            describe(streamed),
            describe(tree),
        )))
    }
}

/// The same structure `deep_eq` compares, rendered. A model's own `repr` is its address, which
/// tells a reader nothing about which field went wrong.
fn describe(value: &Bound<'_, PyAny>) -> String {
    if let Ok(items) = value.cast::<PyList>() {
        return format!("[{}]", join(items.iter().map(|v| describe(&v))));
    }
    if let Ok(items) = value.cast::<PyTuple>() {
        return format!("({})", join(items.iter().map(|v| describe(&v))));
    }
    if let Ok(items) = value.cast::<PyDict>() {
        return format!(
            "{{{}}}",
            join(items.iter().map(|(k, v)| format!("{}: {}", describe(&k), describe(&v))))
        );
    }
    if let Ok(dict) = value.getattr("__dict__") {
        let name = value
            .get_type()
            .name()
            .map_or_else(|_| "?".to_string(), |n| n.to_string_lossy().into_owned());
        let fields_set = match value.getattr("__pydantic_fields_set__") {
            Ok(set) => format!(" fields_set={}", describe(&set)),
            Err(_) => String::new(),
        };
        return format!("{name}{}{fields_set}", describe(&dict));
    }
    match value.repr() {
        Ok(repr) => repr.to_string_lossy().into_owned(),
        Err(_) => "<unreprable>".to_string(),
    }
}

fn join(parts: impl Iterator<Item = String>) -> String {
    parts.collect::<Vec<_>>().join(", ")
}

/// Structural equality, which is what "the same result" has to mean here.
///
/// `==` is not enough on its own: a validated model is usually a plain object whose `==` is
/// identity, and the two paths necessarily produce different instances. Attribute *order* is
/// compared too, because it is visible through `model_dump`.
fn deep_eq(a: &Bound<'_, PyAny>, b: &Bound<'_, PyAny>) -> PyResult<bool> {
    if a.is(b) {
        return Ok(true);
    }
    if !a.get_type().is(b.get_type()) {
        return Ok(false);
    }

    if let (Ok(a), Ok(b)) = (a.cast::<PyList>(), b.cast::<PyList>()) {
        return sequence_eq(a.iter(), b.iter(), a.len(), b.len());
    }
    if let (Ok(a), Ok(b)) = (a.cast::<PyTuple>(), b.cast::<PyTuple>()) {
        return sequence_eq(a.iter(), b.iter(), a.len(), b.len());
    }
    if let (Ok(a), Ok(b)) = (a.cast::<PyDict>(), b.cast::<PyDict>()) {
        if a.len() != b.len() {
            return Ok(false);
        }
        // zipped rather than looked up, so that insertion order is compared as well
        for ((ka, va), (kb, vb)) in std::iter::zip(a.iter(), b.iter()) {
            if !deep_eq(&ka, &kb)? || !deep_eq(&va, &vb)? {
                return Ok(false);
            }
        }
        return Ok(true);
    }
    // a set has no order to compare, and its members are hashable, so `==` is right
    if a.cast::<PySet>().is_ok() {
        return a.eq(b);
    }

    // a validated model: compare what the two paths actually set on it
    if let (Ok(da), Ok(db)) = (a.getattr("__dict__"), b.getattr("__dict__")) {
        if !deep_eq(&da, &db)? {
            return Ok(false);
        }
        for attr in ["__pydantic_fields_set__", "__pydantic_extra__"] {
            match (a.getattr(attr), b.getattr(attr)) {
                (Ok(va), Ok(vb)) => {
                    if !deep_eq(&va, &vb)? {
                        return Ok(false);
                    }
                }
                (Err(_), Err(_)) => {}
                _ => return Ok(false),
            }
        }
        return Ok(true);
    }

    // two nans are the same outcome here even though `==` says otherwise
    if let (Ok(fa), Ok(fb)) = (a.cast::<PyFloat>(), b.cast::<PyFloat>())
        && fa.value().is_nan()
        && fb.value().is_nan()
    {
        return Ok(true);
    }

    a.eq(b)
}

fn sequence_eq<'py>(
    a: impl Iterator<Item = Bound<'py, PyAny>>,
    b: impl Iterator<Item = Bound<'py, PyAny>>,
    len_a: usize,
    len_b: usize,
) -> PyResult<bool> {
    if len_a != len_b {
        return Ok(false);
    }
    for (x, y) in std::iter::zip(a, b) {
        if !deep_eq(&x, &y)? {
            return Ok(false);
        }
    }
    Ok(true)
}
