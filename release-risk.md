# Release risk register (next major / high-impact release)

Prepared by scanning library source under `pydantic/` and `pydantic-core/` (lexicographic order). Focus: fragility for a **major** release (V3 / breaking core changes), not routine patch risk.

Each entry records **where** scanning paused, **why** the area is fragile, and **release implications**.

---


## Risk: CoreSchema closed vocabulary is the inter-package ABI

- **Scan pause:** `pydantic-core/python/pydantic_core/core_schema.py`:1
- **Severity (major release):** see body

**Severity:** Critical

`core_schema.py` (~4500 lines) defines every `type` string and TypedDict that Rust `build_validator` / `build_serializer` understand. Pydantic Python’s `GenerateSchema` only emits this closed set. A major release that renames nodes, removes deprecated validator factory aliases (`field_before_validator_function`, etc.), flips `CoreConfig` defaults (e.g. `serialize_by_alias`), or introduces mandatory new keys **forces a coordinated pydantic + pydantic-core release** and breaks any third party that hand-builds core schemas or subclasses schema generation.

**Why fragile:** Dual implementation (TypedDict docs vs Rust match arms) can drift; deprecation surface in this file is large (#980-era renames still present). `arguments-v3` is documented as “not used by other Pydantic components” yet awaits V3 promotion—dual arguments stacks increase maintenance risk.

**Release implications:** Freeze a schema IDL version; changelog every node change; run cross-package compatibility tests; plan `arguments` → `arguments-v3` migration in one major.

---

## Risk: Default by_alias=False expected to flip True in V3

- **Scan pause:** `pydantic-core/python/pydantic_core/_pydantic_core.pyi`:423
- **Severity (major release):** see body

**Severity:** High

Stubs explicitly document backwards-compatible defaults for `by_alias` on validation/serialization APIs, with comments that **Pydantic V3 is expected to default `by_alias` to `True` everywhere**. That changes the default wire shape of `model_dump` / JSON output and alias population behavior for the majority of models that define aliases but rely on default `by_alias=False` today.

**Why fragile:** Silent behavioral flip; OpenAPI generators, clients, and caches encode current defaults; easy to miss in tests that assert on Python attribute names rather than aliases.

**Release implications:** Feature flag period; explicit migration guide; consider requiring `serialize_by_alias` / `validate_by_alias` in config without implicit global default change; extensive ecosystem testing (FastAPI response models).

---

## Risk: PyO3 py-clone feature can panic

- **Scan pause:** `pydantic-core/Cargo.toml`:28
- **Severity (major release):** see body

**Severity:** Medium–High (correctness / crash)

Cargo.toml notes it would be “very nice to remove the `py-clone` feature as **it can panic**,” but needs work to ensure it is unused. Panics from the extension module abort the interpreter unless caught—unacceptable for a validation library used in servers.

**Why fragile:** Depends on PyO3 feature set and call patterns across validators/serializers; hard to audit completely; major PyO3 upgrades often accompany major pydantic-core releases.

**Release implications:** Audit/remove `py-clone` before major; add stress tests for objects that fail `__deepcopy__` / clone paths; pin PyO3 with known panic behavior documented.

---

## Risk: Input trait leaky abstraction across Python/JSON/strings

- **Scan pause:** `pydantic-core/src/input/input_abstract.rs`:250
- **Severity (major release):** see body

**Severity:** Medium

The shared `Input` trait powers one validator graph for Python objects, JSON (jiter), and string mappings. A FIXME calls out a **leaky abstraction**. Behavioral divergence (especially unions and literals) is already marked for V3 reconsideration in `input_json.rs` (“JSON str always win if in union”).

**Why fragile:** Fixing consistency is inherently breaking for users who depend on current JSON-vs-Python union matching; partial fixes create more edge cases; every new `Input` method multiplies implementations (`input_python`, `input_json`, `input_string`).

**Release implications:** Treat JSON/Python union policy as an explicit V3 decision with golden tests; avoid drive-by consistency tweaks in minors.

---

## Risk: JSON object key deduplication missing (jiter)

- **Scan pause:** `pydantic-core/src/input/input_json.rs`:291
- **Severity (major release):** see body

**Severity:** Medium

FIXME: jiter does not deduplicate keys; iteration may expose duplicate keys differently than Python dicts (which collapse keys). Security and correctness issue for adversarial or malformed JSON.

**Why fragile:** Depends on jiter version upgrades; deduping has performance cost; changing behavior may alter which value “wins” for duplicate keys—observable breakage.

**Release implications:** Coordinate with jiter; document last-key-wins vs error policy; add tests with duplicate keys.

---

## Risk: Alias / path lookup may be quadratic

- **Scan pause:** `pydantic-core/src/lookup_key.rs`:141
- **Severity (major release):** see body

**Severity:** Medium (performance / DoS surface)

FIXME notes `find_map` usage “probably leads to **quadratic complexity**” in alias/path resolution. Another FIXME questions Dict vs Mapping checks for attribute/key access.

**Why fragile:** AliasPath / AliasChoices are public APIs used on large payloads; performance cliffs appear only at scale; fixing may change which alias matches first when multiple paths exist.

**Release implications:** Benchmark alias-heavy models; fix complexity in a major if matching order changes; fuzz nested AliasPath.

---

## Risk: URL validation clones and disabled encode_credentials

- **Scan pause:** `pydantic-core/src/url.rs`:115
- **Severity (major release):** see body

**Severity:** Medium

Repeated FIXME to avoid `.clone()` when constructing URL subclasses; TODOs to re-enable `encode_credentials`. Subclass-aware validation is incomplete—network types in pydantic (`HttpUrl`, DSNs) sit on this.

**Why fragile:** Changing credential encoding or clone/identity behavior breaks URL equality, secrets in DSNs, and round-trips; `unsafe` pointer slicing for path prefixes adds review burden for majors.

**Release implications:** Complete subclass-aware validate; decide credential encoding policy once; extra tests for multi-host DSNs.

---

## Risk: Legacy PYDANTIC_ERRORS_OMIT_URL env var

- **Scan pause:** `pydantic-core/src/errors/validation_exception.rs`:210
- **Severity (major release):** see body

**Severity:** Low–Medium

Legacy env var still checked with deprecation toward `PYDANTIC_ERRORS_INCLUDE_URL`. Error URL formatting is part of operator/tooling contracts.

**Why fragile:** Dual env vars confuse deploy configs; removal in major breaks CI that sets omit URL.

**Release implications:** Remove legacy var in V3 with changelog; document new default for including/excluding doc URLs in errors.

---

## Risk: Computed fields unsupported on TypedDict serializers

- **Scan pause:** `pydantic-core/src/serializers/type_serializers/typed_dict.rs`:90
- **Severity (major release):** see body

**Severity:** Low–Medium (feature gap)

FIXME: computed fields do not work for TypedDict and may never. As TypedDict + `with_config` usage grows, users expect parity with models.

**Why fragile:** Closing the gap needs schema + serializer design; leaving it forever creates permanent inconsistency.

**Release implications:** Either implement or formally document as unsupported in V3.

---

## Risk: RootModel as JSON key serialization inconsistent

- **Scan pause:** `pydantic-core/src/serializers/type_serializers/model.rs`:269
- **Severity (major release):** see body

**Severity:** Low–Medium

FIXME: root model in JSON key position should serialize as inner value. Edge case but affects map keys and custom serializers.

**Release implications:** Fix as breaking edge-case alignment in major; add tests for dict keys of RootModel.

---

## Risk: Literal exactness differs for JSON inputs (V3 TODO)

- **Scan pause:** `pydantic-core/src/validators/literal.rs`:132
- **Severity (major release):** see body

**Severity:** Medium

V3 TODO to make literal matching “exact” for JSON inputs. Current laxness may accept types that become errors later.

**Release implications:** Golden tests for literal unions over JSON; communicate stricter JSON literals in V3.

---

## Risk: Dual arguments vs arguments-v3 validator stacks

- **Scan pause:** `pydantic-core/src/validators/arguments.rs`:1
- **Severity (major release):** see body

**Severity:** High (for validate_call / major cleanup)

Both `arguments` and `arguments_v3` modules exist; Python core_schema documents arguments-v3 as future. `_generate_schema.py` comments that current arguments schema will be replaced in V3 by `arguments-v3`.

**Why fragile:** Two code paths for one feature (`validate_call`); migration must not break signature binding, aliases on parameters, or varargs; easy to fix bugs only on one path.

**Release implications:** Single stack in V3; deprecate old arguments schema generation; expand arguments_v3 tests to full parity.

---

## Risk: ValidationState carries concerns that may not belong globally

- **Scan pause:** `pydantic-core/src/validators/validation_state.rs`:35
- **Severity (major release):** see body

**Severity:** Low–Medium

TODO suggests moving some state into structured types that need it. Growing global validation state increases coupling and makes partial validation / concurrency reasoning harder.

**Release implications:** Refactor in major with care for plugin and wrap-validator info APIs (`ValidationInfo` field names).

---

## Risk: Prebuilt validators/serializers and rebuild staleness

- **Scan pause:** `pydantic-core/src/common/prebuilt.rs`:1
- **Severity (major release):** see body

**Severity:** Medium

Prebuilt support (`_use_prebuilt` false on force rebuild—see pydantic-core #1894 class of bugs) avoids stale references but is easy to get wrong when models rebuild, generics parametrize, or plugins wrap validators.

**Why fragile:** Identity and cache invalidation across Python and Rust; major changes to model construction can reintroduce stale prebuilt pointers.

**Release implications:** Explicit tests for rebuild, generics, and create_model after field mutation; document when prebuilt is disabled.

---

## Risk: Lazy exports and deprecated dynamic imports of internals

- **Scan pause:** `pydantic/__init__.py`:420
- **Severity (major release):** see body

**Severity:** Medium

Package `__init__` lazy-loads almost everything; still exposes deprecated `GenerateSchema` / `FieldValidationInfo` via `__getattr__` with warnings. `__all__` includes long-deprecated V1 APIs (`validator`, `BaseConfig`, `parse_obj_as`).

**Why fragile:** Users and type checkers rely on lazy export graphs; removing names breaks imports even if undocumented; exporting internals teaches bad coupling.

**Release implications:** V3 remove deprecated dynamic imports and V1 names from top-level; shrink `__all__` to true stable surface.

---

## Risk: Large V1→V2 migration matrix must become V2→V3 matrix

- **Scan pause:** `pydantic/_migration.py`:1
- **Severity (major release):** see body

**Severity:** High (migration UX)

Maps MOVED / DEPRECATED_MOVED / REDIRECT_TO_V1 / REMOVED_IN_V2 drive `getattr_migration` for many shim modules. Next major needs an analogous, tested matrix or deliberate hard breaks.

**Why fragile:** Incomplete maps cause opaque ImportError vs helpful redirects; dual maintenance with `deprecated/` and `v1/`.

**Release implications:** Design V3 migration module early; decide fate of `pydantic.v1` (keep, separate package, or drop).

---

## Risk: ConfigWrapper patches for backwards-compatible settings

- **Scan pause:** `pydantic/_internal/_config.py`:184
- **Severity (major release):** see body

**Severity:** Medium

Internal config normalization carries patches explicitly for backwards compatibility (settings to be deprecated in v3 / removed later). Diverges from documented `ConfigDict` and core `CoreConfig`.

**Why fragile:** Silent reinterpretation of user config; major cleanup changes runtime without import errors.

**Release implications:** List every compatibility patch; remove in V3 with migration notes.

---

## Risk: ClassVar / field classification may change in V3

- **Scan pause:** `pydantic/_internal/_fields.py`:390
- **Severity (major release):** see body

**Severity:** High

Comments warn some names treated as class variables now will be **normal fields in V3** to align with dataclasses. Also interacts with deprecated instance method names used as fields.

**Why fragile:** Changes which annotations become validated fields—data model shape changes; hard to detect without schema snapshots.

**Release implications:** Codemod or warning in 2.x when annotations would flip; snapshot `model_fields` keys in tests.

---

## Risk: GenerateSchema monolith — highest Python-side release risk

- **Scan pause:** `pydantic/_internal/_generate_schema.py`:1
- **Severity (major release):** see body

**Severity:** Critical

~2800+ line compiler from Python types to CoreSchema. Contains V3 TODOs (remove deprecated decorator helpers), FastAPI-specific HACKs (suppress warnings for FieldInfo subclasses), incomplete serialization triggers (“ugly hack” for Any serialization), dual arguments schema builders, support for deprecated `__get_validators__` / `__modify_schema__`, and deep coupling to public `main`/`fields`/`types` via `import_cached_*`.

**Why fragile:** Any type-system or core-schema change lands here; regressions are subtle (wrong node, missing ref, broken generics); public↔internal import cycles force careful init order.

**Release implications:** Prioritize characterization tests / schema golden files before V3 refactors; remove deprecated branches only when V1 decorators die; replace FastAPI HACKs with explicit extension API; finish arguments-v3 migration here in lockstep with core.

---

## Risk: defer_build mocks and incomplete models

- **Scan pause:** `pydantic/_internal/_model_construction.py`:257
- **Severity (major release):** see body

**Severity:** Medium

`defer_build` installs mock validators; incomplete annotations set mocks and `__pydantic_complete__ = False`. Production misconfig leads to errors only on first use; rebuild semantics interact with generics and plugins.

**Why fragile:** Timing of completion differs from eager build; plugins may not run until rebuild; major changes to completion hooks break frameworks using deferred models.

**Release implications:** Clear V3 semantics for defer_build; test plugin + defer_build; fail fast options.

---

## Risk: Alias generator parameter names change planned for V3

- **Scan pause:** `pydantic/alias_generators.py`:7
- **Severity (major release):** see body

**Severity:** Low

TODO: in V3 change argument names to be more descriptive. Pure renaming break for callables passed as `alias_generator` if they use keyword args.

**Release implications:** Accept only positional or use a Protocol with stable names.

---

## Risk: Color deprecated in favor of pydantic_extra_types

- **Scan pause:** `pydantic/color.py`:73
- **Severity (major release):** see body

**Severity:** Low (removal risk)

In-tree `Color` is deprecated. Apps still importing `pydantic.color` or top-level if re-exported need migration.

**Release implications:** Remove in V3; ensure extra_types parity.

---

## Risk: ConfigDict keys deprecated for V3 (populate_by_name, ser_json_timedelta, …)

- **Scan pause:** `pydantic/config.py`:193
- **Severity (major release):** see body

**Severity:** High

Multiple keys marked for deprecation/removal in V3: `populate_by_name` (prefer `validate_by_name` / `validate_by_alias` split), `ser_json_timedelta` (prefer `ser_json_temporal`), old `json_encoders` path (elsewhere), keyword `config=` on helpers. Defaults interacting with `by_alias` compound the risk.

**Why fragile:** Config is global per model; wrong migration changes validation and serialization together; frameworks copy ConfigDict blobs.

**Release implications:** Emit stronger warnings in last 2.x; provide config upgrade guide; reject removed keys in V3 with clear errors.

---

## Risk: FieldInfo merge HACKs for FastAPI and partial models

- **Scan pause:** `pydantic/fields.py`:431
- **Severity (major release):** see body

**Severity:** Critical (ecosystem)

HACK 1: inconsistent metadata merge order requires prepend. HACK 2: FastAPI subclasses `FieldInfo` and expects default FieldInfo instances in metadata. Additional HACK for “make model partial” utilities mutating fields. Deprecated `merge_field_infos`. PEP 747 TODOs for TypeForm. Deprecated Field kwargs (`min_items`, `extra`, …).

**Why fragile:** FastAPI (and clones) depend on undocumented FieldInfo layout; fixing “proper” merge **breaks FastAPI** unless coordinated; partial-model utilities depend on mutation semantics.

**Release implications:** Joint FastAPI–Pydantic V3 design for FieldInfo; formalize metadata merge algorithm; version gate subclass expectations; extensive FastAPI test suite in CI for majors.

---

## Risk: Implicit classmethod on validators — V3 behavior change for after validators

- **Scan pause:** `pydantic/functional_validators.py`:722
- **Severity (major release):** see body

**Severity:** Medium

NOTE: in V3, do not apply classmethod conversion for `after` validators the same way. Changes how validators receive `cls`/`self`.

**Release implications:** Document callable signatures for V3; detect instance methods vs functions.

---

## Risk: JSON Schema examples dict form removed in V3; generator complexity

- **Scan pause:** `pydantic/json_schema.py`:2761
- **Severity (major release):** see body

**Severity:** Medium–High

`Examples` dict form deprecated since v2.9, removed in v3. `GenerateJsonSchema` is huge and tracks every core schema kind—core additions require parallel Python updates. Ref/defs remapping is subtle; OpenAPI tools pin output shape.

**Why fragile:** JSON Schema is a public compatibility surface for codegen; cosmetic changes break golden files across the ecosystem.

**Release implications:** Snapshot testing; versioned JSON Schema dialect notes; remove dict examples in V3.

---

## Risk: BaseModel still carries V1 private methods and deprecated instance APIs

- **Scan pause:** `pydantic/main.py`:1672
- **Severity (major release):** see body

**Severity:** Medium

Deprecated `_iter`, `_copy_and_set_values`, etc., and V1-style instance methods still present for compatibility. Instance access to some class attributes warns removal in V3 (`_utils.deprecated_instance_property`).

**Why fragile:** Removal is correct for cleanliness but breaks old middleware and “pydantic helpers” copying V1 patterns.

**Release implications:** Final removal list in V3 migration guide; optional compatibility shim package.

---

## Risk: Mypy plugin path debt and type-ops during analysis

- **Scan pause:** `pydantic/mypy.py`:848
- **Severity (major release):** see body

**Severity:** Medium (DX)

TODOs on removing paths (issue #11119), type operations during semantic analysis, implicit classmethod handling. Plugin tracks mypy versions—major mypy releases break users independently of pydantic runtime.

**Release implications:** Align V3 with supported mypy versions; reduce plugin surface; test matrix.

---

## Risk: Plugin protocol is a binary compatibility surface

- **Scan pause:** `pydantic/plugin/__init__.py`:41
- **Severity (major release):** see body

**Severity:** Medium

`PydanticPluginProtocol.new_schema_validator` signature includes schema, paths, kind, config, settings. Integrators (e.g. Logfire) implement entry points. Changing when validators are built (defer_build, prebuilt) changes hook frequency.

**Release implications:** Version plugin API; avoid signature breaks in majors without adapter period.

---

## Risk: TypeAdapter experimental constructor options

- **Scan pause:** `pydantic/type_adapter.py`:97
- **Severity (major release):** see body

**Severity:** Low–Medium

Docs note some constructor options may be deprecated in a minor if misused. TypeAdapter is the replacement for `parse_obj_as`—behavior must stay stable through major while deprecated tools vanish.

**Release implications:** Stabilize constructor; lock validate/dump parity with BaseModel where documented.

---

## Risk: con* helpers and PaymentCardNumber deprecated toward V3 / extra_types

- **Scan pause:** `pydantic/types.py`:170
- **Severity (major release):** see body

**Severity:** Medium

Multiple `con*` functions documented to be deprecated in 3.0 in favor of Annotated constraints; `PaymentCardNumber` deprecated to pydantic_extra_types. Wide usage in tutorials and generated code.

**Release implications:** Provide Annotated equivalents in migration docs; remove in V3 or keep as thin wrappers.

---

## Risk: Entire pydantic.v1 tree is a second implementation

- **Scan pause:** `pydantic/v1/`:1
- **Severity (major release):** see body

**Severity:** High (product / maintenance)

Full V1 pure-Python stack ships beside V2. Hypothesis plugin leaks imports into modern `color`/`types`. Doubles security and bugfix surface; confuses “which BaseModel”.

**Why fragile:** Decision to drop, freeze, or split out affects migration narrative for V3; any change to package layout breaks `from pydantic.v1 import …`.

**Release implications:** Explicit V3 policy for v1 submodule; consider separate `pydantic-v1` package; fix hypothesis plugin isolation before removal.

---

## Risk: Experimental APIs may graduate or vanish

- **Scan pause:** `pydantic/experimental/pipeline.py`:1
- **Severity (major release):** see body

**Severity:** Low for core, Medium for early adopters

Pipeline API and `generate_arguments_schema` are provisional. If arguments-v3 work lands, experimental paths may be deleted or become the only path.

**Release implications:** Do not promise stability; if promoting pipeline, do so deliberately in major with rename.

---

## Risk: Exact pydantic-core version pin

- **Scan pause:** `pydantic/version.py`:21
- **Severity (major release):** see body

**Severity:** Operational High

`_COMPATIBLE_PYDANTIC_CORE_VERSION` must match `pyproject.toml` pin. Majors often require **simultaneous** core major; mismatch fails at import via `_ensure_pydantic_core_version`.

**Why fragile:** Downstream pins pydantic without unlocking core; vendoring systems break; conda/docker layers skew.

**Release implications:** Single release train; clear upgrade order; consider compatible range only if schema ABI guarantees hold.

---

## Scan coverage notes

Lexicographic scan focused on library sources under:

- `pydantic-core/python/pydantic_core/`
- `pydantic-core/src/**/*.rs`
- `pydantic/**/*.py` (including `_internal`, `deprecated`, `experimental`, `plugin`, `v1`)

Tests, docs pages, and release scripts were not treated as primary fragility sources for *runtime* major-release risk (except where they document V3 intent). Not every file produced a risk entry; files without HACK/TODO/V3/deprecation or architectural coupling notes were skipped after inspection for markers and structural role.

## Top priorities before next major

1. **FieldInfo / FastAPI metadata contract** (`fields.py` HACKs + `_generate_schema` subclass warning suppression).
2. **CoreSchema ABI + defaults** (`by_alias`, `serialize_by_alias`, JSON vs Python unions, literals).
3. **GenerateSchema cleanup** (remove deprecated decorator/__get_validators__ paths; arguments-v3 only).
4. **ConfigDict key removals** and compatibility patches in `ConfigWrapper`.
5. **ClassVar vs field classification** flip (`_fields.py`).
6. **`pydantic.v1` and deprecated export** removal policy.
7. **PyO3 `py-clone` panic** and lookup_key performance.
8. **Exact core version pin** / release orchestration.

## Suggested V3 risk-reduction process

- Maintain a living “breaking change” checklist mapped to files above.
- Golden-file core schemas + JSON schemas for representative models (aliases, unions, RootModel, validate_call, TypedDict).
- Nightly or PR CI job running FastAPI’s pydantic-dependent tests against pydantic HEAD.
- Import-linter: forbid new references to `deprecated` and `v1` from `_internal` except allowlists.
- Feature flags for behavioral flips (`by_alias` default, stricter JSON literals) in final 2.x minors.
