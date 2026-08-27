//! Core schema traversal used for schema cleaning.
//!
//! The traversal is depth-first, using an explicit work stack (so that deeply nested schemas
//! can't overflow the native stack), and never mutates the schema.
use std::collections::hash_map::Entry;

use ahash::AHashMap;
use pyo3::exceptions::{PyKeyError, PyLookupError};
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyString, PyTuple};
use smallvec::SmallVec;

/// A reference was pointing to a non-existing core schema.
#[pyclass(extends=PyLookupError, module="pydantic_core._pydantic_core._schema_gather", frozen, skip_from_py_object)]
#[derive(Debug)]
pub struct MissingDefinitionError {
    #[pyo3(get)]
    schema_reference: Py<PyAny>,
}

#[pymethods]
impl MissingDefinitionError {
    #[new]
    #[pyo3(signature = (schema_reference, /))]
    fn py_new(schema_reference: Py<PyAny>) -> Self {
        Self { schema_reference }
    }
}

/// The child schemas of a schema, in traversal order.
type Children<'py> = SmallVec<[Bound<'py, PyAny>; 8]>;

fn extend_from_iterable<'py>(children: &mut Children<'py>, iterable: &Bound<'py, PyAny>) -> PyResult<()> {
    if let Ok(list) = iterable.cast_exact::<PyList>() {
        children.extend(list.iter());
    } else if let Ok(tuple) = iterable.cast_exact::<PyTuple>() {
        children.extend(tuple.iter());
    } else {
        for item in iterable.try_iter()? {
            children.push(item?);
        }
    }
    Ok(())
}

/// `schema[key]`
fn required<'py>(schema: &Bound<'py, PyDict>, key: &Bound<'py, PyString>) -> PyResult<Bound<'py, PyAny>> {
    schema
        .get_item(key)?
        .ok_or_else(|| PyKeyError::new_err(key.clone().unbind()))
}

/// `if key in schema: children.append(schema[key])`
fn child_optional<'py>(
    children: &mut Children<'py>,
    schema: &Bound<'py, PyDict>,
    key: &Bound<'py, PyString>,
) -> PyResult<()> {
    if let Some(s) = schema.get_item(key)? {
        children.push(s);
    }
    Ok(())
}

/// `children.append(schema[key])`
fn child_required<'py>(
    children: &mut Children<'py>,
    schema: &Bound<'py, PyDict>,
    key: &Bound<'py, PyString>,
) -> PyResult<()> {
    children.push(required(schema, key)?);
    Ok(())
}

/// `if key in schema: children.extend(schema[key])`
fn children_optional<'py>(
    children: &mut Children<'py>,
    schema: &Bound<'py, PyDict>,
    key: &Bound<'py, PyString>,
) -> PyResult<()> {
    match schema.get_item(key)? {
        Some(items) => extend_from_iterable(children, &items),
        None => Ok(()),
    }
}

/// `children.extend(schema[key])`
fn children_required<'py>(
    children: &mut Children<'py>,
    schema: &Bound<'py, PyDict>,
    key: &Bound<'py, PyString>,
) -> PyResult<()> {
    extend_from_iterable(children, &required(schema, key)?)
}

/// `children.extend(schema[key].values())`
fn children_values_required<'py>(
    children: &mut Children<'py>,
    schema: &Bound<'py, PyDict>,
    key: &Bound<'py, PyString>,
) -> PyResult<()> {
    let items = required(schema, key)?;
    if let Ok(items) = items.cast_exact::<PyDict>() {
        // (iterating the dict directly, in order, rather than materializing `.values()`)
        children.reserve(items.len());
        for (_, value) in items.iter() {
            children.push(value);
        }
        Ok(())
    } else {
        extend_from_iterable(children, &items.call_method0(intern!(schema.py(), "values"))?)
    }
}

/// `children.extend(s['schema'] for s in schema['arguments_schema'])`
fn children_arguments<'py>(children: &mut Children<'py>, schema: &Bound<'py, PyDict>) -> PyResult<()> {
    let py = schema.py();
    let mut parameters = Children::new();
    extend_from_iterable(&mut parameters, &required(schema, intern!(py, "arguments_schema"))?)?;
    for parameter in &parameters {
        child_required(children, parameter.cast::<PyDict>()?, intern!(py, "schema"))?;
    }
    Ok(())
}

