# Experiment: unified `SchemaValidator` / `SchemaSerializer` structure

**Status: experiment — not intended for merge as-is.**

This branch explores unifying pydantic-core's `SchemaValidator` and `SchemaSerializer` into a
single structure (`SchemaCore`) so that common data can be shared, with the goal of reducing
memory usage and improving performance. The public Python API is fully preserved:
`Model.__pydantic_validator__.validate_python(...)` etc. work unchanged, and
`__pydantic_validator__` / `__pydantic_serializer__` are still real `SchemaValidator` /
`SchemaSerializer` instances (`isinstance`, `repr`, pickling all behave as before).

## TL;DR

- The unified structure works, is fully API-compatible, and passes the pydantic test suite
  (excluding `tests/pydantic_core`; the only failures are pre-existing Python 3.15 base64
  issues that also fail on `main`).
- The measured standalone benefit is **modest**: on the `k8s.py` benchmark (7,316 models),
  import RSS drops from **165.1 MiB to 160.8 MiB (−4.3 MiB, ~8% of retained tree memory)**,
  import time is unchanged-to-slightly-better, hot paths are unchanged.
- Almost all of the win comes from the **structural node interning** added alongside the
  unification, not from unifying the two objects — the premise that the two structures
  duplicate a lot of memory turned out to be mostly false (details below).
- The real value of the branch is that it **unlocks follow-ups that would be big**: lazy
  serializer construction (~19.5 MiB + build time on k8s) and a single-pass dual build
  (halves the schema walk and the transient allocation peak). Neither needs further API
  changes now that a single owner exists.

## Design

### `SchemaCoreData` + views (`pydantic-core/src/schema_core.rs`)

```
SchemaCore (pyclass, owns SchemaCoreData)
├── py_schema, py_config            (shared; kept for pickle support)
├── validator: Option<ValidatorPart>   { tree, definitions, title, cache_str, ... }
└── serializer: Option<SerializerPart> { tree, definitions, ser config, json size hint }

SchemaValidator (pyclass)  = { core: Py<SchemaCore> }   // thin view
SchemaSerializer (pyclass) = { core: Py<SchemaCore> }   // thin view
```

- `SchemaCore(schema, config)` builds both parts around one shared owner; `.validator` /
  `.serializer` return view objects.
- Direct `SchemaValidator(schema)` / `SchemaSerializer(schema)` construction still works and
  builds a core with only the relevant part — memory behavior is unchanged for
  validator-only users (`validate_call`, direct pydantic-core users).
- Python wiring: `complete_model_class`, `_pydantic_dataclasses.complete_dataclass` and
  `TypeAdapter` build one `SchemaCore` per type; `create_schema_validator` accepts a
  pre-built validator so the plugin path (`PluggableSchemaValidator`) wraps the shared view.
- The prebuilt mechanism (nested models reusing an existing `__pydantic_validator__` /
  `__pydantic_serializer__`) keeps working unchanged because the class attributes are still
  genuine `SchemaValidator` / `SchemaSerializer` pyclass instances.

### The GC invariant (important pitfall)

The first iteration had both views sharing an `Arc<SchemaCoreData>` and each fully
traversing it in `__traverse__`. That breaks CPython's GC invariant that **every strong
reference is reported exactly once**, and made model classes uncollectable (caught by
`tests/test_generics.py::test_caches_get_cleaned_up`).

The fix shapes the object graph honestly: the data is owned by a single Python object
(`SchemaCore`), each view holds and reports exactly one reference to it, and only
`SchemaCore.__traverse__` reports the Python references held by the trees. This is also why
`PrebuiltValidator` must keep holding `Py<SchemaValidator>` rather than cloning the inner
`Arc` tree — any design where two pyclasses traverse the same Rust-owned Python references
breaks collection of model-class cycles.

### Structural node interning

Schemas repeat the same shapes constantly (`str | None = None` fields, `list[str]`, …), and
each occurrence used to allocate its own node. Two levels of deduplication were added for
`nullable`, `list` and `default` nodes (`InternKey` in `definitions.rs`):

- **Per-build memo** in `DefinitionsBuilder`: keyed by child `Arc` pointer + node
  parameters (+ default object *identity*, so mutable per-field defaults are never merged).
