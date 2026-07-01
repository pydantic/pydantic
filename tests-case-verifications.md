# Test case verifications

Companion log of tests under `tests/` that appear **logically incorrect**, **mis-aimed**, or **weak relative to their stated intent** (wrong assumptions, vacuous checks, mismatched assertions, etc.).

Process: scan files lexicographically; for each questionable case, record path, issue, and probable fix.

**Scope note:** Full line-by-line review of every assertion in 12k+ tests is not practical in one pass; this register prioritizes concrete defects and systematically weak patterns found while reading suites. Entries are judgment calls for human review.

## Implementation status

Fixes applied in-repo (see commits/working tree):

| Item | Status |
| ---- | ------ |
| TypeAdapter\[int\]→\[str\] for string pipeline tests | Done |
| `test_nested_composition_with_constraints` distinguishing `not_eq` | Done |
| `test_nested_composition_builds_schema` structure asserts | Done |
| TypeAdapter nested tests str branch | Done |
| `test_discriminated_single_variant` remove noop parametrize | Done |
| `test_public_api_dynamic_imports` identity assert | Done |
| `test_invalid_json_schema_raises` document + expect raise | Done |
| RootModel `validate_assignment_false` clarify | Done |
| `test_init_export` also checks `__all__` | Done |
| TypedDict computed field xfail note | Done |
| PaymentCard legacy suite note | Done |

---


## `test_not_eq / test_eq / test_not_in / test_in / test_predicates (TypeAdapter generic)`

- **File:** `tests/test_pipeline.py`
- **Issue:** Tests declare `TypeAdapter[int]` but annotate/validate **strings** (`Annotated[str, ...]`, inputs like `'potato'`). The type parameter is wrong and does not check that the adapter's static/output type matches runtime validation. This is a misleading type annotation / wrong assumption that the adapter is for `int`.
- **Probable fix:** Use `TypeAdapter[str](Annotated[str, ...])` (or drop the incorrect type arg) so the test's declared type matches what is actually validated.

---

## `test_nested_composition_with_constraints`

- **File:** `tests/test_pipeline.py`
- **Issue:** Pipeline is `(gt(0) | lt(0)) & not_eq(0)`. Values equal to `0` already fail the **union** (`gt(0)` and `lt(0)` both reject 0), so the final `not_eq(0)` arm is never the distinguishing failure mode. Asserting `ValidationError` for `0` does **not** verify that nested `&` applies `not_eq`; it only re-checks the union.
- **Probable fix:** Either remove redundant `not_eq(0)`, or construct a case where the union accepts a value that `not_eq` must reject (e.g. union of two branches that both allow a sentinel the and-step rejects), or assert error details proving the failing step.

---

## `test_nested_composition_builds_schema`

- **File:** `tests/test_pipeline.py`
- **Issue:** `assert M.__pydantic_core_schema__ is not None` is nearly vacuous for any successfully defined `BaseModel` subclass—the class body would have failed earlier if schema build crashed (the original bug). It does not assert schema **shape** (union/chain nodes) or that nested operators appear in the schema.
- **Probable fix:** Assert structural properties of the core schema (e.g. presence of `union`/`chain` types via a small walker), or rely on validation tests alone and drop the vacuous `is not None` check. Keep `model_json_schema()` only if asserting keys/types.

---

## `test_nested_composition / test_nested_composition_transform`

- **File:** `tests/test_pipeline.py`
- **Issue:** Only exercise the **int** arm of `(int | str)` with input `42`. They never hit the str branch of the union, so they under-test the nested composition they introduced (str path is only covered in later BaseModel tests).
- **Probable fix:** Add at least one str-input assertion on these TypeAdapter tests for parity, or document that BaseModel tests own str-branch coverage and keep TA tests minimal on purpose.

---

## `test_discriminated_single_variant`

- **File:** `tests/test_discriminated_union.py`
- **Issue:** Parametrized with `union: [True, False]` but **both branches set identical annotations** (`x: InnerModel = Field(discriminator='qwe')`). The parameter never changes behavior—two identical tests. Wrong assumption that `union=True/False` exercises different code paths.
- **Probable fix:** Make branches differ (e.g. `x: InnerModel | Other` vs single variant), or remove the useless parametrization and keep one test.

---

## `test_public_api_dynamic_imports`

- **File:** `tests/test_exports.py`
- **Issue:** For non-module imports, asserts `isinstance(imported_object, object)`, which is **true for every Python object**. Does not verify the imported symbol is the intended object, only that getattr succeeded without raising.
- **Probable fix:** Compare to a known reference (e.g. `imported_object is getattr(expected_module, attr_name)`) or assert type/module/qualname for critical exports.

---

## `test_invalid_json_schema_raises`

- **File:** `tests/test_meta.py`
- **Issue:** Marked `xfail` when **not** on emscripten (i.e. fails on normal platforms by design). On typical CI (linux/mac), the test is expected to fail rather than enforcing that invalid JSON schema **raises**. Inverted/confusing intent: it documents broken behavior instead of asserting the desired raise on the primary platforms.
- **Probable fix:** Invert the condition if the goal is to require raises on CPython/desktop; or rename/restructure as an explicit known-failure tracking test with a linked issue, not a meta test implying validation of invalid schemas.

---

## `test_validate_assignment_false (RootModel)`

- **File:** `tests/test_root_model.py`
- **Issue:** With default `validate_assignment=False`, assigns `m.root = 'abc'` on `RootModel[int]` and asserts `m.root == 'abc'` (string on an int root). Correctly reflects current config, but the test **does not document** that this bypasses type validation—readers may think RootModel always stores validated ints. Easy to misread as asserting int acceptance of str.
- **Probable fix:** Rename/clarify with a comment that assignment skips validation; optionally assert `type(m.root) is str` to make the non-validation explicit. Add contrast with `validate_assignment=True` test (already adjacent).

---

## `test_init_export`

- **File:** `tests/test_exports.py`
- **Issue:** Only does `getattr(pydantic, name)` for `dir(pydantic)` with deprecation warnings ignored. Does not assert successful resolution of `__all__` members specifically, nor that exports match public API inventory—weak smoke test that can miss missing exports if they are absent from `dir()`.
- **Probable fix:** Parametrize over `pydantic.__all__` and assert each name resolves and (optionally) appears in `dir`.

---

## `test_multiple_references_to_schema (TypedDict xfail)`

- **File:** `tests/test_computed_fields.py`
- **Issue:** Includes `make_typed_dict` under `xfail` because computed fields do not work on TypedDict. The test name claims coverage of multiple schema references across model factories, but TypedDict path never asserts success—permanent xfail masks incomplete implementation without failing CI when behavior changes unexpectedly (xfail pass would only warn).
- **Probable fix:** Track as explicit issue; consider `pytest.mark.skip` until supported, or split TypedDict into a dedicated expected-failure module with clearer ownership.

---

## `PaymentCard tests vs deprecation`

- **File:** `tests/test_types_payment_card_number.py`
- **Issue:** Full suite still tests deprecated `PaymentCardNumber` in pydantic core package (with filterwarnings). Not wrong per se, but assumes in-tree type remains the implementation under test long-term while product directs users to `pydantic_extra_types`—risk of maintaining tests for code slated for removal without testing the replacement.
- **Probable fix:** Mirror critical cases against `pydantic_extra_types` when available, or mark module as legacy-only with a removal ticket.

---