/// Collect the child schemas of `schema` (of type `schema_type`, anything but `'definition-ref'`),
/// in traversal order (not including the `'serialization'` schema).
fn collect_child_schemas<'py>(
    children: &mut Children<'py>,
    schema: &Bound<'py, PyDict>,
    schema_type: &str,
) -> PyResult<()> {
    let py = schema.py();
    match schema_type {
        "definitions" => {
            child_required(children, schema, intern!(py, "schema"))?;
            children_required(children, schema, intern!(py, "definitions"))?;
        }
        "list" | "set" | "frozenset" | "generator" => {
            child_optional(children, schema, intern!(py, "items_schema"))?;
        }
        "tuple" => {
            children_optional(children, schema, intern!(py, "items_schema"))?;
        }
        "dict" | "frozendict" => {
            child_optional(children, schema, intern!(py, "keys_schema"))?;
            child_optional(children, schema, intern!(py, "values_schema"))?;
        }
        "union" => {
            let mut choices = Children::new();
            extend_from_iterable(&mut choices, &required(schema, intern!(py, "choices"))?)?;
            // `iter_union_choices()`: `choice[0] if isinstance(choice, tuple) else choice`
            for choice in choices {
                if choice.is_instance_of::<PyTuple>() {
                    children.push(choice.get_item(0)?);
                } else {
                    children.push(choice);
                }
            }
        }
        "tagged-union" => {
            children_values_required(children, schema, intern!(py, "choices"))?;
        }
        "chain" => {
            children_required(children, schema, intern!(py, "steps"))?;
        }
        "lax-or-strict" => {
            child_required(children, schema, intern!(py, "lax_schema"))?;
            child_required(children, schema, intern!(py, "strict_schema"))?;
        }
        "json-or-python" => {
            child_required(children, schema, intern!(py, "json_schema"))?;
            child_required(children, schema, intern!(py, "python_schema"))?;
        }
        "model-fields" | "typed-dict" => {
            child_optional(children, schema, intern!(py, "extras_schema"))?;
            children_optional(children, schema, intern!(py, "computed_fields"))?;
            children_values_required(children, schema, intern!(py, "fields"))?;
        }
        "dataclass-args" => {
            children_optional(children, schema, intern!(py, "computed_fields"))?;
            children_required(children, schema, intern!(py, "fields"))?;
        }
        "named-tuple" => {
            children_required(children, schema, intern!(py, "fields"))?;
        }
        "arguments" => {
            children_arguments(children, schema)?;
            child_optional(children, schema, intern!(py, "var_args_schema"))?;
            child_optional(children, schema, intern!(py, "var_kwargs_schema"))?;
        }
        "arguments-v3" => {
            children_arguments(children, schema)?;
        }
        "call" => {
            child_required(children, schema, intern!(py, "arguments_schema"))?;
            child_optional(children, schema, intern!(py, "return_schema"))?;
        }
        "computed-field" => {
            child_required(children, schema, intern!(py, "return_schema"))?;
        }
        "function-before" => {
            child_optional(children, schema, intern!(py, "schema"))?;
            child_optional(children, schema, intern!(py, "json_schema_input_schema"))?;
        }
        "function-plain" => {
            // TODO duplicate schema types for serializers and validators, needs to be deduplicated.
            child_optional(children, schema, intern!(py, "return_schema"))?;
            child_optional(children, schema, intern!(py, "json_schema_input_schema"))?;
        }
        "function-wrap" => {
            // TODO duplicate schema types for serializers and validators, needs to be deduplicated.
            child_optional(children, schema, intern!(py, "return_schema"))?;
            child_optional(children, schema, intern!(py, "schema"))?;
            child_optional(children, schema, intern!(py, "json_schema_input_schema"))?;
        }
        _ => {
            child_optional(children, schema, intern!(py, "schema"))?;
        }
    }
    Ok(())
}