- **Process-global intern pool** (one per side): only for nodes whose entire subtree is
  data-free — leaf children (`str`/`int`/`bool`/`float`/`none`/`any`) keyed semantically by
  kind + build flags, compound children only if they are themselves pool members (stable
  pointers), and defaults only when absent or the immortal `None`. The pool grows with the
  number of *distinct node shapes*, never with the number of builds, and can never pin user
  objects — so a `TypeAdapter(Optional[str])` in a loop hits one pool entry instead of
  leaking.

Leaf singletons (plain `str`/`int`/`bool`/… validators and serializers) already existed on
`main`, which is why the naive "share the leaves" win was already taken.

## Measurements

All numbers: release builds, CPython 3.15.0b4 (macOS arm64), median of 3 runs.

### `import k8s` (7,316 models, ~88k schema nodes)

|                        | main    | this branch |
|------------------------|---------|-------------|
| RSS delta after import | 165.1 MiB | 160.8 MiB |
| import time            | ~1.56 s | ~1.51 s |
| memray leaked-at-exit   | 143.8 MiB | 140.1 MiB |

### Hot paths (medium model, ns/op, timeit best-of-5)

|                   | main | this branch |
|-------------------|------|-------------|
| `validate_python` | 515  | 491 |
| `to_json`         | 382  | 385 |
| `model_dump`      | 606  | 615 |

Differences are within noise; the extra pointer hop per call (view → `Py<SchemaCore>` →
part) is not measurable.

### Where the memory actually is (k8s import, measured by stubbing each side + memray)

- Retained validator trees: **~32 MiB**; retained serializer trees: **~19.5 MiB**.
- Everything else (~115 MiB) is Python-side: class objects, annotations, core schema dicts,
  `FieldInfo`, etc.
- The frequently-quoted much larger numbers (~140 MiB *per side*) come from peak-RSS
  measurements and are dominated by **transient build allocations**, not retained
  duplication. Peak matters too (containers OOM on peak) — but the fix for peak is fewer
  build passes, not shared retained state.

### Why the unification itself buys little

1. The trees hold genuinely different per-node data (lookup keys/alias trees vs.
   serialization filters/computed fields); their topologies also diverge (the serializer
   skips wrapper nodes, `serialization` schema keys override structure), ruling out a 1:1
   merged-node tree.
2. `py_schema` / `py_config` were already the *same* Python objects on both sides —
   refcounts, not copies.
3. Leaf singletons and the prebuilt mechanism already dedup the cheap-to-share parts.
4. The remaining tree memory is dominated by **per-field machinery**: validator-side
   `Field` / `LookupPathCollection` / `LookupTree` (~650 B/field measured) and
   serializer-side `GeneralFieldsSerializer` (`AHashMap` + `SerField`, ~300 B/field), plus
   ~12.5k prebuilt wrapper nodes per side on k8s. None of that is validator↔serializer
   duplication.

## Recommended follow-ups (enabled by this structure)

1. **Lazy serializer construction** — build `SerializerPart` on first dump. Best
   effort-to-savings ratio: ~19.5 MiB retained + a chunk of build time on k8s; many apps
   never serialize most models. Needs a `OnceLock`-style part and a decision about when
   schema errors surface.
2. **Single-pass dual build** — one schema walk producing both trees. Attacks the transient
   allocation peak and import time (each build pass costs ~150–200 ms of the 1.75 s k8s
   import). Mechanical but large: every node type needs a combined build path.
3. **Shrink per-field structures** — the largest retained consumer; intra-structure work,
   orthogonal to unification.

## Files changed

- `pydantic-core/src/schema_core.rs` (new): `SchemaCoreData`, `SchemaCore` pyclass.
- `pydantic-core/src/validators/mod.rs`, `serializers/mod.rs`: pyclasses become views;
  build logic moved to `ValidatorPart` / `SerializerPart`; global intern pools.
- `pydantic-core/src/definitions.rs`: `InternKey`, `ChildKey`, per-build memo,
  `GlobalInternPool`.
- `nullable` / `list` / `with_default` build fns (both sides): interning call sites; leaf
  validators/serializers gained `intern_flags()` accessors.
- `pydantic/_internal/_model_construction.py`, `_dataclasses.py`, `type_adapter.py`,
  `plugin/_schema_validator.py`: build one `SchemaCore` per type, share the views.
- `pydantic_core/__init__.py`, `_pydantic_core.pyi`: export + stub for `SchemaCore`.
