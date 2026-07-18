# Implementation Walkthrough

## Phase 1: API Plumbing (Complete)

### Python API changes
- `pydantic/main.py`: Added `aggregate_errors: bool | None = None` to
  `BaseModel.model_validate`, `model_validate_json`, and `model_validate_strings`.
- `pydantic/type_adapter.py`: Added the same parameter to `TypeAdapter.validate_python`,
  `validate_json`, and `validate_strings`.

### Rust changes (`pydantic-core/src/validators/`)
- `mod.rs`: Added `pub aggregate_errors: Option<bool>` to `Extra`.
- `mod.rs`: Updated `_validate` and `_validate_json` to thread `aggregate_errors` through.
- `mod.rs`: Updated `SchemaValidator::validate_python`, `validate_json`, and
  `validate_strings` signatures.
- `generator.rs`: Updated `Extra` initializations.
- `url.rs`: Passed `None` for `aggregate_errors` in unrelated `Extra::new` call sites.
- `validate_assignment` and `get_default_value`: Both set `aggregate_errors: None`
  explicitly in their struct-literal `Extra` constructions.

### Plugin compatibility
No plugin protocol signatures changed. `aggregate_errors` is filtered inside
`_schema_validator.py` before invoking third-party plugin callbacks.
The internal Rust call receives the full keyword arguments unchanged.
Existing plugin tests (`tests/test_plugins.py`) pass without modification in the
local development environment.

## Phase 2: String Validation Surgical Slice (Complete)

In Phase 2, we isolated the scope to just `StrConstrainedValidator` in Rust,
while avoiding any extra abstraction overhead. The logic checks whether
`aggregate_errors` is true or omitted.

### String Constraint Scope Contract

When `aggregate_errors=True`, constrained string validation aggregates only
`min_length` and `pattern` failures evaluated for the same transformed string
value. `ascii_only`, `max_length`, type conversion, and all other constraint
families preserve their existing behavior. `strip_whitespace` retains its
existing pre-constraint transform behavior; `to_lower` and `to_upper` retain
their existing post-validation transform behavior. This is intentionally not a
general exhaustive-validation framework.

## Out of scope

This benchmark does not require a general exhaustive-validation framework.

Excluded behavior includes:
- `max_length` aggregation
- Numeric, bytes, collection, date/time, and other non-string constraints
- Custom field-validator aggregation
- Model-validator aggregation
- Union branch-policy changes
- Constructor, assignment-validation, settings, and serialization changes

Only constrained-string `min_length` and `pattern` failures are aggregated
when `aggregate_errors=True`.

### Source invariants (verified by inspection)

- Omitted / `False` enters the original fail-fast path.
- `True` is the only path allocating `Vec<ValLineError>`.
- `min_length` and `pattern` construct the same errors (same input, context) as fail-fast.
- `strip_whitespace` runs before both eligible checks.
- `to_lower` / `to_upper` keep existing post-validation timing.
- `max_length` and `ascii_only` retain fail-fast / early-exit behavior in aggregate mode.
- `ValError::LineErrors(errors)` is reached only when `errors` is nonempty.

### Lint and format status

`cargo fmt --check` and `git diff --check` exit 0. `cargo clippy --all-targets
--all-features -- -D warnings` exits nonzero on both the baseline commit and
the feature branch due to pre-existing diagnostics in files outside the feature
diff (`lookup_key.rs`, `input_abstract.rs`, `input_python.rs`,
`input_string.rs`). The project's own CI lint gate runs through `pre-commit`,
not bare Clippy with `-D warnings`. Baseline-versus-feature Clippy log
comparison inside Docker (same toolchain) confirmed no new diagnostics were
introduced by this change.

### Test validation

22 regression tests in `tests/test_aggregate_errors.py`:

- `test_aggregate_errors_plumbing`
- `test_model_validate_accepts_aggregate_errors_for_valid_input`
- `test_aggregate_errors_false_matches_omitted`
- `test_aggregate_errors_does_not_leak_between_calls`
- `test_type_adapter_accepts_aggregate_errors`
- `test_plugin_without_aggregate_errors_parameter_remains_compatible`
- `test_single_constraint_still_reports_one_error`
- `test_string_constraints_aggregation`
- `test_ascii_only_is_terminal_before_aggregation`
- `test_aggregate_mode_does_not_affect_max_length`
- `test_aggregate_errors_with_strip_whitespace`
- `test_json_parity`
- `test_strict_mode_parity`
- `test_aggregate_errors_false_matches_omitted_for_strings` (5 parametrized cases)
- `test_model_validate_strings_aggregates`
- `test_type_adapter_validate_json_aggregates`
- `test_type_adapter_validate_strings_aggregates`
- `test_aggregate_errors_valid_input_returns_no_errors`

## Docker Offline Verification

### Build
- Image: `olympus-pydantic-aggregate-errors`
- Base: `python:3.13-slim`, Rust stable, uv
- Cloned pydantic at pinned SHA `cf67d4b3193c3fe43ede18612ed62785eee11382`
- Applied `solution.patch` and `tests.patch` at build time
- Compiled Rust extension via `uv run maturin develop --uv` at build time
- 10 Rust warnings during compilation — all pre-existing `LookupPath` visibility
  issues in `lookup_key.rs`, `input_abstract.rs`, `input_json.rs`, `input_python.rs`,
  `input_string.rs`. None in modified files.

### Offline test results (`docker run --rm --network none`)

| Stage | Result |
|---|---|
| Extension provenance | `/workspace/pydantic-core/python/pydantic_core/_pydantic_core.cpython-313-x86_64-linux-gnu.so` |
| `test_aggregate_errors.py` | **22 passed** |
| `test_types.py -k string` | **51 passed**, 3 skipped, 1 xfailed |
| `test_plugins.py` (advisory) | 13 failed — pre-existing `_plugins=None` env issue in isolation |
| `make test` (full suite) | **12,229 passed**, 527 skipped, 37 xfailed, 4 failed |

### Full-suite failures (all pre-existing, unrelated)

All 4 failures are `ImportError: email-validator is not installed` in:
- `tests/test_docstrings.py` (2 tests)
- `tests/test_docs.py` (2 tests)

These are caused by the missing `email-validator` optional dependency in the
Docker environment (`uv sync --group testing-extra` does not install optional
email extras). The same four failures occur on the baseline commit in this
environment. They are not related to `aggregate_errors`.

The count difference between local (12,305 passed) and Docker (12,229 passed)
is due to environment/version selection: Docker uses `python:3.13-slim` with the
`testing-extra` dependency group, while the local WSL environment has additional
optional packages installed.

### Clippy baseline comparison (inside Docker, same toolchain)

Both baseline and feature branches exit with code 101. The 13 diagnostics are
identical (all `LookupPath` visibility warnings in `lookup_key.rs`,
`input_abstract.rs`, `input_json.rs`, `input_python.rs`, `input_string.rs`,
plus one `unnecessary_trailing_comma` in `mod.rs` line 90). The only diff
content is cargo build progress output ordering (dependencies cached differently
between runs). No new diagnostics were introduced by this change.

**Zero new test failures were introduced by this change.**