/// A step of the depth-first traversal: a schema is entered (pre-order: its child schemas are
/// scheduled) and, once they are traversed, left (post-order: metadata handling, span closing).
enum TraversalStep<'py> {
    /// Enter a schema.
    Enter(Bound<'py, PyAny>),
    /// Leave a schema, once its child schemas (and the `'serialization'` schema) are traversed:
    /// handle the metadata, and close the span of encountered references of this schema.
    Leave {
        schema: Bound<'py, PyDict>,
        span_index: usize,
        traverse_metadata: bool,
    },
}

/// The current context used during core schema traversing.
///
/// Context instances should only be used during schema traversing.
struct GatherCtx<'a, 'py> {
    py: Python<'py>,
    /// The available definitions.
    definitions: &'a Bound<'py, PyDict>,
    /// The list of core schemas having the discriminator application deferred.
    ///
    /// Internally, these core schemas have a specific key set in the core metadata dict.
    deferred_discriminator_schemas: Bound<'py, PyList>,
    /// The collected definition references.
    ///
    /// If a definition reference schema can be inlined, it means that there is
    /// only one in the whole core schema. As such, it is stored as the value.
    /// Otherwise, the value is set to `None`.
    ///
    /// During schema traversing, definition reference schemas can be added as candidates, or removed
    /// (by setting the value to `None`).
    collected_references: Bound<'py, PyDict>,
    /// A mapping between the traversed core schema IDs and (the index in `spans` of) their span in the `encountered_refs`.
    ///
    /// Core schemas are stored (and thus shared) on successfully completed Pydantic models (and other
    /// referenceable types), meaning the same core schema object can appear multiple times in the
    /// traversed schema. Every schema object only needs to be traversed once: traversing per path
    /// can result in exponential blowup with highly interconnected models (e.g. `Model3` references
    /// `Model2` and `Model1`, while `Model2` also references `Model1`).
    ///
    /// However, the `collected_references` bookkeeping is per encounter: seeing a reference a second
    /// time (even through a shared schema object) means it can't be inlined. To preserve this without
    /// re-traversing, the references encountered while traversing each schema (i.e. the schema's span
    /// of the `encountered_refs`) are marked as non-inlinable when the schema is visited again.
    /// A `usize::MAX` end index means the schema is currently being traversed (in which case every reference
    /// encountered since the start index is marked as non-inlinable. This happens when a
    /// `'definition-ref'` schema object is reachable from the definition it points to, and inlining
    /// would then create a cycle).
    visited: AHashMap<usize, usize>,
    /// The `(start, end)` spans (see `visited`) of every visited schema.
    spans: Vec<(usize, usize)>,
    /// A list of the definition references encountered during the traversal, used with `visited`.
    encountered_refs: Vec<Bound<'py, PyAny>>,
    steps: Vec<TraversalStep<'py>>,
}

