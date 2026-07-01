# Proposed tests to add: nested pipeline operators

**Context:** Follow-up to [#13287](https://github.com/pydantic/pydantic/issues/13287) / [#13363](https://github.com/pydantic/pydantic/pull/13363) (*Fix application of nested operators in pipeline API*). Nested `|` / `&` now compile via `_apply_pipeline` instead of `handler(inner_pipeline)`.

**Target file:** `tests/test_pipeline.py` (alongside `test_nested_composition` and `test_nested_composition_transform`).

**Goal:** Keep coverage focused—lock semantics and failure modes of **nested** composition without re-parametrizing the entire pipeline suite.

**Imports already used in the file** (extend as needed):

```python
from typing import Annotated
from pydantic import BaseModel, TypeAdapter, ValidationError
from pydantic.experimental.pipeline import transform, validate_as
```

---

## Current coverage (for review)

| Test | Covers |
| ---- | ------ |
| `test_composition` | Flat `\|` / `&`, mid-chain `transform`, successes and failures, call ordering |
| `test_nested_composition` | `(validate_as(int) \| validate_as(str)) & validate_as(int)` — success for `42` only |
| `test_nested_composition_transform` | Same union then `transform(+1)` — success for `42` → `43` only |

**Gaps:** failure inputs, opposite association `A | (B & C)`, deeper nesting, `BaseModel` (issue reproducer), method-form `otherwise`/`then`, constraints under recursion, optional JSON.

---

## Priority legend

- **P0** — Strongly recommended; matches the bug report or locks behavior that could regress silently.
- **P1** — High value; structural variants of the fix.
- **P2** — Nice to have; broader confidence.

---

## P0 — Issue mirror and failure modes

### 1. `test_nested_composition_on_basemodel`

**Why:** Issue #13287 used `BaseModel.model_validate`, not `TypeAdapter`. Same schema path in practice, but a model regression matches the report and protects metaclass / field attachment.

```python
def test_nested_composition_on_basemodel() -> None:
    """Regression for https://github.com/pydantic/pydantic/issues/13287."""

    class M(BaseModel):
        some_int: Annotated[int, (validate_as(int) | validate_as(int)) & validate_as(int)]

    assert M.model_validate({'some_int': 42}).some_int == 42
```

(Use `| validate_as(str)` instead of a second `validate_as(int)` if you want parity with the TypeAdapter nested tests.)

---

### 2. `test_nested_composition_failures`

**Why:** Nested tests only assert success. Failures ensure union/chain still reject bad input and that schema generation did not “succeed” with a broken validator.

```python
def test_nested_composition_failures() -> None:
    ta = TypeAdapter[int](Annotated[int, (validate_as(int) | validate_as(str)) & validate_as(int)])

    with pytest.raises(ValidationError):
        ta.validate_python(None)
    with pytest.raises(ValidationError):
        ta.validate_python([1])
    with pytest.raises(ValidationError):
        ta.validate_python({'x': 1})
```

**Review note:** Exact error types/locations need not be asserted unless you want stricter snapshots later.

---

### 3. `test_nested_composition_str_branch`

**Why:** `(int | str) & int` should accept values that only pass the **str** arm of the union, then succeed (or fail) on the following `validate_as(int)`. This locks **intended coercion/chain semantics**, not only “no AttributeError.”

```python
def test_nested_composition_str_branch() -> None:
    ta = TypeAdapter[int](Annotated[int, (validate_as(int) | validate_as(str)) & validate_as(int)])

    # String that parses as int through the chain after the union
    assert ta.validate_python('42') == 42

    with pytest.raises(ValidationError):
        ta.validate_python('not-an-int')
```

**Review note:** Confirm this matches product intent when reviewing. If maintainers prefer the str arm *not* to feed `validate_as(int)` this way, adjust expectations—but **some** explicit str-branch assertion should exist.

---

## P1 — Alternate association and deeper nesting

### 4. `test_nested_or_of_ands`

**Why:** The bug/fix centered on `(A | B) & C` (and-of-or). The recursive `_apply_pipeline` path must also handle **`A | (B & C)`** (or-of-and)—different tree shape, same mechanism.

```python
def test_nested_or_of_ands() -> None:
    ta = TypeAdapter[int](
        Annotated[
            int,
            validate_as(int).lt(0) | (validate_as(int).gt(10) & validate_as(int).lt(20)),
        ]
    )

    assert ta.validate_python(-1) == -1
    assert ta.validate_python(15) == 15

    with pytest.raises(ValidationError):
        ta.validate_python(5)  # neither < 0 nor in (10, 20)
    with pytest.raises(ValidationError):
        ta.validate_python(10)  # gt(10) fails at boundary
    with pytest.raises(ValidationError):
        ta.validate_python(20)  # lt(20) fails at boundary
```

**Review note:** Boundary expectations depend on `gt`/`lt` (strict). Adjust if you use `ge`/`le` for simpler numbers.

---

### 5. `test_doubly_nested_pipelines`

**Why:** Ensures recursion depth > 1 (nested operand that itself contains `|` / `&`).

```python
def test_doubly_nested_pipelines() -> None:
    ta = TypeAdapter[int](
        Annotated[
            int,
            ((validate_as(int) | validate_as(str)) & validate_as(int)) | validate_as(int).gt(100),
        ]
    )

    assert ta.validate_python(1) == 1
    assert ta.validate_python(101) == 101

    with pytest.raises(ValidationError):
        ta.validate_python(None)
```

---

### 6. `test_nested_composition_method_form`

**Why:** `|` / `&` are aliases of `otherwise` / `then`. Guarantees the fix is not accidentally operator-specific (it isn’t today, but documents the public method API).

```python
def test_nested_composition_method_form() -> None:
    pipe = validate_as(int).otherwise(validate_as(str)).then(validate_as(int))
    ta = TypeAdapter[int](Annotated[int, pipe])

    assert ta.validate_python(42) == 42
    assert ta.validate_python('7') == 7
```

---

## P1 — Nested + transform / constraints under recursion

### 7. `test_nested_composition_transform_failures`

**Why:** Complements `test_nested_composition_transform` with a failing input so transform isn’t only tested on the happy path.

```python
def test_nested_composition_transform_failures() -> None:
    ta = TypeAdapter[int](
        Annotated[int, (validate_as(int) | validate_as(str)) & transform(lambda v: v + 1)]
    )

    with pytest.raises(ValidationError):
        ta.validate_python(None)
```

**Review note:** If `transform` runs only after a successful union member, behavior for odd types should be whatever union+chain defines; asserting `ValidationError` for `None` is the minimum.

---

### 8. `test_nested_composition_with_constraints`

**Why:** Exercises `_apply_constraint` when the constrained pipeline is an operand of `|` / `&` (recursion through constraint steps, not only `validate_as` / `transform`).

```python
def test_nested_composition_with_constraints() -> None:
    ta = TypeAdapter[int](
        Annotated[
            int,
            (validate_as(int).gt(0) | validate_as(int).lt(0)) & validate_as(int).ne(0),
        ]
    )

    assert ta.validate_python(1) == 1
    assert ta.validate_python(-1) == -1

    with pytest.raises(ValidationError):
        ta.validate_python(0)
```

**Review note:** `ne` must exist on the pipeline API (`not_eq` / predicate)—align method names with `pipeline.py` (`eq` / `not_eq` / `predicate`). Adjust to:

```python
(validate_as(int).gt(0) | validate_as(int).lt(0)) & validate_as(int)  # simpler
# plus .predicate(lambda x: x != 0) if needed
```

Prefer APIs already covered in `test_not_eq` / `test_eq` in the same file.

**Safer variant using existing patterns:**

```python
def test_nested_composition_with_constraints() -> None:
    ta = TypeAdapter[int](
        Annotated[
            int,
            (validate_as(int).ge(10) | validate_as(int).le(-10)) & validate_as(int).not_eq(0),
        ]
    )
    # Use whatever method name test_not_eq uses (e.g. not_eq / != helper)
```

Cross-check `test_not_eq` in `tests/test_pipeline.py` before landing.

---

## P2 — Optional extras

### 9. `test_nested_composition_json`

**Why:** JSON vs Python input can diverge in core; low priority for an experimental pipeline fix but cheap confidence.

```python
def test_nested_composition_json() -> None:
    ta = TypeAdapter[int](Annotated[int, (validate_as(int) | validate_as(str)) & validate_as(int)])

    assert ta.validate_json('42') == 42
    with pytest.raises(ValidationError):
        ta.validate_json('null')
```

---

### 10. `test_nested_composition_builds_schema`

**Why:** Separates “schema generation does not raise” from “validate accepts value” (closer to the original crash, which happened at build time).

```python
def test_nested_composition_builds_schema() -> None:
    ta = TypeAdapter[int](Annotated[int, (validate_as(int) | validate_as(str)) & validate_as(int)])

    schema = ta.core_schema
    assert schema is not None
    # Optional: smoke JSON schema
    assert isinstance(ta.json_schema(), dict)
```

---

### 11. Nested transform call-order (optional, heavier)

Only if you want parity with `test_composition`’s `calls` list for a **nested** graph. Probably overkill unless debugging ordering bugs.

```python
def test_nested_composition_transform_call_order() -> None:
    calls: list[str] = []

    def tag(name: str):
        def inner(x: int) -> int:
            calls.append(name)
            return x
        return inner

    ta = TypeAdapter[int](
        Annotated[
            int,
            (validate_as(int).transform(tag('L')) | validate_as(str).transform(tag('R')))
            & transform(tag('AFTER')),
        ]
    )
    assert ta.validate_python(1) == 1
    assert calls == ['L', 'AFTER']  # confirm expected union short-circuit
    calls.clear()
```

**Review note:** Exact `calls` depend on union try-order and whether str arm runs; treat as documentation of current behavior, not sacred.

---

## Suggested landing set (minimal PR)

If you want a small, high-signal addition only:

1. `test_nested_composition_on_basemodel` (P0)
2. `test_nested_composition_failures` (P0)
3. `test_nested_composition_str_branch` (P0 — after agreeing on str→int behavior)
4. `test_nested_or_of_ands` (P1)
5. `test_doubly_nested_pipelines` (P1)
6. `test_nested_composition_method_form` (P1)

Defer P2 unless you want extra smoke coverage.

---

## What not to add (recommendation)

- Full parametrize of every constraint × nest depth (noisy, low ROI for experimental API).
- Duplicating all of `test_composition` with extra parentheses around flat pipelines.
- Snapshotting full `core_schema` dicts (brittle across core versions).

---

## How to run after adding

```bash
uv run pytest tests/test_pipeline.py -q
```

Baseline on current `main` (with #13363): **66 passed**. New tests should increase that count accordingly.

---

## Open questions for reviewers

1. For `(validate_as(int) | validate_as(str)) & validate_as(int)`, should `'42'` succeed with `42`? (Affects P0 #3.)
2. Do we want `BaseModel` + `TypeAdapter` both, or is `BaseModel` alone enough for the issue mirror?
3. Any interest in `validate_as_deferred` under nesting? (Probably P2 / out of scope unless someone hit it.)

---

## Implementation status

Applied to `tests/test_pipeline.py` with reviewer preferences:

- Prefer **`BaseModel`** for nested-operator tests (TypeAdapter retained on the two original nested tests).
- Use **`validate_as(str)`** in unions where relevant.
- Include **`validate_as_deferred`** cases: `test_nested_composition_validate_as_deferred`, `test_nested_or_of_ands_validate_as_deferred`.

Run: `uv run pytest tests/test_pipeline.py -q`