impl<'py> GatherCtx<'_, 'py> {
    fn run(&mut self, schema: &Bound<'py, PyAny>) -> PyResult<()> {
        self.steps.push(TraversalStep::Enter(schema.clone()));
        while let Some(step) = self.steps.pop() {
            match step {
                TraversalStep::Enter(schema) => self.enter(schema)?,
                TraversalStep::Leave {
                    schema,
                    span_index,
                    traverse_metadata,
                } => {
                    if traverse_metadata {
                        self.traverse_metadata(&schema)?;
                    }
                    self.spans[span_index].1 = self.encountered_refs.len();
                }
            }
        }
        Ok(())
    }

    fn traverse_metadata(&mut self, schema: &Bound<'py, PyDict>) -> PyResult<()> {
        if let Some(meta) = schema.get_item(intern!(self.py, "metadata"))? {
            if meta.is_none() {
                return Ok(());
            }
            let key = intern!(self.py, "pydantic_internal_union_discriminator");
            let contains = match meta.cast_exact::<PyDict>() {
                Ok(meta_dict) => meta_dict.contains(key)?,
                Err(_) => meta.contains(key)?,
            };
            if contains {
                self.deferred_discriminator_schemas.append(schema)?;
            }
        }
        Ok(())
    }

    /// The "pre-order" part of the traversal of a schema: bookkeeping, and scheduling the traversal
    /// of the child schemas (in order), the `'serialization'` schema and the `Leave` step.
    fn enter(&mut self, schema: Bound<'py, PyAny>) -> PyResult<()> {
        let py = self.py;
        let schema_id = schema.as_ptr() as usize;
        let span_index = match self.visited.entry(schema_id) {
            Entry::Occupied(entry) => {
                // The schema object was already traversed (or is currently being traversed, in which case
                // the end index is not set yet). Mark every definition reference encountered during its
                // traversal as non-inlinable, as if they were encountered again:
                let (start, end) = self.spans[*entry.get()];
                let end = if end == usize::MAX {
                    self.encountered_refs.len()
                } else {
                    end
                };
                for schema_ref in &self.encountered_refs[start..end] {
                    self.collected_references.set_item(schema_ref, py.None())?;
                }
                return Ok(());
            }
            Entry::Vacant(entry) => {
                let span_index = self.spans.len();
                entry.insert(span_index);
                self.spans.push((self.encountered_refs.len(), usize::MAX));
                span_index
            }
        };

        let schema = schema.cast_into::<PyDict>()?;
        let schema_type = required(&schema, intern!(py, "type"))?;
        let schema_type = schema_type.cast::<PyString>()?.to_str()?;

        // Steps are popped from the stack, so pushed in reverse order:
        // child schemas (in order), then the `'serialization'` schema, then `Leave`.
        let mut children = Children::new();
        let mut traverse_metadata = true;
        if schema_type == "definition-ref" {
            let schema_ref = required(&schema, intern!(py, "schema_ref"))?;
            self.encountered_refs.push(schema_ref.clone());

            if !self.collected_references.contains(&schema_ref)? {
                let definition = match self.definitions.get_item(&schema_ref)? {
                    Some(definition) if !definition.is_none() => definition,
                    _ => return Err(PyErr::new::<MissingDefinitionError, _>((schema_ref.unbind(),))),
                };
                // The `'definition-ref'` schema was only encountered once, make it
                // a candidate to be inlined:
                self.collected_references.set_item(&schema_ref, &schema)?;
                children.push(definition);
                child_optional(&mut children, &schema, intern!(py, "serialization"))?;
            } else {
                // The `'definition-ref'` schema was already encountered, meaning
                // the previously encountered schema (and this one) can't be inlined
                // (and its serialization schema / metadata aren't considered):
                self.collected_references.set_item(&schema_ref, py.None())?;
                traverse_metadata = false;
            }
        } else {
            collect_child_schemas(&mut children, &schema, schema_type)?;
            child_optional(&mut children, &schema, intern!(py, "serialization"))?;
        }

        self.steps.push(TraversalStep::Leave {
            schema,
            span_index,
            traverse_metadata,
        });
        self.steps.extend(children.into_iter().rev().map(TraversalStep::Enter));
        Ok(())
    }
}

/// Traverse the core schema and definitions and return the necessary information for schema cleaning,
/// as a `(collected_references, deferred_discriminator_schemas)` tuple.
///
/// During the core schema traversing, any `'definition-ref'` schema is:
///
/// - Validated: the reference must point to an existing definition. If this is not the case, a
///   `MissingDefinitionError` exception is raised.
/// - Stored in the context: the actual reference is stored in the context. Depending on whether
///   the `'definition-ref'` schema is encountered more that once, the schema itself is also
///   saved in the context to be inlined (i.e. replaced by the definition it points to).
#[pyfunction]
pub fn gather_schemas_for_cleaning<'py>(
    py: Python<'py>,
    schema: &Bound<'py, PyAny>,
    definitions: &Bound<'py, PyDict>,
) -> PyResult<(Bound<'py, PyDict>, Bound<'py, PyList>)> {
    let mut ctx = GatherCtx {
        py,
        definitions,
        deferred_discriminator_schemas: PyList::empty(py),
        collected_references: PyDict::new(py),
        // typical model schemas have tens to hundreds of nodes; start big enough to avoid the first few rehashes
        visited: AHashMap::with_capacity(256),
        spans: Vec::with_capacity(256),
        encountered_refs: Vec::new(),
        steps: Vec::with_capacity(64),
    };
    ctx.run(schema)?;
    Ok((ctx.collected_references, ctx.deferred_discriminator_schemas))
}
